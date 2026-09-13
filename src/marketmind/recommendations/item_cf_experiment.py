"""Run the controlled validation-only Item-CF experiment."""

from __future__ import annotations

import argparse
import json
import resource
import time
from pathlib import Path

import numpy as np
import pandas as pd

from marketmind.recommendations.evaluation import aggregate_metrics, instance_metrics
from marketmind.recommendations.item_cf import NEIGHBOR_CONFIGS, fit_item_cf, recommend
from marketmind.recommendations.popularity import popularity_ranking
from marketmind.recommendations.splits import TemporalSplit, next_item_instances, validate_events

POPULARITY_NDCG10 = 0.0031214571649555373
POPULARITY_HIT10 = 0.005814672770011135
POPULARITY_HIT20 = 0.010515897562786094
POPULARITY_COVERAGE20 = 9.4381916424813e-05


def _metric_frame(instances, rankings, diagnostics):
    rows = []
    for instance, ranking, diagnostic in zip(instances.itertuples(index=False), rankings, diagnostics):
        rows.append({
            "visitorid": instance.visitorid,
            "target_warm": bool(instance.candidate_item_known),
            "target_previously_seen": bool(instance.target_previously_seen),
            "target_event": instance.target_event,
            "history_bucket": "2-3" if instance.history_interaction_count <= 3 else ("4-9" if instance.history_interaction_count <= 9 else "10+"),
            **diagnostic, **instance_metrics(ranking, instance.target_itemid),
        })
    return pd.DataFrame(rows)


