"""Point-in-time feature construction for Customer Return Risk baselines."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler

from marketmind.return_risk.cohorts import EligibilityRule, household_eligibility
from marketmind.segmentation.snapshot import validate_snapshot_inputs

CANDIDATE_FEATURE_ORDER = (
    "recency_days",
    "basket_frequency_lifetime",
    "monetary_lifetime",
    "average_basket_value",
    "baskets_last_7d",
    "baskets_last_14d",
    "baskets_last_28d",
    "baskets_last_56d",
    "spend_last_28d",
    "spend_last_56d",
    "median_days_between_baskets",
    "mean_days_between_baskets",
    "std_days_between_baskets",
    "active_span_days",
    "active_days",
    "active_weeks",
    "active_months",
    "unique_products",
    "unique_departments",
    "department_spend_hhi",
    "discount_share_of_gross",
    "coupon_basket_rate",
    "discounted_basket_rate",
    "baskets_28d_change",
    "spend_28d_change",
)

# Frozen after the training-only audit in Phase 3 Step 2.
BASELINE_FEATURE_ORDER = (
    "recency_days",
    "basket_frequency_lifetime",
    "monetary_lifetime",
    "average_basket_value",
    "baskets_last_7d",
    "baskets_last_28d",
    "spend_last_28d",
    "median_days_between_baskets",
    "std_days_between_baskets",
    "active_span_days",
    "unique_departments",
    "department_spend_hhi",
    "discount_share_of_gross",
    "coupon_basket_rate",
    "baskets_28d_change",
    "spend_28d_change",
)

LOG1P_FEATURES = (
    "recency_days",
    "basket_frequency_lifetime",
    "monetary_lifetime",
    "average_basket_value",
    "baskets_last_7d",
    "baskets_last_28d",
    "spend_last_28d",
    "median_days_between_baskets",
    "std_days_between_baskets",
    "active_span_days",
    "unique_departments",
)


class FrozenLog1pTransformer(BaseEstimator, TransformerMixin):
    """Apply the frozen log policy while preserving the baseline feature order."""

    def fit(self, X, y=None):
        frame = pd.DataFrame(X)
        if tuple(frame.columns) != BASELINE_FEATURE_ORDER:
            raise ValueError("baseline feature order does not match the frozen contract")
        return self

    def transform(self, X):
        frame = pd.DataFrame(X).copy()
        if tuple(frame.columns) != BASELINE_FEATURE_ORDER:
            raise ValueError("baseline feature order does not match the frozen contract")
        if (frame.loc[:, LOG1P_FEATURES] < 0).any().any():
            raise ValueError("log1p baseline features must be nonnegative")
        frame.loc[:, LOG1P_FEATURES] = np.log1p(frame.loc[:, LOG1P_FEATURES])
        return frame

    def get_feature_names_out(self, input_features=None):
        return np.asarray(BASELINE_FEATURE_ORDER, dtype=object)


def make_logistic_preprocessor() -> Pipeline:
    """Return the fixed log1p plus RobustScaler training-fit pipeline."""

    return Pipeline([
        ("log1p", FrozenLog1pTransformer()),
        ("scale", RobustScaler()),
    ])


def _window(baskets: pd.DataFrame, snapshot: pd.Timestamp, days: int) -> pd.DataFrame:
    """Return basket rows in the history-only interval ``(T-days, T]``."""

    return baskets.loc[
        baskets["basket_timestamp"].gt(snapshot - pd.Timedelta(days=days))
        & baskets["basket_timestamp"].le(snapshot)
    ]


def build_candidate_features(
    transactions: pd.DataFrame,
    products: pd.DataFrame,
    snapshot_at: str | pd.Timestamp,
    rule: EligibilityRule = EligibilityRule(),
) -> pd.DataFrame:
    """Build deterministic candidate features using observations at or before T."""

    snapshot = pd.Timestamp(snapshot_at)
    tx, product = validate_snapshot_inputs(transactions, products)
    eligibility = household_eligibility(tx, snapshot, rule)
    eligible_ids = eligibility.index[eligibility["eligible"]]
    tx = tx.loc[
        tx["transaction_timestamp"].le(snapshot)
        & tx["household_id"].isin(eligible_ids)
    ].copy()
    tx = tx.merge(
        product[["product_id", "department"]].drop_duplicates("product_id"),
        on="product_id",
        how="left",
        validate="many_to_one",
    )
    tx["department"] = tx["department"].fillna("UNKNOWN")
    tx["discount_value"] = tx[
        ["retail_disc", "coupon_disc", "coupon_match_disc"]
    ].sum(axis=1)
    tx["coupon_value"] = tx[["coupon_disc", "coupon_match_disc"]].sum(axis=1)
    tx["gross_value"] = tx["sales_value"] + tx["discount_value"]

    baskets = tx.groupby(["household_id", "basket_id"], observed=True).agg(
        basket_timestamp=("transaction_timestamp", "min"),
        basket_sales=("sales_value", "sum"),
        discount_value=("discount_value", "sum"),
        coupon_value=("coupon_value", "sum"),
        gross_value=("gross_value", "sum"),
    ).reset_index()
    baskets = baskets.sort_values(["household_id", "basket_timestamp", "basket_id"])
    gaps = baskets.groupby("household_id", observed=True)["basket_timestamp"].diff()
    baskets["gap_days"] = gaps.dt.total_seconds().div(86400)

    base = baskets.groupby("household_id", observed=True).agg(
        last_basket=("basket_timestamp", "max"),
        first_basket=("basket_timestamp", "min"),
        basket_frequency_lifetime=("basket_id", "nunique"),
        monetary_lifetime=("basket_sales", "sum"),
        average_basket_value=("basket_sales", "mean"),
        median_days_between_baskets=("gap_days", "median"),
        mean_days_between_baskets=("gap_days", "mean"),
        std_days_between_baskets=("gap_days", "std"),
        coupon_baskets=("coupon_value", lambda s: int(s.gt(0).sum())),
        discounted_baskets=("discount_value", lambda s: int(s.gt(0).sum())),
        discounts=("discount_value", "sum"),
        gross=("gross_value", "sum"),
    )
    base["recency_days"] = (
        snapshot.normalize() - base["last_basket"].dt.normalize()
    ).dt.days
    base["active_span_days"] = (
        base["last_basket"].dt.normalize() - base["first_basket"].dt.normalize()
    ).dt.days
    base["coupon_basket_rate"] = base["coupon_baskets"] / base["basket_frequency_lifetime"]
    base["discounted_basket_rate"] = base["discounted_baskets"] / base["basket_frequency_lifetime"]
    base["discount_share_of_gross"] = np.divide(
        base["discounts"], base["gross"], out=np.zeros(len(base)), where=base["gross"].gt(0)
    )

    active = tx.assign(
        active_date=tx["transaction_timestamp"].dt.normalize(),
        active_week=tx["transaction_timestamp"].dt.to_period("W"),
        active_month=tx["transaction_timestamp"].dt.to_period("M"),
    ).groupby("household_id", observed=True).agg(
        active_days=("active_date", "nunique"),
        active_weeks=("active_week", "nunique"),
        active_months=("active_month", "nunique"),
        unique_products=("product_id", "nunique"),
        unique_departments=("department", "nunique"),
    )
    dept = tx.groupby(["household_id", "department"], observed=True)["sales_value"].sum()
    positive_dept = dept.clip(lower=0)
    dept_total = positive_dept.groupby(level=0).sum()
    hhi = positive_dept.div(dept_total.replace(0, np.nan), level=0).pow(2).groupby(level=0).sum()
    active["department_spend_hhi"] = hhi.fillna(0)

    features = base.join(active)
    for days in (7, 14, 28, 56):
        recent = _window(baskets, snapshot, days)
        features[f"baskets_last_{days}d"] = recent.groupby("household_id")["basket_id"].nunique().reindex(features.index, fill_value=0)
    for days in (28, 56):
        recent = _window(baskets, snapshot, days)
        features[f"spend_last_{days}d"] = recent.groupby("household_id")["basket_sales"].sum().reindex(features.index, fill_value=0.0)

    previous = baskets.loc[
        baskets["basket_timestamp"].gt(snapshot - pd.Timedelta(days=56))
        & baskets["basket_timestamp"].le(snapshot - pd.Timedelta(days=28))
    ]
    previous_count = previous.groupby("household_id")["basket_id"].nunique().reindex(features.index, fill_value=0)
    previous_spend = previous.groupby("household_id")["basket_sales"].sum().reindex(features.index, fill_value=0.0)
    features["baskets_28d_change"] = features["baskets_last_28d"] - previous_count
    features["spend_28d_change"] = features["spend_last_28d"] - previous_spend

    features["std_days_between_baskets"] = features["std_days_between_baskets"].fillna(0)
    result = features.loc[:, CANDIDATE_FEATURE_ORDER].astype(float)
    result.index.name = "household_id"
    return result.sort_index()


def baseline_features(candidate_features: pd.DataFrame) -> pd.DataFrame:
    """Select the training-audit-frozen baseline columns in deterministic order."""

    missing = set(BASELINE_FEATURE_ORDER).difference(candidate_features.columns)
    if missing:
        raise ValueError(f"candidate features missing frozen columns: {sorted(missing)}")
    return candidate_features.loc[:, BASELINE_FEATURE_ORDER].copy()
