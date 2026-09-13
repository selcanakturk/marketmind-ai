"""Execute the frozen validation-only RetailRocket popularity baseline."""

from __future__ import annotations

import argparse
import json
import resource
import time
from pathlib import Path

import pandas as pd

from marketmind.recommendations.evaluation import aggregate_metrics, instance_metrics
from marketmind.recommendations.popularity import point_in_time_topk
from marketmind.recommendations.splits import TemporalSplit, next_item_instances, validate_events


def run_validation(events_path: str | Path, output_dir: str | Path) -> dict:
    started = time.perf_counter()
    raw = pd.read_csv(events_path)
    events = validate_events(raw)
    split = TemporalSplit()
    # Deliberately remove the lockbox before constructing any validation object.
    development = events.loc[events.event_at.lt(split.lockbox_start), ["timestamp", "visitorid", "event", "itemid", "transactionid"]]
    instance_started = time.perf_counter()
    instances = next_item_instances(development, split.validation_start, split.lockbox_start)
    instance_seconds = time.perf_counter() - instance_started
    if len(instances) != 8_083:
        raise ValueError(f"expected 8,083 validation instances, got {len(instances):,}")
    if not instances.target_timestamp.gt(instances.recommendation_timestamp).all():
        raise ValueError("every target must occur strictly after recommendation time")
    if not instances.target_timestamp.lt(split.lockbox_start).all():
        raise ValueError("validation target crossed into lockbox")

    evaluation_started = time.perf_counter()
    recommendations = point_in_time_topk(development, instances, 20)
    rank_columns = [f"rank_{rank}" for rank in range(1, 21)]
    joined = instances.merge(recommendations, on=["visitorid", "recommendation_timestamp"], validate="one_to_one")
    metric_rows = []
    for row in joined.itertuples(index=False):
        ranking = [getattr(row, column) for column in rank_columns]
        metric_rows.append({
            "visitorid": row.visitorid,
            "target_warm": bool(row.candidate_item_known),
            "target_previously_seen": bool(row.target_previously_seen),
            "target_event": row.target_event,
            "history_bucket": "2-3" if row.history_interaction_count <= 3 else ("4-9" if row.history_interaction_count <= 9 else "10+"),
            **instance_metrics(ranking, row.target_itemid),
        })
    metrics = pd.DataFrame(metric_rows)
    evaluation_seconds = time.perf_counter() - evaluation_started

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    instances.to_csv(output / "validation_instances.csv", index=False)
    recommendations.to_csv(output / "popularity_top20.csv", index=False)
    metrics.to_csv(output / "popularity_metrics_by_instance.csv", index=False)

    cutoff_ms = int(split.validation_start.timestamp() * 1000)
    catalog = development.loc[development.timestamp.le(cutoff_ms), "itemid"].nunique()
    coverage = {}
    for k in (5, 10, 20):
        unique = pd.unique(recommendations[[f"rank_{rank}" for rank in range(1, k + 1)]].to_numpy().ravel()).size
        coverage[str(k)] = {"unique_items": int(unique), "catalog_coverage": unique / catalog}
    slice_metrics = {}
    for dimension in ("target_warm", "target_previously_seen", "target_event", "history_bucket"):
        slice_metrics[dimension] = {
            str(key): {"instances": int(len(group)), **aggregate_metrics(group)}
            for key, group in metrics.groupby(dimension, observed=True)
        }
    top_frequency = recommendations.rank_1.value_counts()
    slot_values = recommendations[rank_columns].to_numpy().ravel()
    global_top20 = recommendations.loc[0, rank_columns].tolist()
    profile = {
        "validation_instances": len(instances), "catalog_items": int(catalog),
        "cold_targets": int((~instances.candidate_item_known).sum()),
        "warm_targets": int(instances.candidate_item_known.sum()),
        "overall_metrics": aggregate_metrics(metrics), "slices": slice_metrics,
        "coverage": coverage,
        "concentration": {
            "most_popular_item": int(recommendations.rank_1.iloc[0]),
            "most_popular_item_top1_frequency": int(top_frequency.iloc[0]),
            "most_popular_item_top1_share": float(top_frequency.iloc[0] / len(recommendations)),
            "top_10_global_item_slot_share": float(pd.Series(slot_values).isin(global_top20[:10]).mean()),
            "top_20_global_item_slot_share": float(pd.Series(slot_values).isin(global_top20).mean()),
        },
        "compute": {
            "instance_construction_seconds": instance_seconds,
            "popularity_and_metrics_seconds": evaluation_seconds,
            "total_seconds": time.perf_counter() - started,
            "process_peak_rss_mb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 / 1024,
        },
        "lockbox_status": "no recommendations or performance metrics generated",
    }
    (output / "popularity_summary.json").write_text(json.dumps(profile, indent=2) + "\n")
    profile["artifact_bytes"] = {path.name: path.stat().st_size for path in output.iterdir() if path.is_file()}
    return profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", default="data/raw/retailrocket/events.csv")
    parser.add_argument("--output-dir", default="reports/recommendation/artifacts")
    args = parser.parse_args()
    print(json.dumps(run_validation(args.events, args.output_dir), indent=2))


if __name__ == "__main__":
    main()
