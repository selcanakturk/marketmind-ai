"""One-command production retraining for the frozen RetailRocket Item-CF."""

from __future__ import annotations

import argparse
import json
import platform
import resource
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import scipy

from marketmind.recommendations.bundle import RecommendationBundle, load_bundle, save_bundle
from marketmind.recommendations.config import (
    ALLOWED_EVENTS, DEFAULT_K, FROZEN_CONFIGURATION, LOCKBOX_RESTRICTION, LOCKBOX_STATUS, MODEL_VERSION,
    NEIGHBOR_COUNT, REQUIRED_EVENT_COLUMNS, RESEARCH_METRICS, SCHEMA_VERSION,
)
from marketmind.recommendations.item_cf import fit_item_cf


def validate_events(events: pd.DataFrame) -> pd.DataFrame:
    """Validate and canonically sort raw events; transactionid is optional."""
    missing = sorted(set(REQUIRED_EVENT_COLUMNS).difference(events.columns))
    if missing:
        raise ValueError(f"events missing columns: {missing}")
    frame = events.copy()
    for column in ("timestamp", "visitorid", "itemid"):
        numeric = pd.to_numeric(frame[column], errors="coerce")
        if numeric.isna().any() or not np.isfinite(numeric).all() or (numeric < 0).any():
            raise ValueError(f"{column} must contain finite nonnegative numeric values")
        if not np.equal(numeric, np.floor(numeric)).all():
            raise ValueError(f"{column} must contain integer values")
        frame[column] = numeric.astype(np.int64)
    if frame["event"].isna().any() or not frame["event"].isin(ALLOWED_EVENTS).all():
        raise ValueError(f"event must be one of {ALLOWED_EVENTS}")
    if frame.empty:
        raise ValueError("events must not be empty")
    return frame.sort_values(["timestamp", "visitorid", "itemid", "event"], kind="mergesort").reset_index(drop=True)


def train_production_bundle(events: pd.DataFrame) -> RecommendationBundle:
    started = time.perf_counter()
    frame = validate_events(events)
    model = fit_item_cf(frame, max_neighbors=NEIGHBOR_COUNT)
    indptr = [0]
    indices: list[np.ndarray] = []
    similarities: list[np.ndarray] = []
    for row in range(len(model.item_ids)):
        row_indices, row_similarities = model.neighbors[row]
        indices.append(row_indices.astype(np.int32, copy=False))
        similarities.append(row_similarities.astype(np.float32, copy=False))
        indptr.append(indptr[-1] + len(row_indices))
    counts = frame.groupby("itemid", sort=False).size().rename("count").reset_index()
    counts = counts.sort_values(["count", "itemid"], ascending=[False, True], kind="mergesort")
    first_seen = frame.groupby("itemid", sort=True)["timestamp"].min().reindex(model.item_ids)
    pair_count = int(frame[["visitorid", "itemid"]].drop_duplicates().shape[0])
    bundle = RecommendationBundle(
        item_ids=model.item_ids.astype(np.int64),
        neighbor_indptr=np.asarray(indptr, dtype=np.int64),
        neighbor_indices=np.concatenate(indices) if indices else np.array([], dtype=np.int32),
        neighbor_similarities=np.concatenate(similarities) if similarities else np.array([], dtype=np.float32),
        popularity_item_ids=counts["itemid"].to_numpy(np.int64),
        popularity_counts=counts["count"].to_numpy(np.int64),
        item_first_seen_ms=first_seen.to_numpy(np.int64),
        training_cutoff_ms=int(frame["timestamp"].max()),
        model_version=MODEL_VERSION, schema_version=SCHEMA_VERSION,
        configuration=dict(FROZEN_CONFIGURATION),
        training_statistics={"raw_events": int(len(frame)), "visitors": int(frame.visitorid.nunique()),
                             "items": int(frame.itemid.nunique()), "binary_visitor_item_pairs": pair_count,
                             "sparsity": float(1 - pair_count / (frame.visitorid.nunique() * frame.itemid.nunique())),
                             "neighbor_edges": int(indptr[-1]), "neighbor_graph_bytes": int(
                                 np.asarray(indptr, dtype=np.int64).nbytes
                                 + sum(value.nbytes for value in indices)
                                 + sum(value.nbytes for value in similarities)),
                             "graph_build_seconds": model.build_seconds,
                             "production_training_seconds": time.perf_counter() - started,
                             "peak_process_rss_bytes": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                                                           * (1024 if platform.system() != "Darwin" else 1))},
        library_versions={"python": platform.python_version(), "numpy": np.__version__,
                          "pandas": pd.__version__, "scipy": scipy.__version__, "joblib": joblib.__version__},
        research_metrics=RESEARCH_METRICS, lockbox_status=LOCKBOX_STATUS,
    )
    bundle.validate()
    return bundle


def export_artifacts(bundle: RecommendationBundle, output_dir: str | Path) -> None:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    artifact = destination / "model.joblib"
    save_bundle(bundle, artifact)
    cutoff = pd.to_datetime(bundle.training_cutoff_ms, unit="ms", utc=True).isoformat()
    metadata = {
        "model_family": "item-item collaborative filtering",
        "model_version": bundle.model_version, "version": bundle.model_version, "schema_version": bundle.schema_version,
        "created_at_utc": datetime.now(timezone.utc).isoformat(), "created_at": datetime.now(timezone.utc).isoformat(),
        "training_cutoff": cutoff,
        "training_event_count": bundle.training_statistics["raw_events"],
        "visitor_count": bundle.training_statistics["visitors"],
        "item_count": bundle.training_statistics["items"],
        "binary_interaction_count": bundle.training_statistics["binary_visitor_item_pairs"],
        "neighbor_count": NEIGHBOR_COUNT, "similarity": "exact sparse cosine", "aggregation": "sum",
        "allow_seen_items": True, "self_similarity": True, "event_weighting": None,
        "recency_weighting": None, "default_k": DEFAULT_K,
        "fallback": "all-event popularity through scoring snapshot",
        "configuration": bundle.configuration, "result_schema_version": bundle.schema_version,
        "library_versions": bundle.library_versions, "research_metrics": bundle.research_metrics,
        "research_validation_metrics_reference": "reports/recommendation/item_cf_results.md",
        "research_lockbox_metrics_reference": "reports/recommendation/final_lockbox_results.md",
        "lockbox_status": bundle.lockbox_status, "lockbox_restriction": LOCKBOX_RESTRICTION,
        "artifact_contents": ["ascending item ID mapping", "CSR-style sparse top-50 neighbor graph",
                              "full-history popularity state", "item first-seen timestamps", "metadata"],
    }
    summary = {**bundle.training_statistics, "model_version": bundle.model_version,
               "training_cutoff": cutoff,
               "serialized_artifact_bytes": artifact.stat().st_size,
               "metadata_bytes": 0,
               "statement": "Final production retraining only; no recommendation quality or outcome metrics were calculated."}
    (destination / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    summary["metadata_bytes"] = (destination / "metadata.json").stat().st_size
    (destination / "training_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    load_bundle(artifact)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", default="data/raw/retailrocket/events.csv")
    parser.add_argument("--output-dir", default="models/recommendations")
    args = parser.parse_args()
    events = pd.read_csv(args.events)
    bundle = train_production_bundle(events)
    export_artifacts(bundle, args.output_dir)
    print(f"saved {bundle.model_version} ({bundle.training_statistics['raw_events']:,} events) to {args.output_dir}")


if __name__ == "__main__":
    main()
