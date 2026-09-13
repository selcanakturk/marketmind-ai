"""Run the validation-only controlled implicit-ALS challenger."""

from __future__ import annotations

import argparse
import json
import resource
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd

from marketmind.recommendations.als import ALS_CONFIGS, fit_als
from marketmind.recommendations.evaluation import aggregate_metrics, instance_metrics
from marketmind.recommendations.popularity import popularity_ranking
from marketmind.recommendations.splits import TemporalSplit, next_item_instances, validate_events

POPULARITY = {"ndcg_at_10": 0.0031214571649555373, "hit_rate_at_10": 0.005814672770011135, "hit_rate_at_20": 0.010515897562786094, "coverage_at_20": 9.4381916424813e-05}
ITEM_CF = {"ndcg_at_10": 0.1914702054352544, "hit_rate_at_10": 0.2507732277619696, "hit_rate_at_20": 0.26363973772114313, "coverage_at_20": 0.2364408579316203}


def _batch_rank(model, visitor_ids, batch_size=128, k=20):
    """Score the trained item catalog in bounded batches and emit only top K."""

    rankings, received, latent_counts = [], [], []
    mapping = model.visitor_to_index
    for start in range(0, len(visitor_ids), batch_size):
        visitor_batch = visitor_ids[start:start + batch_size]
        known_positions = [(position, mapping.get(int(visitor))) for position, visitor in enumerate(visitor_batch)]
        known = [(position, index) for position, index in known_positions if index is not None]
        batch_rankings = {position: [] for position in range(len(visitor_batch))}
        if known:
            user_indices = np.asarray([index for _, index in known], dtype=np.int64)
            indices, scores = model.estimator.recommend(
                user_indices, model.interaction_matrix[user_indices], N=k,
                filter_already_liked_items=False, recalculate_user=False,
            )
            for (position, _), item_indices, item_scores in zip(known, indices, scores):
                pairs = sorted(
                    ((int(model.item_ids[item]), float(score)) for item, score in zip(item_indices, item_scores) if np.isfinite(score)),
                    key=lambda value: (-value[1], value[0]),
                )
                batch_rankings[position] = [item for item, _ in pairs]
        for position in range(len(visitor_batch)):
            rankings.append(batch_rankings[position])
            received.append(bool(batch_rankings[position]))
            latent_counts.append(len(batch_rankings[position]))
    return rankings, np.asarray(received, dtype=bool), np.asarray(latent_counts, dtype=int)


def _metrics(instances, rankings):
    rows = []
    for instance, ranking in zip(instances.itertuples(index=False), rankings):
        rows.append({
            "visitorid": instance.visitorid, "target_warm": bool(instance.candidate_item_known),
            "target_previously_seen": bool(instance.target_previously_seen), "target_event": instance.target_event,
            "history_bucket": "2-3" if instance.history_interaction_count <= 3 else ("4-9" if instance.history_interaction_count <= 9 else "10+"),
            **instance_metrics(ranking, instance.target_itemid),
        })
    return pd.DataFrame(rows)


