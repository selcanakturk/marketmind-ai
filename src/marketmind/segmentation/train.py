"""Train and export the frozen MarketMind household segmentation engine."""

from __future__ import annotations

import argparse
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import pyreadr
import sklearn
from sklearn.cluster import KMeans
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score

from marketmind.segmentation.alignment import semantic_mapping_from_profiles
from marketmind.segmentation.bundle import SegmentationModelBundle, save_bundle
from marketmind.segmentation.config import (
    ELIGIBILITY_MIN_ACTIVE_SPAN_DAYS,
    ELIGIBILITY_MIN_BASKETS,
    ELIGIBILITY_MIN_HISTORY_DAYS,
    FEATURE_ORDER,
    KMEANS_PARAMETERS,
    LOG_FEATURES,
    MODEL_VERSION,
    REFERENCE_CLUSTER_COUNTS,
    REFERENCE_ELIGIBLE_HOUSEHOLDS,
    REFERENCE_INTERNAL_METRICS,
    REFERENCE_SNAPSHOT,
    SCHEMA_VERSION,
    SEGMENT_CODES,
    UNCHANGED_FEATURES,
)
from marketmind.segmentation.preprocessing import prepare_features
from marketmind.segmentation.snapshot import build_household_snapshot


def load_sources(data_dir: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load authentic Complete Journey transactions and products."""
    directory = Path(data_dir)
    return (
        pyreadr.read_r(str(directory / "transactions.rds"))[None],
        pyreadr.read_r(str(directory / "products.rda"))["products"],
    )


def _library_versions() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scikit_learn": sklearn.__version__,
        "joblib": joblib.__version__,
        "pyreadr": pyreadr.__version__,
    }


def _plain_semantic_mapping(profiles: pd.DataFrame) -> dict[int, dict[str, str]]:
    mapping = semantic_mapping_from_profiles(profiles)
    plain = {
        int(cluster): {
            "segment_code": definition.segment_code,
            "display_name": definition.display_name,
            "description": definition.description,
        }
        for cluster, definition in mapping.items()
    }
    if {item["segment_code"] for item in plain.values()} != set(SEGMENT_CODES):
        raise ValueError("reference profiles did not resolve all semantic identities")
    return plain


def train_frozen_model(
    data_dir: str | Path, snapshot_date: str = REFERENCE_SNAPSHOT
) -> tuple[SegmentationModelBundle, dict[str, Any], pd.DataFrame, dict[str, Any]]:
    """Fit only the frozen configuration and build aggregated audit artifacts."""
    started = time.perf_counter()
    transactions, products = load_sources(data_dir)
    snapshot = build_household_snapshot(
        transactions,
        products,
        snapshot_at=snapshot_date,
        min_observed_history_days=ELIGIBILITY_MIN_HISTORY_DAYS,
        min_baskets=ELIGIBILITY_MIN_BASKETS,
        min_active_span_days=ELIGIBILITY_MIN_ACTIVE_SPAN_DAYS,
    )
    if snapshot_date == REFERENCE_SNAPSHOT and len(snapshot.features) != REFERENCE_ELIGIBLE_HOUSEHOLDS:
        raise ValueError(
            f"canonical reference snapshot must contain {REFERENCE_ELIGIBLE_HOUSEHOLDS} eligible households"
        )
    prepared = prepare_features(snapshot.features)
    estimator = KMeans(**KMEANS_PARAMETERS).fit(prepared.scaled)
    labels = estimator.labels_
    counts = {int(k): int(v) for k, v in pd.Series(labels).value_counts().sort_index().items()}
    metrics = {
        "silhouette": float(silhouette_score(prepared.scaled, labels)),
        "davies_bouldin": float(davies_bouldin_score(prepared.scaled, labels)),
        "calinski_harabasz": float(calinski_harabasz_score(prepared.scaled, labels)),
    }
    if snapshot_date == REFERENCE_SNAPSHOT:
        if counts != REFERENCE_CLUSTER_COUNTS:
            raise ValueError(f"reference cluster counts changed: {counts}")
        for metric, expected in REFERENCE_INTERNAL_METRICS.items():
            if not np.isclose(metrics[metric], expected, rtol=1e-10, atol=1e-12):
                raise ValueError(f"reference {metric} changed: {metrics[metric]}")

    original = snapshot.features.loc[:, FEATURE_ORDER].assign(raw_cluster_id=labels)
    medians = original.groupby("raw_cluster_id", observed=True).median()
    semantic_mapping = _plain_semantic_mapping(medians)
    distances = np.linalg.norm(
        prepared.scaled.to_numpy() - estimator.cluster_centers_[labels], axis=1
    )
    profile_rows = []
    for cluster in sorted(counts):
        profile_rows.append(
            {
                "raw_cluster_id": cluster,
                **semantic_mapping[cluster],
                "household_count": counts[cluster],
                "household_percentage": counts[cluster] / len(labels),
                **{feature: float(medians.loc[cluster, feature]) for feature in FEATURE_ORDER},
            }
        )
    profiles = pd.DataFrame(profile_rows)
    versions = _library_versions()
    bundle = SegmentationModelBundle(
        scaler=prepared.scaler,
        estimator=estimator,
        feature_order=FEATURE_ORDER,
        log_features=LOG_FEATURES,
        unchanged_features=UNCHANGED_FEATURES,
        eligibility_policy={
            "min_observed_history_days": ELIGIBILITY_MIN_HISTORY_DAYS,
            "min_baskets": ELIGIBILITY_MIN_BASKETS,
            "min_active_span_days": ELIGIBILITY_MIN_ACTIVE_SPAN_DAYS,
        },
        semantic_mapping=semantic_mapping,
        model_version=MODEL_VERSION,
        schema_version=SCHEMA_VERSION,
        reference_snapshot=str(snapshot_date),
        kmeans_parameters=dict(KMEANS_PARAMETERS),
        centroid_profiles=profile_rows,
        library_versions=versions,
    )
    monitoring = {
        "model_version": MODEL_VERSION,
        "reference_snapshot": str(snapshot_date),
        "feature_quantiles_original_units": {
            feature: {
                "q25": float(snapshot.features[feature].quantile(0.25)),
                "median": float(snapshot.features[feature].median()),
                "q75": float(snapshot.features[feature].quantile(0.75)),
            }
            for feature in FEATURE_ORDER
        },
        "segment_profiles": profile_rows,
        "centroid_distance_transformed_scaled_space": {
            "overall": _quantiles(distances),
            "by_raw_cluster": {
                str(cluster): _quantiles(distances[labels == cluster])
                for cluster in sorted(counts)
            },
        },
        "eligibility": {
            "observed_households": snapshot.eligibility.observed_households,
            "eligible_households": snapshot.eligibility.eligible_households,
            "eligible_percentage": snapshot.eligibility.eligible_households / snapshot.eligibility.observed_households,
            "insufficient_history_households": snapshot.eligibility.observed_households - snapshot.eligibility.eligible_households,
            "insufficient_history_percentage": (snapshot.eligibility.observed_households - snapshot.eligibility.eligible_households) / snapshot.eligibility.observed_households,
        },
        "thresholds": None,
        "note": "Reference statistics only; no automatic alert thresholds are defined.",
    }
    stats = {
        "observed_households": snapshot.eligibility.observed_households,
        "eligible_households": len(snapshot.features),
        "cluster_counts": counts,
        "cluster_percentages": {k: v / len(labels) for k, v in counts.items()},
        "internal_metrics": metrics,
        "fit_seconds": time.perf_counter() - started,
    }
    return bundle, stats, profiles, monitoring


def _quantiles(values: np.ndarray) -> dict[str, float]:
    return {
        "median": float(np.quantile(values, 0.50)),
        "q75": float(np.quantile(values, 0.75)),
        "q90": float(np.quantile(values, 0.90)),
        "q95": float(np.quantile(values, 0.95)),
    }


def build_metadata(bundle: SegmentationModelBundle, stats: dict[str, Any]) -> dict[str, Any]:
    """Create reviewable metadata without household-level observations."""
    return {
        "module": "customer_segmentation",
        "model_name": "MarketMind Frozen Household KMeans-3",
        "model_family": "sklearn.cluster.KMeans",
        "model_version": bundle.model_version,
        "schema_version": bundle.schema_version,
        "algorithm": "KMeans",
        "n_clusters": 3,
        "reference_snapshot": bundle.reference_snapshot,
        "training_date": datetime.now(timezone.utc).isoformat(),
        "entity_grain": "Complete Journey grocery-retail household",
        "eligibility_policy": bundle.eligibility_policy,
        "feature_order": list(bundle.feature_order),
        "transformations": {"log1p": list(bundle.log_features), "unchanged": list(bundle.unchanged_features)},
        "scaler": "sklearn.preprocessing.RobustScaler",
        "kmeans_parameters": bundle.kmeans_parameters,
        "semantic_mapping": {str(k): v for k, v in bundle.semantic_mapping.items()},
        "reference_cluster_sizes": {str(k): v for k, v in stats["cluster_counts"].items()},
        "reference_cluster_percentages": {str(k): v for k, v in stats["cluster_percentages"].items()},
        "reference_internal_metrics": stats["internal_metrics"],
        "temporal_stability_summary": {
            "snapshots": ["2017-06-30", "2017-07-31", "2017-08-31", "2017-09-30"],
            "consecutive_ari": [0.7133, 0.7001, 0.7175],
            "monthly_unchanged_assignment_share": "approximately 90-91%",
            "interpretation": "descriptive temporal credibility, not supervised performance",
        },
        "assignment_policy": {
            "eligible": "frozen features -> transformations -> scaler.transform -> nearest KMeans centroid -> semantic mapping",
            "ineligible_status": "insufficient_history",
            "distance_semantics": "Euclidean distance in transformed/scaled space; geometric atypicality only",
        },
        "refresh_policy": {
            "eligibility_and_assignment": "monthly at calendar month-end",
            "model_review": "quarterly",
            "model_refit": "not automatic; evidence-triggered after review",
        },
        "drift_monitoring_policy": [
            "feature median and quantile shifts",
            "eligibility and segment-share shifts",
            "aligned centroid/profile movement",
            "centroid-distance distribution growth",
            "semantic-ordering breakdown",
        ],
        "library_versions": bundle.library_versions,
        "training_statistics": {"fit_seconds": stats["fit_seconds"]},
        "known_limitations": [
            "The dataset represents grocery-retail households, not individual e-commerce customers.",
            "Segments are descriptive and do not establish causal effects.",
            "Cluster assignment is not a probability.",
            "Centroid distance is not confidence or certainty.",
            "Only four historical snapshots were evaluated.",
            "No second-year seasonal replication exists.",
            "Cumulative behavior features depend on observation history.",
            "The model is not automatically valid for unrelated retailers or domains.",
        ],
    }


def export_artifacts(
    bundle: SegmentationModelBundle,
    metadata: dict[str, Any],
    profiles: pd.DataFrame,
    monitoring: dict[str, Any],
    output_dir: str | Path,
) -> None:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    save_bundle(bundle, directory / "model.joblib")
    (directory / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    profiles.to_csv(directory / "reference_profiles.csv", index=False)
    (directory / "monitoring_baseline.json").write_text(json.dumps(monitoring, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw/complete_journey"))
    parser.add_argument("--output-dir", type=Path, default=Path("models/segmentation"))
    parser.add_argument("--snapshot-date", default=REFERENCE_SNAPSHOT)
    args = parser.parse_args()
    bundle, stats, profiles, monitoring = train_frozen_model(args.data_dir, args.snapshot_date)
    export_artifacts(bundle, build_metadata(bundle, stats), profiles, monitoring, args.output_dir)
    print(f"Trained MarketMind Frozen Household KMeans-3 at {args.snapshot_date}: {stats['eligible_households']:,} eligible households")
    print(f"Cluster counts: {stats['cluster_counts']}")
    print(f"Saved bundle, metadata, profiles, and baseline to {args.output_dir}")


if __name__ == "__main__":
    main()