def run_experiment(events_path: str | Path, output_dir: str | Path) -> dict:
    total_started = time.perf_counter()
    split = TemporalSplit()
    raw = pd.read_csv(events_path)
    events = validate_events(raw)
    # Lockbox rows are discarded before instances, training, or scoring exist.
    development = events.loc[events.event_at.lt(split.lockbox_start)].copy()
    raw_columns = ["timestamp", "visitorid", "event", "itemid", "transactionid"]
    instances = next_item_instances(development[raw_columns], split.validation_start, split.lockbox_start)
    if len(instances) != 8_083:
        raise ValueError("canonical validation cohort changed")
    training = development.loc[development.event_at.lt(split.validation_start)].copy()
    if training.event_at.ge(split.validation_start).any():
        raise ValueError("validation event entered Item-CF training")

    model = fit_item_cf(training, max_neighbors=max(NEIGHBOR_CONFIGS))
    popularity = popularity_ranking(development[raw_columns], split.validation_start, k=len(model.item_ids))
    history = training.groupby("visitorid", observed=True).itemid.apply(list).to_dict()
    popularity_top20 = popularity[:20]
    config_rows, config_outputs = [], {}
    for neighbor_count in NEIGHBOR_CONFIGS:
        started = time.perf_counter()
        rankings, diagnostics = [], []
        for visitor in instances.visitorid:
            ranking, diagnostic = recommend(
                model, history.get(visitor, []), popularity,
                neighbors=neighbor_count, k=20,
            )
            if len(ranking) != 20 or len(ranking) != len(set(ranking)):
                raise ValueError("Item-CF must emit 20 unique items")
            rankings.append(ranking)
            diagnostics.append(diagnostic)
        metrics = _metric_frame(instances, rankings, diagnostics)
        overall = aggregate_metrics(metrics)
        unique20 = len({item for ranking in rankings for item in ranking})
        config_rows.append({
            "neighbors": neighbor_count, **overall,
            "coverage_at_20": unique20 / len(model.item_ids),
            "evaluation_seconds": time.perf_counter() - started,
        })
        config_outputs[neighbor_count] = (rankings, diagnostics, metrics)
    configs = pd.DataFrame(config_rows)
    selected = int(configs.sort_values(["ndcg_at_10", "neighbors"], ascending=[False, True]).iloc[0].neighbors)
    rankings, diagnostics, metrics = config_outputs[selected]

    rank_columns = [f"rank_{rank}" for rank in range(1, 21)]
    top20 = pd.DataFrame({"visitorid": instances.visitorid, **{column: [ranking[index] for ranking in rankings] for index, column in enumerate(rank_columns)}})
    slice_rows = []
    for dimension in ("target_warm", "target_previously_seen", "target_event", "history_bucket"):
        for value, group in metrics.groupby(dimension, observed=True):
            summary = aggregate_metrics(group)
            slice_rows.append({"dimension": dimension, "value": str(value), "instances": len(group), **summary})
    slices = pd.DataFrame(slice_rows)

    coverage = {}
    for k in (5, 10, 20):
        unique = pd.unique(top20[[f"rank_{rank}" for rank in range(1, k + 1)]].to_numpy().ravel()).size
        coverage[str(k)] = {"unique_items": int(unique), "catalog_coverage": unique / len(model.item_ids)}
    overlap_counts = np.array([len(set(ranking) & set(popularity_top20)) for ranking in rankings])
    collaborative_counts = metrics.collaboratively_scored_candidates.to_numpy()
    collaborative_topk = metrics.collaborative_items_in_topk.to_numpy()
    complete_fallback = metrics.complete_popularity_fallback.astype(bool).to_numpy()
    cf_hits = metrics.hit_rate_at_20.astype(bool).to_numpy()
    popularity_hits = instances.target_itemid.isin(popularity_top20).to_numpy()
    categories = {
        "popularity_miss_cf_hit": ~popularity_hits & cf_hits,
        "popularity_hit_cf_miss": popularity_hits & ~cf_hits,
        "both_miss": ~popularity_hits & ~cf_hits,
        "both_hit": popularity_hits & cf_hits,
    }
    errors = []
    for category, mask in categories.items():
        sample = instances.loc[mask].sort_values("visitorid").head(5)
        for row in sample.itertuples(index=False):
            errors.append({"category": category, "visitorid": row.visitorid, "target_itemid": row.target_itemid, "target_event": row.target_event, "history_interaction_count": row.history_interaction_count, "target_previously_seen": row.target_previously_seen})
    error_frame = pd.DataFrame(errors)

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    configs.to_csv(output / "item_cf_config_results.csv", index=False)
    top20.to_csv(output / "item_cf_top20.csv", index=False)
    metrics.to_csv(output / "item_cf_selected_metrics.csv", index=False)
    slices.to_csv(output / "item_cf_slice_results.csv", index=False)
    error_frame.to_csv(output / "item_cf_error_sample.csv", index=False)

    selected_metrics = aggregate_metrics(metrics)
    result = {
        "selected_neighbors": selected,
        "matrix": {
            "visitors": model.interaction_matrix.shape[0], "items": model.interaction_matrix.shape[1],
            "nonzeros": model.interaction_matrix.nnz,
            "sparsity": 1 - model.interaction_matrix.nnz / (model.interaction_matrix.shape[0] * model.interaction_matrix.shape[1]),
            "retained_similarity_edges": int(sum(len(value[0]) for value in model.neighbors.values())),
        },
        "overall_metrics": selected_metrics,
        "comparison": {
            "ndcg_at_10_absolute": selected_metrics["ndcg_at_10"] - POPULARITY_NDCG10,
            "ndcg_at_10_relative": selected_metrics["ndcg_at_10"] / POPULARITY_NDCG10 - 1,
            "hit_rate_at_10_absolute": selected_metrics["hit_rate_at_10"] - POPULARITY_HIT10,
            "hit_rate_at_20_absolute": selected_metrics["hit_rate_at_20"] - POPULARITY_HIT20,
            "coverage_at_20_absolute": coverage["20"]["catalog_coverage"] - POPULARITY_COVERAGE20,
        },
        "coverage": coverage,
        "personalization": {
            "instances_with_nonzero_collaborative_score_rate": float((collaborative_counts > 0).mean()),
            "complete_popularity_fallback_rate": float(complete_fallback.mean()),
            "partial_popularity_fill_rate": float(((collaborative_topk > 0) & (collaborative_topk < 20)).mean()),
            "average_collaboratively_scored_candidates": float(collaborative_counts.mean()),
            "average_collaborative_items_in_top20": float(collaborative_topk.mean()),
            "average_top20_overlap_with_popularity": float(overlap_counts.mean() / 20),
            "different_from_popularity_rate": float((overlap_counts < 20).mean()),
            "unique_recommended_items_at_20": coverage["20"]["unique_items"],
        },
        "cold_targets": int((~instances.candidate_item_known).sum()),
        "warm_targets": int(instances.candidate_item_known.sum()),
        "configuration_results": configs.to_dict("records"),
        "compute": {
            "similarity_build_seconds": model.build_seconds,
            "selected_evaluation_seconds": float(configs.loc[configs.neighbors.eq(selected), "evaluation_seconds"].iloc[0]),
            "total_seconds": time.perf_counter() - total_started,
            "peak_rss_mb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 / 1024,
        },
        "error_category_counts": {name: int(mask.sum()) for name, mask in categories.items()},
        "lockbox_status": "no recommendations or ranking performance generated",
    }
    (output / "item_cf_summary.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", default="data/raw/retailrocket/events.csv")
    parser.add_argument("--output-dir", default="reports/recommendation/artifacts")
    args = parser.parse_args()
    print(json.dumps(run_experiment(args.events, args.output_dir), indent=2))


if __name__ == "__main__":
    main()
