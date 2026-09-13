"""Build the frozen production anomaly artifacts without outcome evaluation."""

from __future__ import annotations

import argparse
import io
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd

from marketmind.anomalies.bundle import AnomalyArtifacts, RobustResidualState, save_artifacts
from marketmind.anomalies.config import (
    IF_CONFIG_NAME, IF_FEATURE_COLUMNS, IF_PARAMETERS, IF_ROLE, LOCKBOX_STATUS,
    MAD_MULTIPLIER, MODEL_VERSION, REVIEW_CAPACITY_PER_DAY, ROBUST_THRESHOLD,
    SCHEMA_VERSION,
)
from marketmind.anomalies.isolation_forest import build_features, fit_isolation_forest


def load_oos_corpus(artifact_dir: str | Path) -> pd.DataFrame:
    """Load and strictly validate the finalized, legitimately OOS residual corpus."""
    root = Path(artifact_dir)
    first = pd.read_csv(root / "oos_residual_blocks.csv")
    final = pd.read_csv(root / "lockbox_robust_scores_authentic.csv")
    columns = ["block", "d", "date", "state_id", "store_id", "dept_id",
               "actual_sales", "expected_sales", "residual"]
    corpus = pd.concat([first[columns], final[columns]], ignore_index=True)
    corpus["date"] = pd.to_datetime(corpus["date"])
    corpus["d_number"] = corpus["d"].str.removeprefix("d_").astype(int)
    if len(corpus) != 13_720 or corpus[["store_id", "dept_id"]].drop_duplicates().shape[0] != 70:
        raise ValueError("final production corpus must contain 13,720 rows and 70 series")
    if corpus.duplicated(["date", "store_id", "dept_id"]).any():
        raise ValueError("duplicate OOS residual series-date")
    if not ((corpus.actual_sales - corpus.expected_sales - corpus.residual).abs() < 1e-9).all():
        raise ValueError("residual source violates actual minus expected definition")
    if corpus.isna().any().any() or corpus.d_number.max() != 1941:
        raise ValueError("OOS residual corpus is incomplete")
    return corpus.sort_values(["date", "store_id", "dept_id"]).reset_index(drop=True)


def build_artifacts(artifact_dir: str | Path, calendar_path: str | Path):
    started = time.perf_counter()
    corpus = load_oos_corpus(artifact_dir)
    metadata = corpus[["state_id", "store_id", "dept_id"]].drop_duplicates().sort_values(
        ["store_id", "dept_id"]
    ).reset_index(drop=True)
    histories = {
        tuple(key): group.sort_values("date").residual.to_numpy(float)
        for key, group in corpus.groupby(["store_id", "dept_id"], sort=True)
    }
    state = RobustResidualState(
        histories, metadata, corpus.date.max().date().isoformat(), 1941,
        "finalized research OOS residual blocks d_1466-d_1941 (196 observed dates; lockbox consumed)",
    )
    state_buffer = io.BytesIO(); joblib.dump(state, state_buffer)
    calendar = pd.read_csv(calendar_path).rename(columns={"event_name_1": "event_name_1"})
    calendar["date"] = pd.to_datetime(calendar["date"])
    features = build_features(corpus, calendar, training_corpus=True)
    model, if_fit_seconds, if_bytes = fit_isolation_forest(features, IF_CONFIG_NAME)
    bundle = AnomalyArtifacts(state, model, IF_FEATURE_COLUMNS, IF_ROLE)
    stats = {
        "residual_state_source": state.source,
        "residual_rows": len(corpus), "series_count": 70,
        "observed_dates": int(corpus.date.nunique()),
        "date_range": [corpus.date.min().date().isoformat(), corpus.date.max().date().isoformat()],
        "day_range": [f"d_{corpus.d_number.min()}", f"d_{corpus.d_number.max()}"],
        "if_training_rows": len(features), "if_fit_seconds": if_fit_seconds,
        "if_serialized_bytes": if_bytes, "state_serialized_bytes": len(state_buffer.getvalue()),
        "build_seconds": time.perf_counter() - started,
        "training_cutoff": "d_1941",
    }
    return bundle, stats


def export_artifacts(bundle: AnomalyArtifacts, stats: dict, output_dir: str | Path) -> None:
    root = Path(output_dir); root.mkdir(parents=True, exist_ok=True)
    save_artifacts(bundle, root / "model.joblib")
    bundle.residual_state.summary().to_csv(root / "robust_residual_state.csv", index=False)
    stats = {**stats, "artifact_sizes_bytes": {
        "model.joblib": (root / "model.joblib").stat().st_size,
        "robust_residual_state.csv": (root / "robust_residual_state.csv").stat().st_size,
    }}
    production_metadata = {
        "model_family": "per-series robust standardized forecast residual",
        "version": MODEL_VERSION, "schema_version": SCHEMA_VERSION,
        "grain": ["department", "store", "day"],
        "forecast_model_reference": "models/forecasting/model.joblib (frozen Phase 1 HGBR-4 production forecast)",
        "residual_definition": "actual_sales - expected_sales",
        "scale_definition": "1.4826 * historical residual MAD", "mad_multiplier": MAD_MULTIPLIER,
        "threshold": ROBUST_THRESHOLD, "review_capacity": REVIEW_CAPACITY_PER_DAY,
        "direction_semantics": {"positive": "spike", "negative": "drop", "zero": "neutral", "missing": "undefined"},
        "state_update_semantics": "score complete date from state through T-1, freeze output, then append all T residuals",
        "IF_role": IF_ROLE, "IF_config": {"name": IF_CONFIG_NAME, **IF_PARAMETERS, "feature_order": list(IF_FEATURE_COLUMNS)},
        "training_cutoff": "d_1941 / 2016-05-22",
        "research_validation_reference": "reports/anomalies/robust_residual_baseline_results.md",
        "research_lockbox_reference": "reports/anomalies/final_lockbox_results.md",
        "lockbox_status": LOCKBOX_STATUS, "created_at": datetime.now(timezone.utc).isoformat(),
    }
    (root / "metadata.json").write_text(json.dumps(production_metadata, indent=2) + "\n")
    (root / "training_summary.json").write_text(json.dumps(stats, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, default=Path("reports/anomalies/artifacts"))
    parser.add_argument("--calendar", type=Path, default=Path("data/raw/m5/calendar.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("models/anomalies"))
    args = parser.parse_args()
    bundle, stats = build_artifacts(args.artifact_dir, args.calendar)
    export_artifacts(bundle, stats, args.output_dir)
    print(f"Built frozen anomaly artifact from {stats['residual_rows']:,} OOS residual rows; no outcome metric calculated.")


if __name__ == "__main__":
    main()
