"""Notebook-independent production inference for the frozen Item-CF engine."""

from __future__ import annotations

import numpy as np
import pandas as pd

from marketmind.recommendations.bundle import RecommendationBundle, load_bundle
from marketmind.recommendations.config import DEFAULT_K, MAX_K
from marketmind.recommendations.train import validate_events

OUTPUT_COLUMNS = (
    "visitorid", "snapshot_timestamp", "rank", "itemid", "recommendation_score",
    "score_source", "was_previously_seen", "collaborative_candidate_count",
    "used_popularity_fill", "known_history_item_count", "fallback_reason",
)


def _snapshot_ms(snapshot_timestamp: str | int | pd.Timestamp) -> tuple[int, pd.Timestamp]:
    if isinstance(snapshot_timestamp, (int, np.integer)):
        value = int(snapshot_timestamp)
        if value < 0:
            raise ValueError("snapshot_timestamp must be nonnegative")
        return value, pd.to_datetime(value, unit="ms", utc=True)
    parsed = pd.Timestamp(snapshot_timestamp)
    if pd.isna(parsed):
        raise ValueError("snapshot_timestamp must be explicit and valid")
    if parsed.tzinfo is None:
        parsed = parsed.tz_localize("UTC")
    else:
        parsed = parsed.tz_convert("UTC")
    return int(parsed.timestamp() * 1000), parsed


def recommend_visitor(
    events: pd.DataFrame,
    visitorid: int,
    snapshot_timestamp: str | int | pd.Timestamp,
    bundle: RecommendationBundle,
    k: int = DEFAULT_K,
) -> pd.DataFrame:
    """Recommend unique items available at explicit T; rows after T are ignored."""
    bundle.validate()
    if not isinstance(k, (int, np.integer)) or not 1 <= int(k) <= MAX_K:
        raise ValueError(f"k must be an integer in [1, {MAX_K}]")
    try:
        visitor = int(visitorid)
    except (TypeError, ValueError) as error:
        raise ValueError("visitorid must be an integer") from error
    if visitor < 0 or visitor != visitorid:
        raise ValueError("visitorid must be a nonnegative integer")
    snapshot_ms, snapshot = _snapshot_ms(snapshot_timestamp)
    if snapshot_ms < bundle.training_cutoff_ms:
        raise ValueError("snapshot precedes this all-history artifact's training cutoff")

    frame = validate_events(events)
    current = frame.loc[frame["timestamp"] <= snapshot_ms]
    if current.empty:
        raise ValueError("no items are available by the scoring snapshot")
    history = current.loc[current["visitorid"] == visitor, "itemid"].drop_duplicates().to_numpy(np.int64)
    history_set = set(map(int, history))
    known_history = sorted(item for item in history_set if item in bundle.item_to_index)
    available = set(map(int, current["itemid"].unique()))

    scores: dict[int, float] = {}
    for item in known_history:
        row = bundle.item_to_index[item]
        start, end = bundle.neighbor_indptr[row:row + 2]
        for neighbor, similarity in zip(bundle.neighbor_indices[start:end], bundle.neighbor_similarities[start:end]):
            candidate = int(bundle.item_ids[neighbor])
            if candidate in available:
                scores[candidate] = scores.get(candidate, 0.0) + float(similarity)
    collaborative = sorted(scores, key=lambda item: (-scores[item], item))
    selected = collaborative[:int(k)]
    sources = ["collaborative"] * len(selected)
    selected_scores = [scores[item] for item in selected]
    selected_set = set(selected)

    popularity = current.groupby("itemid", sort=False).size().rename("count").reset_index()
    popularity = popularity.sort_values(["count", "itemid"], ascending=[False, True], kind="mergesort")
    if len(selected) < k:
        for row in popularity.itertuples(index=False):
            item = int(row.itemid)
            if item not in selected_set:
                selected.append(item)
                sources.append("popularity_fill")
                selected_scores.append(float(row.count))
                selected_set.add(item)
                if len(selected) == k:
                    break
    fallback_reason = ""
    if not history_set:
        fallback_reason = "no_history"
    elif not known_history:
        fallback_reason = "no_collaborative_history"
    elif not scores:
        fallback_reason = "no_available_collaborative_candidates"
    used_fill = "popularity_fill" in sources
    result = pd.DataFrame({
        "visitorid": visitor, "snapshot_timestamp": snapshot, "rank": np.arange(1, len(selected) + 1),
        "itemid": selected, "recommendation_score": selected_scores, "score_source": sources,
        "was_previously_seen": [item in history_set for item in selected],
        "collaborative_candidate_count": len(scores), "used_popularity_fill": used_fill,
        "known_history_item_count": len(known_history), "fallback_reason": fallback_reason,
    })
    if result["itemid"].duplicated().any():
        raise RuntimeError("production ranking contains duplicate item IDs")
    return result.loc[:, OUTPUT_COLUMNS]


def recommend_batch(events, visitorids, snapshot_timestamp, bundle, k=DEFAULT_K) -> pd.DataFrame:
    """Score visitors deterministically in caller order."""
    frames = [recommend_visitor(events, visitor, snapshot_timestamp, bundle, k) for visitor in visitorids]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=OUTPUT_COLUMNS)


def recommend_from_artifact(events, visitorid, snapshot_timestamp, artifact_path, k=DEFAULT_K):
    return recommend_visitor(events, visitorid, snapshot_timestamp, load_bundle(artifact_path), k)
