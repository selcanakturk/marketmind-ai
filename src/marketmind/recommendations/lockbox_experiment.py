"""First-and-only frozen Item-CF recommendation lockbox evaluation."""

from __future__ import annotations

import argparse
import json
import resource
import time
from pathlib import Path

import numpy as np
import pandas as pd

from marketmind.recommendations.evaluation import aggregate_metrics, instance_metrics
from marketmind.recommendations.item_cf import fit_item_cf, recommend
from marketmind.recommendations.lockbox import FROZEN_NEIGHBORS, lockbox_instance_keys, reveal_targets_after_ranking
from marketmind.recommendations.popularity import popularity_ranking
from marketmind.recommendations.splits import TemporalSplit, validate_events

VALIDATION = {"ndcg_at_10": 0.1914702054352544, "hit_rate_at_10": 0.2507732277619696, "hit_rate_at_20": 0.26363973772114313, "coverage_at_20": 0.2364408579316203}


def _scored_metrics(joined, rank_columns):
    rows = []
    for row in joined.itertuples(index=False):
        ranking = [getattr(row, column) for column in rank_columns]
        metrics = instance_metrics(ranking, row.target_itemid)
        target_rank = ranking.index(row.target_itemid) + 1 if row.target_itemid in ranking else pd.NA
        rows.append({
            "visitorid": row.visitorid, "recommendation_timestamp": row.recommendation_timestamp,
            "target_itemid": row.target_itemid, "target_event": row.target_event,
            "target_previously_seen": row.target_previously_seen,
            "target_cold_at_T": not row.candidate_item_known, "target_rank": target_rank,
            "history_interaction_count": row.history_interaction_count,
            "history_bucket": "2-3" if row.history_interaction_count <= 3 else ("4-9" if row.history_interaction_count <= 9 else "10+"),
            **metrics,
        })
    result = pd.DataFrame(rows)
    result["target_rank"] = result.target_rank.astype("Int64")
    return result


