"""Reusable aggregate-only RetailRocket audit helpers; no recommender code."""

from __future__ import annotations

import pandas as pd

from marketmind.recommendations.splits import validate_events


def event_summary(events: pd.DataFrame) -> pd.DataFrame:
    frame = validate_events(events)
    summary = frame.groupby("event", observed=True).agg(
        events=("event", "size"), visitors=("visitorid", "nunique"), items=("itemid", "nunique")
    )
    summary["event_share"] = summary["events"] / len(frame)
    return summary


def daily_activity(events: pd.DataFrame) -> pd.DataFrame:
    frame = validate_events(events).assign(source_day=lambda x: (x.event_at - pd.Timedelta(hours=3)).dt.floor("D"))
    frame["transaction_event"] = frame.event.eq("transaction")
    return frame.groupby("source_day", observed=True).agg(
        events=("event", "size"), visitors=("visitorid", "nunique"),
        items=("itemid", "nunique"), transaction_events=("transaction_event", "sum"),
    )