def run_experiment(events_path: str | Path, output_dir: str | Path) -> dict:
    total_started = time.perf_counter()
    split = TemporalSplit()
    events = validate_events(pd.read_csv(events_path))
    development = events.loc[events.event_at.lt(split.lockbox_start)].copy()
    raw_columns = ["timestamp", "visitorid", "event", "itemid", "transactionid"]
    instances = next_item_instances(development[raw_columns], split.validation_start, split.lockbox_start)
    if len(instances) != 8_083:
        raise ValueError("canonical validation cohort changed")
    training = development.loc[development.event_at.lt(split.validation_start)].copy()
    if training.event_at.ge(split.validation_start).any():
        raise ValueError("validation interactions entered ALS training")
    candidate_items = np.sort(training.itemid.unique())
    popularity = popularity_ranking(development[raw_columns], split.validation_start, len(candidate_items))

    config_rows, outputs = [], {}
    for name in ALS_CONFIGS:
        fit_started = time.perf_counter()
        model = fit_als(training, name)
        fit_seconds = time.perf_counter() - fit_started
        score_started = time.perf_counter()
        rankings, received, latent_counts = _batch_rank(model, instances.visitorid.to_numpy())
        # Only training-factor items can be latent-scored; point-in-time popularity fills any short list.
        candidate_set = set(candidate_items)
        for index, ranking in enumerate(rankings):
            chosen = set(ranking)
            if len(ranking) < 20:
                for item in popularity:
                    if item not in chosen:
                        ranking.append(int(item)); chosen.add(int(item))
                        if len(ranking) == 20: break
            if len(ranking) != 20 or len(ranking) != len(set(ranking)) or not set(ranking).issubset(candidate_set):
                raise ValueError("ALS ranking violates full-catalog contract")
        metrics = _metrics(instances, rankings)
        score_seconds = time.perf_counter() - score_started
        overall = aggregate_metrics(metrics)
        unique20 = len({item for ranking in rankings for item in ranking})
        with tempfile.TemporaryDirectory() as directory:
            model_path = Path(directory) / "als_model.npz"
            model.estimator.save(model_path)
            serialized_bytes = model_path.stat().st_size
        config_rows.append({
            "config": name, **ALS_CONFIGS[name], **overall,
            "coverage_at_20": unique20 / len(candidate_items), "fit_seconds": fit_seconds,
            "scoring_seconds": score_seconds, "serialized_estimator_bytes": serialized_bytes,
        })
        outputs[name] = (rankings, metrics, received, latent_counts, model.estimator.user_factors.shape, model.estimator.item_factors.shape)
        del model
    configs = pd.DataFrame(config_rows)
    selected = configs.sort_values(["ndcg_at_10", "config"], ascending=[False, True]).iloc[0].config
    rankings, metrics, received, latent_counts, user_factor_shape, item_factor_shape = outputs[selected]

    rank_columns = [f"rank_{rank}" for rank in range(1, 21)]
    top20 = pd.DataFrame({"visitorid": instances.visitorid, **{column: [ranking[index] for ranking in rankings] for index, column in enumerate(rank_columns)}})
    item_cf = pd.read_csv(Path(output_dir) / "item_cf_top20.csv").sort_values("visitorid")
    popularity_top20 = popularity[:20]
    item_cf_rankings = item_cf[rank_columns].to_numpy()
    als_array = top20[rank_columns].to_numpy()
    overlap_cf = np.array([len(set(a) & set(b)) for a, b in zip(als_array, item_cf_rankings)])
    overlap_pop = np.array([len(set(a) & set(popularity_top20)) for a in als_array])
    history_pairs = training[["visitorid", "itemid"]].drop_duplicates()
    history_sets = history_pairs.groupby("visitorid", observed=True).itemid.apply(set).to_dict()
    seen_slots = np.array([sum(item in history_sets.get(visitor, set()) for item in ranking) for visitor, ranking in zip(instances.visitorid, rankings)])

    slice_rows = []
    for dimension in ("target_warm", "target_previously_seen", "target_event", "history_bucket"):
        for value, group in metrics.groupby(dimension, observed=True):
            slice_rows.append({"dimension": dimension, "value": str(value), "instances": len(group), **aggregate_metrics(group)})
    slices = pd.DataFrame(slice_rows)
    coverage = {}
    for k in (5, 10, 20):
        unique = pd.unique(als_array[:, :k].ravel()).size
        coverage[str(k)] = {"unique_items": int(unique), "catalog_coverage": unique / len(candidate_items)}
    partial_fill = (latent_counts > 0) & (latent_counts < 20)
    selected_row = configs.loc[configs.config.eq(selected)].iloc[0]
    selected_metrics = aggregate_metrics(metrics)
    item_cf_hits = pd.read_csv(Path(output_dir) / "item_cf_selected_metrics.csv").sort_values("visitorid").hit_rate_at_20.astype(bool).to_numpy()
    als_hits = metrics.sort_values("visitorid").hit_rate_at_20.astype(bool).to_numpy()
    error_masks = {"als_hit_item_cf_miss": als_hits & ~item_cf_hits, "item_cf_hit_als_miss": item_cf_hits & ~als_hits, "both_hit": als_hits & item_cf_hits, "both_miss": ~als_hits & ~item_cf_hits}
    error_rows = []
    ordered_instances = instances.sort_values("visitorid")
    for category, mask in error_masks.items():
        for row in ordered_instances.loc[mask].head(5).itertuples(index=False):
            error_rows.append({"category": category, "visitorid": row.visitorid, "target_itemid": row.target_itemid, "target_event": row.target_event, "history_interaction_count": row.history_interaction_count, "target_previously_seen": row.target_previously_seen})

    output = Path(output_dir); output.mkdir(parents=True, exist_ok=True)
    configs.to_csv(output / "als_config_results.csv", index=False)
    top20.to_csv(output / "als_top20.csv", index=False)
    metrics.to_csv(output / "als_selected_metrics.csv", index=False)
    slices.to_csv(output / "als_slice_results.csv", index=False)
    pd.DataFrame(error_rows).to_csv(output / "als_error_samples.csv", index=False)
    comparison = pd.DataFrame([
        {"model": "popularity", **POPULARITY}, {"model": "item_cf", **ITEM_CF},
        {"model": selected, "ndcg_at_10": selected_metrics["ndcg_at_10"], "hit_rate_at_10": selected_metrics["hit_rate_at_10"], "hit_rate_at_20": selected_metrics["hit_rate_at_20"], "coverage_at_20": coverage["20"]["catalog_coverage"]},
    ])
    comparison.to_csv(output / "als_comparison.csv", index=False)
    result = {
        "selected_config": selected, "selected_parameters": ALS_CONFIGS[selected],
        "matrix": {"visitors": int(user_factor_shape[0]), "items": int(item_factor_shape[0]), "nonzeros": 1_695_358, "sparsity": 0.9999928059662684},
        "factor_shapes": {"users": list(user_factor_shape), "items": list(item_factor_shape)},
        "overall_metrics": selected_metrics, "coverage": coverage,
        "differences": {
            "vs_popularity_ndcg10_absolute": selected_metrics["ndcg_at_10"] - POPULARITY["ndcg_at_10"],
            "vs_popularity_ndcg10_relative": selected_metrics["ndcg_at_10"] / POPULARITY["ndcg_at_10"] - 1,
            "vs_item_cf_ndcg10_absolute": selected_metrics["ndcg_at_10"] - ITEM_CF["ndcg_at_10"],
            "vs_item_cf_ndcg10_relative": selected_metrics["ndcg_at_10"] / ITEM_CF["ndcg_at_10"] - 1,
        },
        "personalization": {
            "received_als_rate": float(received.mean()), "complete_popularity_fallback_rate": float((~received).mean()),
            "partial_popularity_fill_rate": float(partial_fill.mean()),
            "mean_top20_overlap_item_cf": float(overlap_cf.mean() / 20), "mean_top20_overlap_popularity": float(overlap_pop.mean() / 20),
            "differ_from_item_cf_rate": float((overlap_cf < 20).mean()), "differ_from_popularity_rate": float((overlap_pop < 20).mean()),
            "recommended_seen_slot_share": float(seen_slots.sum() / (20 * len(instances))), "recommended_novel_slot_share": float(1 - seen_slots.sum() / (20 * len(instances))),
        },
        "cold_targets": int((~instances.candidate_item_known).sum()), "warm_targets": int(instances.candidate_item_known.sum()),
        "configuration_results": configs.to_dict("records"),
        "compute": {"selected_fit_seconds": float(selected_row.fit_seconds), "selected_scoring_seconds": float(selected_row.scoring_seconds), "selected_serialized_estimator_bytes": int(selected_row.serialized_estimator_bytes), "total_seconds": time.perf_counter() - total_started, "peak_rss_mb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 / 1024},
        "error_category_counts": {name: int(mask.sum()) for name, mask in error_masks.items()},
        "lockbox_status": "no recommendations or ranking performance generated",
    }
    (output / "als_summary.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", default="data/raw/retailrocket/events.csv")
    parser.add_argument("--output-dir", default="reports/recommendation/artifacts")
    args = parser.parse_args()
    print(json.dumps(run_experiment(args.events, args.output_dir), indent=2))


if __name__ == "__main__": main()
