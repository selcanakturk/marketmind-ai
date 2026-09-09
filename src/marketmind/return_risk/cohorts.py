"""Leakage-safe household cohort and future-outcome construction.

This module intentionally constructs eligibility and labels only. It does not
create predictive features or a model-ready matrix.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

REQUIRED_COLUMNS = ("household_id", "basket_id", "transaction_timestamp")


class RightCensoringError(ValueError):
    """Raised when a requested outcome window is not fully observable."""


@dataclass(frozen=True)
class EligibilityRule:
    """Deterministic minimum history requirements at a prediction snapshot."""

    min_observed_history_days: int = 90
    min_baskets: int = 5
    min_active_span_days: int = 30

    def __post_init__(self) -> None:
        values = (
            self.min_observed_history_days,
            self.min_baskets,
            self.min_active_span_days,
        )
        if any(value < 0 for value in values):
            raise ValueError("eligibility thresholds must be nonnegative")


def _validated_transactions(transactions: pd.DataFrame) -> pd.DataFrame:
    missing = set(REQUIRED_COLUMNS).difference(transactions.columns)
    if missing:
        raise ValueError(f"transactions is missing required columns: {sorted(missing)}")
    if transactions[list(REQUIRED_COLUMNS)].isna().any().any():
        raise ValueError("transactions contains missing mandatory values")
    tx = transactions.loc[:, REQUIRED_COLUMNS].copy()
    tx["transaction_timestamp"] = pd.to_datetime(
        tx["transaction_timestamp"], errors="raise"
    )
    if (tx.groupby("basket_id", observed=True)["household_id"].nunique() > 1).any():
        raise ValueError("a basket_id may not map to multiple households")
    return tx


def history_through_snapshot(
    transactions: pd.DataFrame, snapshot_at: str | pd.Timestamp
) -> pd.DataFrame:
    """Return only transaction lines known at or before snapshot time T."""

    tx = _validated_transactions(transactions)
    snapshot = pd.Timestamp(snapshot_at)
    return tx.loc[tx["transaction_timestamp"] <= snapshot].copy()


def household_eligibility(
    transactions: pd.DataFrame,
    snapshot_at: str | pd.Timestamp,
    rule: EligibilityRule = EligibilityRule(),
) -> pd.DataFrame:
    """Return one auditable eligibility row per household observed by T."""

    snapshot = pd.Timestamp(snapshot_at)
    history = history_through_snapshot(transactions, snapshot)
    if history.empty:
        raise ValueError("no households were observed by snapshot_at")
    result = history.groupby("household_id", observed=True).agg(
        first_transaction=("transaction_timestamp", "min"),
        last_transaction=("transaction_timestamp", "max"),
        basket_count=("basket_id", "nunique"),
    )
    result["observed_history_days"] = (
        snapshot.normalize() - result["first_transaction"].dt.normalize()
    ).dt.days
    result["active_span_days"] = (
        result["last_transaction"].dt.normalize()
        - result["first_transaction"].dt.normalize()
    ).dt.days
    result["eligible"] = (
        result["observed_history_days"].ge(rule.min_observed_history_days)
        & result["basket_count"].ge(rule.min_baskets)
        & result["active_span_days"].ge(rule.min_active_span_days)
    )
    return result.sort_index()


def future_outcomes(
    transactions: pd.DataFrame,
    household_ids,
    snapshot_at: str | pd.Timestamp,
    horizon_days: int,
    observation_end: str | pd.Timestamp,
) -> pd.DataFrame:
    """Label basket return in the complete interval ``(T, T + H]``.

    ``return_risk_target=1`` means no distinct basket was observed in that
    complete interval. It does not mean contractual churn.
    """

    if horizon_days <= 0:
        raise ValueError("horizon_days must be positive")
    tx = _validated_transactions(transactions)
    snapshot = pd.Timestamp(snapshot_at)
    outcome_end = snapshot + pd.Timedelta(days=horizon_days)
    observed_through = pd.Timestamp(observation_end)
    if outcome_end > observed_through:
        raise RightCensoringError(
            f"outcome ends {outcome_end}, after observation_end {observed_through}"
        )
    household_index = pd.Index(household_ids, name="household_id").drop_duplicates()
    future = tx.loc[
        tx["transaction_timestamp"].gt(snapshot)
        & tx["transaction_timestamp"].le(outcome_end)
        & tx["household_id"].isin(household_index)
    ]
    counts = future.groupby("household_id", observed=True)["basket_id"].nunique()
    result = counts.reindex(household_index, fill_value=0).rename("future_baskets").to_frame()
    result["return_flag"] = result["future_baskets"].gt(0).astype("int8")
    result["return_risk_target"] = result["return_flag"].eq(0).astype("int8")
    result["snapshot_at"] = snapshot
    result["outcome_end"] = outcome_end
    return result


def build_labeled_cohort(
    transactions: pd.DataFrame,
    snapshot_at: str | pd.Timestamp,
    horizon_days: int,
    observation_end: str | pd.Timestamp,
    rule: EligibilityRule = EligibilityRule(),
) -> pd.DataFrame:
    """Combine point-in-time eligibility attributes and complete outcomes."""

    eligibility = household_eligibility(transactions, snapshot_at, rule)
    eligible = eligibility.loc[eligibility["eligible"]].copy()
    outcomes = future_outcomes(
        transactions,
        eligible.index,
        snapshot_at,
        horizon_days,
        observation_end,
    )
    return eligible.join(outcomes, validate="one_to_one")
