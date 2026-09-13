"""Frozen, non-personalized, point-in-time popularity baseline."""

from __future__ import annotations

import numpy as np
import pandas as pd

from marketmind.recommendations.splits import validate_events


def popularity_ranking(events: pd.DataFrame, recommendation_timestamp, k: int = 20) -> list[int]:
    """Rank history items by count descending and numeric item ID ascending."""

    if k <= 0:
        raise ValueError("k must be positive")
    frame = validate_events(events)
    cutoff = pd.Timestamp(recommendation_timestamp)
    if cutoff.tzinfo is None:
        cutoff = cutoff.tz_localize("UTC")
    history = frame.loc[frame.event_at.le(cutoff)]
    counts = history.groupby("itemid", observed=True).size().rename("interaction_count").reset_index()
    ranked = counts.sort_values(["interaction_count", "itemid"], ascending=[False, True], kind="mergesort")
    return ranked.itemid.head(k).astype(int).tolist()


def point_in_time_topk(events: pd.DataFrame, instances: pd.DataFrame, k: int = 20) -> pd.DataFrame:
    """Generate top-K without a dense instance-by-catalog matrix.

    One ranking is computed per distinct recommendation timestamp and reused for
    instances at that timestamp because this frozen baseline is non-personalized.
    """

    required = {"visitorid", "recommendation_timestamp"}
    if not required.issubset(instances):
        raise ValueError(f"instances missing columns: {sorted(required.difference(instances))}")
    if instances.visitorid.duplicated().any():
        raise ValueError("each visitor must have one evaluation instance")
    rows = []
    cache = {}
    for instance in instances.sort_values(["recommendation_timestamp", "visitorid"], kind="mergesort").itertuples():
        timestamp = pd.Timestamp(instance.recommendation_timestamp)
        if timestamp not in cache:
            cache[timestamp] = popularity_ranking(events, timestamp, k)
        ranking = cache[timestamp]
        if len(ranking) != len(set(ranking)):
            raise ValueError("popularity ranking contains duplicates")
        rows.append({"visitorid": instance.visitorid, "recommendation_timestamp": timestamp, **{f"rank_{rank}": item for rank, item in enumerate(ranking, 1)}})
    return pd.DataFrame(rows).sort_values("visitorid").reset_index(drop=True)