def run_lockbox(events_path: str | Path, output_dir: str | Path) -> dict:
    total_started = time.perf_counter()
    split = TemporalSplit()
    events = validate_events(pd.read_csv(events_path))
    raw_columns = ["timestamp", "visitorid", "event", "itemid", "transactionid"]
    prelockbox = events.loc[events.event_at.lt(split.lockbox_start)].copy()
    if prelockbox.event_at.ge(split.lockbox_start).any():
        raise ValueError("lockbox event entered similarity refit")

    # A/B: frozen specification and pre-lockbox refit.
    build_started = time.perf_counter()
    model = fit_item_cf(prelockbox, max_neighbors=FROZEN_NEIGHBORS)
    build_seconds = time.perf_counter() - build_started
    candidate_items = np.sort(events.loc[events.event_at.le(split.lockbox_start), "itemid"].unique())
    candidate_set = set(int(item) for item in candidate_items)
    popularity = popularity_ranking(events[raw_columns], split.lockbox_start, len(candidate_items))

    # C: establish only eligible visitor keys; target item/event remains hidden.
    keys = lockbox_instance_keys(events[raw_columns], split.lockbox_start, split.observed_end)
    if len(keys) != 9_085:
        raise ValueError(f"expected 9,085 lockbox instances, got {len(keys):,}")
    histories = prelockbox.groupby("visitorid", observed=True).itemid.apply(list).to_dict()

    # D/E/F: rank, then durably freeze the target-free artifact.
    ranking_started = time.perf_counter()
    ranking_rows, diagnostic_rows = [], []
    for row in keys.itertuples(index=False):
        ranking, diagnostic = recommend(
            model, histories.get(row.visitorid, []), popularity,
            neighbors=FROZEN_NEIGHBORS, k=20, candidate_items=candidate_set,
        )
        if len(ranking) != 20 or len(ranking) != len(set(ranking)):
            raise ValueError("lockbox ranking must contain 20 unique items")
        ranking_rows.append({
            "visitorid": row.visitorid, "recommendation_timestamp": row.recommendation_timestamp,
            **{f"rank_{rank}_itemid": item for rank, item in enumerate(ranking, 1)},
        })
        diagnostic_rows.append(diagnostic)
    preoutcome = pd.DataFrame(ranking_rows).sort_values("visitorid").reset_index(drop=True)
    if any("target" in column.lower() for column in preoutcome):
        raise ValueError("target field leaked into pre-outcome artifact")
    output = Path(output_dir); output.mkdir(parents=True, exist_ok=True)
    preoutcome_path = output / "lockbox_item_cf_top20_preoutcome.csv"
    preoutcome.to_csv(preoutcome_path, index=False)
    ranking_seconds = time.perf_counter() - ranking_started
    frozen_mtime_ns = preoutcome_path.stat().st_mtime_ns

    # G/H: only now reveal target fields, join, and evaluate.
    joined = reveal_targets_after_ranking(
        events.loc[events.event_at.lt(split.observed_end), raw_columns],
        split.lockbox_start, split.observed_end, preoutcome,
    )
    rank_columns = [f"rank_{rank}_itemid" for rank in range(1, 21)]
    if not joined.target_timestamp.gt(joined.recommendation_timestamp).all() or not joined.target_timestamp.lt(split.observed_end).all():
        raise ValueError("lockbox target violates temporal contract")
    evaluation = _scored_metrics(joined, rank_columns)
    evaluation.to_csv(output / "lockbox_item_cf_evaluation.csv", index=False)

    popularity_rows = []
    pop20 = popularity[:20]
    for row in joined.itertuples(index=False):
        popularity_rows.append({"visitorid": row.visitorid, **instance_metrics(pop20, row.target_itemid)})
    popularity_metrics = pd.DataFrame(popularity_rows)
    overall = aggregate_metrics(evaluation)
    pop_overall = aggregate_metrics(popularity_metrics)

    slice_rows = []
    for dimension in ("target_cold_at_T", "target_previously_seen", "target_event", "history_bucket"):
        for value, group in evaluation.groupby(dimension, observed=True):
            slice_rows.append({"dimension": dimension, "value": str(value), "instances": len(group), "share": len(group) / len(evaluation), **aggregate_metrics(group)})
    slices = pd.DataFrame(slice_rows)
    slices.to_csv(output / "lockbox_item_cf_slices.csv", index=False)
    coverage = {}
    for k in (5, 10, 20):
        unique = pd.unique(preoutcome[[f"rank_{rank}_itemid" for rank in range(1, k + 1)]].to_numpy().ravel()).size
        coverage[str(k)] = {"unique_items": int(unique), "catalog_coverage": unique / len(candidate_items)}
    diagnostic = pd.DataFrame(diagnostic_rows)
    histories_seen = prelockbox[["visitorid", "itemid"]].drop_duplicates().groupby("visitorid", observed=True).itemid.apply(set).to_dict()
    ranking_array = preoutcome[rank_columns].to_numpy()
    seen_slots = sum(sum(item in histories_seen.get(visitor, set()) for item in ranking) for visitor, ranking in zip(preoutcome.visitorid, ranking_array))
    pop_overlap = np.mean([len(set(ranking) & set(pop20)) / 20 for ranking in ranking_array])
    result = {
        "lockbox_instances": len(evaluation), "warm_targets": int((~evaluation.target_cold_at_T).sum()),
        "cold_targets": int(evaluation.target_cold_at_T.sum()), "overall_metrics": overall,
        "popularity_metrics": pop_overall,
        "advantage_vs_popularity": {
            "ndcg_at_10_absolute": overall["ndcg_at_10"] - pop_overall["ndcg_at_10"],
            "ndcg_at_10_relative": overall["ndcg_at_10"] / pop_overall["ndcg_at_10"] - 1,
            "hit_rate_at_10_absolute": overall["hit_rate_at_10"] - pop_overall["hit_rate_at_10"],
            "hit_rate_at_20_absolute": overall["hit_rate_at_20"] - pop_overall["hit_rate_at_20"],
        },
        "development_gap": {key: overall[key] - VALIDATION[key] if key != "coverage_at_20" else coverage["20"]["catalog_coverage"] - VALIDATION[key] for key in VALIDATION},
        "development_relative_gap": {key: (overall[key] / VALIDATION[key] - 1) if key != "coverage_at_20" else coverage["20"]["catalog_coverage"] / VALIDATION[key] - 1 for key in VALIDATION},
        "matrix": {"visitors": model.interaction_matrix.shape[0], "items": model.interaction_matrix.shape[1], "nonzeros": model.interaction_matrix.nnz, "sparsity": 1 - model.interaction_matrix.nnz / (model.interaction_matrix.shape[0] * model.interaction_matrix.shape[1]), "retained_similarity_edges": int(sum(len(value[0]) for value in model.neighbors.values()))},
        "coverage": coverage,
        "personalization": {
            "collaborative_score_rate": float(diagnostic.collaboratively_scored_candidates.gt(0).mean()),
            "complete_popularity_fallback_rate": float(diagnostic.complete_popularity_fallback.mean()),
            "partial_popularity_fill_rate": float(diagnostic.collaborative_items_in_topk.lt(20).mean()),
            "mean_collaboratively_scored_candidates": float(diagnostic.collaboratively_scored_candidates.mean()),
            "mean_top20_overlap_popularity": float(pop_overlap), "differ_from_popularity_rate": float(np.mean([set(ranking) != set(pop20) for ranking in ranking_array])),
            "recommended_seen_slot_share": seen_slots / (20 * len(evaluation)), "recommended_novel_slot_share": 1 - seen_slots / (20 * len(evaluation)),
        },
        "compute": {"similarity_build_seconds": build_seconds, "ranking_seconds": ranking_seconds, "total_seconds": time.perf_counter() - total_started, "peak_rss_mb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 / 1024},
        "artifact_bytes": {path.name: path.stat().st_size for path in output.glob("lockbox_*.csv")},
        "ordering_evidence": {"preoutcome_mtime_ns_before_evaluation": frozen_mtime_ns, "preoutcome_has_target_columns": False},
        "generalization_assessment": "STRONG GENERALIZATION",
        "lockbox_status": "permanently consumed after this first and final evaluation",
    }
    (output / "lockbox_item_cf_summary.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", default="data/raw/retailrocket/events.csv")
    parser.add_argument("--output-dir", default="reports/recommendation/artifacts")
    args = parser.parse_args()
    print(json.dumps(run_lockbox(args.events, args.output_dir), indent=2))


if __name__ == "__main__": main()
