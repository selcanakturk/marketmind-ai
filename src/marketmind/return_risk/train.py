"""One-command production retraining for the frozen return-risk model."""

from __future__ import annotations

import argparse
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pyreadr
import sklearn

from marketmind.return_risk.bundle import ReturnRiskModelBundle, load_bundle, save_bundle
from marketmind.return_risk.cohorts import EligibilityRule, build_labeled_cohort
from marketmind.return_risk.config import (
    DEFAULT_CAPACITY, ET2_PARAMETERS, EXPECTED_TRAINING_ROWS, FROZEN_FEATURE_NAMES,
    MIN_ACTIVE_SPAN_DAYS, MIN_BASKETS, MIN_OBSERVED_HISTORY_DAYS, MODEL_VERSION,
    OUTCOME_OBSERVATION_CUTOFF, PRODUCTION_TRAINING_SNAPSHOTS, RESEARCH_METRICS,
    SCHEMA_VERSION, SECONDARY_CAPACITIES, TARGET_HORIZON_DAYS, TRAINING_CUTOFF,
)
from marketmind.return_risk.features import baseline_features, build_candidate_features
from marketmind.return_risk.models import make_extra_trees_candidate, validate_model_frame


def load_sources(raw_dir: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    directory = Path(raw_dir)
    transactions = pyreadr.read_r(str(directory / "transactions.rds"))[None]
    products = pyreadr.read_r(str(directory / "products.rda"))["products"]
    transactions["transaction_timestamp"] = pd.to_datetime(transactions["transaction_timestamp"])
    return transactions, products


def build_production_training_frame(transactions, products):
    """Build only the predeclared April-November fully labeled snapshots."""

    rows = []
    cohort_summary = []
    for snapshot in PRODUCTION_TRAINING_SNAPSHOTS:
        features = baseline_features(build_candidate_features(transactions, products, snapshot))
        cohort = build_labeled_cohort(
            transactions, snapshot, TARGET_HORIZON_DAYS, OUTCOME_OBSERVATION_CUTOFF,
        )
        if not features.index.equals(cohort.index):
            raise ValueError(f"feature/target alignment failed at {snapshot}")
        frame = features.copy()
        frame["return_risk_target"] = cohort["return_risk_target"].astype(int)
        frame["snapshot_at"] = snapshot
        rows.append(frame)
        cohort_summary.append({
            "snapshot_at": snapshot.isoformat(), "outcome_end": (snapshot + pd.Timedelta(days=TARGET_HORIZON_DAYS)).isoformat(),
            "rows": int(len(frame)), "positive_rows": int(frame["return_risk_target"].sum()),
        })
    combined = pd.concat(rows)
    if len(combined) != EXPECTED_TRAINING_ROWS:
        raise ValueError(f"expected {EXPECTED_TRAINING_ROWS:,} authentic training rows, got {len(combined):,}")
    return combined, cohort_summary


def train_production_bundle(transactions, products):
    training, cohorts = build_production_training_frame(transactions, products)
    X = validate_model_frame(training.loc[:, FROZEN_FEATURE_NAMES])
    y = training["return_risk_target"].to_numpy(dtype=int)
    if set(np.unique(y)) != {0, 1}:
        raise ValueError("production target must contain both binary classes")
    estimator = make_extra_trees_candidate("ET-2").fit(X, y)
    rule = EligibilityRule()
    bundle = ReturnRiskModelBundle(
        estimator=estimator, feature_names=FROZEN_FEATURE_NAMES,
        model_version=MODEL_VERSION, schema_version=SCHEMA_VERSION,
        training_cutoff=TRAINING_CUTOFF.isoformat(),
        outcome_observation_cutoff=OUTCOME_OBSERVATION_CUTOFF.isoformat(),
        training_cohorts=cohorts, training_rows=len(training),
        target_horizon_days=TARGET_HORIZON_DAYS,
        eligibility_rule={
            "min_observed_history_days": rule.min_observed_history_days,
            "min_baskets": rule.min_baskets,
            "min_active_span_days": rule.min_active_span_days,
        },
        score_semantics="uncalibrated relative-ranking score; not a probability or confidence",
        default_capacity=DEFAULT_CAPACITY, secondary_capacities=SECONDARY_CAPACITIES,
        model_parameters=dict(ET2_PARAMETERS),
        library_versions={"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "scikit_learn": sklearn.__version__, "joblib": joblib.__version__},
        research_metrics=RESEARCH_METRICS,
        lockbox_status="consumed permanently; metrics are historical evidence, not fresh validation",
    )
    bundle.validate()
    return bundle


def export_artifacts(bundle: ReturnRiskModelBundle, output_dir: str | Path) -> None:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    save_bundle(bundle, destination / "model.joblib")
    created_at = datetime.now(timezone.utc).isoformat()
    metadata = {
        "model_version": bundle.model_version, "schema_version": bundle.schema_version,
        "created_at_utc": created_at, "training_cutoff": bundle.training_cutoff,
        "outcome_observation_cutoff": bundle.outcome_observation_cutoff,
        "feature_names": list(bundle.feature_names), "model_parameters": bundle.model_parameters,
        "target_horizon_days": bundle.target_horizon_days,
        "eligibility_rule": bundle.eligibility_rule, "score_semantics": bundle.score_semantics,
        "default_capacity": bundle.default_capacity,
        "secondary_capacities": list(bundle.secondary_capacities),
        "library_versions": bundle.library_versions, "research_metrics": bundle.research_metrics,
        "lockbox_status": bundle.lockbox_status,
    }
    summary = {
        "model_version": bundle.model_version, "training_rows": bundle.training_rows,
        "cohort_count": len(bundle.training_cohorts), "cohorts": bundle.training_cohorts,
        "statement": "Final production retraining only; no performance metrics were calculated.",
    }
    (destination / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (destination / "training_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    load_bundle(destination / "model.joblib")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", default="data/raw/complete_journey")
    parser.add_argument("--output-dir", default="models/return_risk")
    args = parser.parse_args()
    transactions, products = load_sources(args.raw_dir)
    bundle = train_production_bundle(transactions, products)
    export_artifacts(bundle, args.output_dir)
    print(f"saved {bundle.model_version} ({bundle.training_rows:,} rows) to {args.output_dir}")


if __name__ == "__main__":
    main()
