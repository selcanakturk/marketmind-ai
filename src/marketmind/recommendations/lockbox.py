"""Auditable one-time recommendation lockbox evaluation mechanics."""

from __future__ import annotations

import pandas as pd

from marketmind.recommendations.splits import next_item_instances, validate_events

FROZEN_NEIGHBORS = 50


def lockbox_instance_keys(events: pd.DataFrame, recommendation_timestamp, window_end) -> pd.DataFrame:
    """Return eligible visitor keys without revealing target item/event fields."""

    frame = validate_events(events)
    start, end = pd.Timestamp(recommendation_timestamp), pd.Timestamp(window_end)
    history = frame.loc[frame.event_at.le(start)]
    future_visitors = frame.loc[frame.event_at.gt(start) & frame.event_at.lt(end), ["visitorid"]].drop_duplicates()
    counts = history.groupby("visitorid", observed=True).size().rename("history_interaction_count")
    keys = future_visitors.merge(counts, left_on="visitorid", right_index=True, how="inner")
    keys = keys.loc[keys.history_interaction_count.ge(2), ["visitorid"]].copy()
    keys["recommendation_timestamp"] = start
    return keys.sort_values("visitorid").reset_index(drop=True)


def reveal_targets_after_ranking(events, recommendation_timestamp, window_end, preoutcome_rankings):
    """Join target fields only after validating an outcome-free ranking artifact."""

    forbidden = [column for column in preoutcome_rankings if "target" in column.lower()]
    if forbidden:
        raise ValueError(f"pre-outcome rankings contain forbidden target fields: {forbidden}")
    rank_columns = [column for column in preoutcome_rankings if column.startswith("rank_")]
    if len(rank_columns) != 20:
        raise ValueError("pre-outcome artifact must contain exactly 20 rank columns")
    targets = next_item_instances(events, recommendation_timestamp, window_end)
    return targets.merge(
        preoutcome_rankings,
        on=["visitorid", "recommendation_timestamp"],
        validate="one_to_one",
    ).sort_values("visitorid").reset_index(drop=True)
