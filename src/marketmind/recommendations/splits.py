"""Leakage-safe temporal utilities for RetailRocket recommendation research."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

EVENT_COLUMNS = ("timestamp", "visitorid", "event", "itemid", "transactionid")
EVENT_TYPES = frozenset({"view", "addtocart", "transaction"})


@dataclass(frozen=True)
class TemporalSplit:
    """Half-open global windows; every boundary is an explicit UTC instant."""

    observed_start: pd.Timestamp = pd.Timestamp("2015-05-03 03:00:00", tz="UTC")
    validation_start: pd.Timestamp = pd.Timestamp("2015-08-17 03:00:00", tz="UTC")
    lockbox_start: pd.Timestamp = pd.Timestamp("2015-09-01 03:00:00", tz="UTC")
    observed_end: pd.Timestamp = pd.Timestamp("2015-09-18 03:00:00", tz="UTC")

    def __post_init__(self):
        if not self.observed_start < self.validation_start < self.lockbox_start < self.observed_end:
            raise ValueError("temporal boundaries must be strictly increasing")


def validate_events(events: pd.DataFrame) -> pd.DataFrame:
    """Validate and canonicalize the authentic event schema and milliseconds."""

    missing = set(EVENT_COLUMNS).difference(events.columns)
    if missing:
        raise ValueError(f"events missing required columns: {sorted(missing)}")
    frame = events.loc[:, EVENT_COLUMNS].copy()
    if frame[["timestamp", "visitorid", "event", "itemid"]].isna().any().any():
        raise ValueError("mandatory event fields may not be missing")
    if not set(frame["event"].unique()).issubset(EVENT_TYPES):
        raise ValueError("unknown RetailRocket event type")
    frame["event_at"] = pd.to_datetime(frame["timestamp"], unit="ms", utc=True, errors="raise")
    return frame.sort_values(["event_at", "visitorid", "itemid", "event"], kind="mergesort").reset_index(drop=True)


def chronological_partitions(events: pd.DataFrame, split: TemporalSplit = TemporalSplit()):
    """Return nonoverlapping train, validation, and untouched-lockbox rows."""

    frame = validate_events(events)
    windows = {
        "train": (split.observed_start, split.validation_start),
        "validation": (split.validation_start, split.lockbox_start),
        "lockbox": (split.lockbox_start, split.observed_end),
    }
    return {name: frame.loc[frame.event_at.ge(start) & frame.event_at.lt(end)].copy() for name, (start, end) in windows.items()}


def candidate_items(events: pd.DataFrame, recommendation_at) -> pd.Index:
    """Items observed at or before T; future-only items cannot enter ranking."""

    frame = validate_events(events)
    cutoff = pd.Timestamp(recommendation_at)
    if cutoff.tzinfo is None:
        cutoff = cutoff.tz_localize("UTC")
    return pd.Index(sorted(frame.loc[frame.event_at.le(cutoff), "itemid"].unique()), name="itemid")


def next_item_instances(
    events: pd.DataFrame,
    recommendation_at,
    window_end,
    *,
    min_prior_interactions: int = 2,
) -> pd.DataFrame:
    """Create one single-target next-interaction instance per eligible visitor.

    The target is the visitor's first event in ``(T, window_end)``. History is
    at or before T. Previously seen targets remain valid and are labeled.
    """

    if min_prior_interactions < 1:
        raise ValueError("min_prior_interactions must be positive")
    frame = validate_events(events)
    start, end = pd.Timestamp(recommendation_at), pd.Timestamp(window_end)
    if start.tzinfo is None:
        start = start.tz_localize("UTC")
    if end.tzinfo is None:
        end = end.tz_localize("UTC")
    if start >= end:
        raise ValueError("recommendation_at must precede window_end")
    history = frame.loc[frame.event_at.le(start)]
    future = frame.loc[frame.event_at.gt(start) & frame.event_at.lt(end)]
    first = future.drop_duplicates("visitorid", keep="first")
    history_summary = history.groupby("visitorid", observed=True).agg(
        history_interaction_count=("event", "size"),
        history_unique_item_count=("itemid", "nunique"),
    )
    instances = first.merge(history_summary, left_on="visitorid", right_index=True, how="inner")
    instances = instances.loc[instances.history_interaction_count.ge(min_prior_interactions)].copy()
    seen_pairs = history[["visitorid", "itemid"]].drop_duplicates().assign(target_previously_seen=True)
    instances = instances.merge(seen_pairs, on=["visitorid", "itemid"], how="left")
    instances["target_previously_seen"] = instances["target_previously_seen"].fillna(False).astype(bool)
    instances["candidate_item_known"] = instances["itemid"].isin(history["itemid"])
    instances = instances.rename(columns={"event_at": "target_timestamp", "itemid": "target_itemid", "event": "target_event"})
    instances["recommendation_timestamp"] = start
    return instances[[
        "visitorid", "recommendation_timestamp", "target_timestamp",
        "target_itemid", "target_event", "history_interaction_count",
        "history_unique_item_count", "target_previously_seen", "candidate_item_known",
    ]].sort_values("visitorid").reset_index(drop=True)
