"""Point-in-time household feature construction for Complete Journey.

This module deliberately stops at an auditable, unscaled feature table. It does
not fit a scaler, choose a clustering algorithm, or assign segment labels.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from marketmind.segmentation.config import (
    ELIGIBILITY_MIN_ACTIVE_SPAN_DAYS,
    ELIGIBILITY_MIN_BASKETS,
    ELIGIBILITY_MIN_HISTORY_DAYS,
)

TRANSACTION_REQUIRED_COLUMNS = (
    "household_id", "store_id", "basket_id", "product_id", "sales_value",
    "retail_disc", "coupon_disc", "coupon_match_disc", "transaction_timestamp",
)
PRODUCT_REQUIRED_COLUMNS = ("product_id", "department", "brand")


@dataclass(frozen=True)
class EligibilityAudit:
    """Deterministic, sequential household eligibility counts."""

    observed_households: int
    excluded_insufficient_history: int
    excluded_insufficient_baskets: int
    excluded_insufficient_active_span: int
    eligible_households: int


@dataclass(frozen=True)
class SnapshotResult:
    """Unscaled feature table and its eligibility audit."""

    features: pd.DataFrame
    eligibility: EligibilityAudit


def _require_columns(frame: pd.DataFrame, required: set[str], name: str) -> None:
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"{name} is missing required columns: {sorted(missing)}")


def validate_snapshot_inputs(
    transactions: pd.DataFrame, products: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Validate the frozen Complete Journey input contract without imputation."""

    _require_columns(transactions, set(TRANSACTION_REQUIRED_COLUMNS), "transactions")
    _require_columns(products, set(PRODUCT_REQUIRED_COLUMNS), "products")
    tx = transactions.copy()
    product = products.copy()
    if tx[list(TRANSACTION_REQUIRED_COLUMNS)].isna().any().any():
        raise ValueError("transactions contains missing mandatory values")
    if product["product_id"].isna().any():
        raise ValueError("products contains missing product_id values")
    tx["transaction_timestamp"] = pd.to_datetime(
        tx["transaction_timestamp"], errors="raise"
    )
    numeric = ["sales_value", "retail_disc", "coupon_disc", "coupon_match_disc"]
    values = tx[numeric].apply(pd.to_numeric, errors="raise").to_numpy(float)
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("sales and discount inputs must be finite and nonnegative")
    if tx.duplicated(["basket_id", "product_id"]).any():
        raise ValueError("transactions contains duplicate basket-product rows")
    if (tx.groupby("basket_id")["household_id"].nunique() > 1).any():
        raise ValueError("a basket_id may not map to multiple households")
    if (tx.groupby("basket_id")["store_id"].nunique() > 1).any():
        raise ValueError("a basket_id may not map to multiple stores")
    if product["product_id"].duplicated().any():
        raise ValueError("products contains duplicate product_id rows")
    return tx, product


def household_eligibility_table(
    transactions: pd.DataFrame,
    *,
    snapshot_at: str | pd.Timestamp,
    min_observed_history_days: int = ELIGIBILITY_MIN_HISTORY_DAYS,
    min_baskets: int = ELIGIBILITY_MIN_BASKETS,
    min_active_span_days: int = ELIGIBILITY_MIN_ACTIVE_SPAN_DAYS,
) -> pd.DataFrame:
    """Return one deterministic eligibility row per household observed by T."""

    cutoff = pd.Timestamp(snapshot_at)
    tx = transactions.loc[transactions["transaction_timestamp"] <= cutoff]
    if tx.empty:
        raise ValueError("No transactions exist on or before snapshot_at")
    household = tx.groupby("household_id", observed=True).agg(
        first_transaction=("transaction_timestamp", "min"),
        last_transaction=("transaction_timestamp", "max"),
        basket_frequency=("basket_id", "nunique"),
    )
    cutoff_day = cutoff.normalize()
    household["observed_history_days"] = (
        cutoff_day - household["first_transaction"].dt.normalize()
    ).dt.days
    household["active_span_days"] = (
        household["last_transaction"].dt.normalize()
        - household["first_transaction"].dt.normalize()
    ).dt.days
    household["eligible"] = (
        (household["observed_history_days"] >= min_observed_history_days)
        & (household["basket_frequency"] >= min_baskets)
        & (household["active_span_days"] >= min_active_span_days)
    )
    return household


def build_household_snapshot(
    transactions: pd.DataFrame,
    products: pd.DataFrame,
    *,
    snapshot_at: str | pd.Timestamp,
    min_observed_history_days: int = ELIGIBILITY_MIN_HISTORY_DAYS,
    min_baskets: int = ELIGIBILITY_MIN_BASKETS,
    min_active_span_days: int = ELIGIBILITY_MIN_ACTIVE_SPAN_DAYS,
) -> SnapshotResult:
    """Build the Phase 2 candidate feature matrix as known at ``snapshot_at``.

    Eligibility filters are applied sequentially in the order documented by the
    methodology: observed history, basket count, then active span. All monetary
    values are in the source dataset's nominal currency units.
    """

    cutoff = pd.Timestamp(snapshot_at)
    transactions, products = validate_snapshot_inputs(transactions, products)
    tx = transactions.loc[transactions["transaction_timestamp"] <= cutoff].copy()
    if tx.empty:
        raise ValueError("No transactions exist on or before snapshot_at")
    household = household_eligibility_table(
        transactions,
        snapshot_at=cutoff,
        min_observed_history_days=min_observed_history_days,
        min_baskets=min_baskets,
        min_active_span_days=min_active_span_days,
    )
    cutoff_day = cutoff.normalize()

    history_ok = household["observed_history_days"] >= min_observed_history_days
    baskets_ok = household["basket_frequency"] >= min_baskets
    span_ok = household["active_span_days"] >= min_active_span_days
    eligible = history_ok & baskets_ok & span_ok
    audit = EligibilityAudit(
        observed_households=len(household),
        excluded_insufficient_history=int((~history_ok).sum()),
        excluded_insufficient_baskets=int((history_ok & ~baskets_ok).sum()),
        excluded_insufficient_active_span=int(
            (history_ok & baskets_ok & ~span_ok).sum()
        ),
        eligible_households=int(eligible.sum()),
    )
    eligible_ids = household.index[eligible]
    tx = tx.loc[tx["household_id"].isin(eligible_ids)].copy()

    product_lookup = products[["product_id", "department", "brand"]].drop_duplicates(
        "product_id"
    )
    tx = tx.merge(product_lookup, on="product_id", how="left", validate="many_to_one")
    tx["department"] = tx["department"].fillna("UNKNOWN")
    tx["brand"] = tx["brand"].astype(object).fillna("UNKNOWN")
    discount_cols = ["retail_disc", "coupon_disc", "coupon_match_disc"]
    tx["discount_value"] = tx[discount_cols].fillna(0).sum(axis=1).clip(lower=0)
    tx["coupon_value"] = (
        tx[["coupon_disc", "coupon_match_disc"]].fillna(0).sum(axis=1).clip(lower=0)
    )
    tx["gross_value"] = tx["sales_value"] + tx["discount_value"]
    tx["private_sales"] = np.where(tx["brand"].eq("Private"), tx["sales_value"], 0.0)

    basket = tx.groupby(["household_id", "basket_id"], observed=True).agg(
        basket_timestamp=("transaction_timestamp", "min"),
        basket_sales=("sales_value", "sum"),
        basket_discount=("discount_value", "sum"),
        basket_coupon=("coupon_value", "sum"),
        store_id=("store_id", "first"),
    ).reset_index()
    basket["discounted"] = basket["basket_discount"] > 0
    basket["coupon_used"] = basket["basket_coupon"] > 0

    features = tx.groupby("household_id", observed=True).agg(
        monetary_value=("sales_value", "sum"),
        unique_products=("product_id", "nunique"),
        unique_departments=("department", "nunique"),
        total_discount=("discount_value", "sum"),
        gross_value=("gross_value", "sum"),
        private_sales=("private_sales", "sum"),
    )
    basket_features = basket.groupby("household_id", observed=True).agg(
        basket_frequency=("basket_id", "nunique"),
        avg_basket_value=("basket_sales", "mean"),
        active_days=("basket_timestamp", lambda s: s.dt.normalize().nunique()),
        discounted_basket_rate=("discounted", "mean"),
        coupon_basket_rate=("coupon_used", "mean"),
    )
    features = features.join(basket_features, how="inner")

    recency = basket.groupby("household_id", observed=True)["basket_timestamp"].max()
    features["recency_days"] = (
        cutoff_day - recency.dt.normalize()
    ).dt.days.astype(float)
    features["active_span_days"] = household.loc[features.index, "active_span_days"]

    def median_gap(group: pd.DataFrame) -> float:
        dates = group["basket_timestamp"].dt.normalize().drop_duplicates().sort_values()
        return float(dates.diff().dt.days.dropna().median())

    features["median_days_between_shops"] = basket.groupby(
        "household_id", observed=True, group_keys=False
    ).apply(median_gap, include_groups=False)

    department_sales = tx.groupby(
        ["household_id", "department"], observed=True
    )["sales_value"].sum()
    department_total = department_sales.groupby(level=0).transform("sum")
    department_share = department_sales.div(department_total.replace(0, np.nan))
    features["department_spend_hhi"] = department_share.pow(2).groupby(level=0).sum()
    features["discount_share_of_gross"] = features["total_discount"].div(
        features["gross_value"].replace(0, np.nan)
    )
    features["private_label_spend_share"] = features["private_sales"].div(
        features["monetary_value"].replace(0, np.nan)
    )

    store_baskets = basket.groupby(["household_id", "store_id"], observed=True).size()
    features["dominant_store_basket_share"] = store_baskets.groupby(level=0).max().div(
        features["basket_frequency"]
    )

    ordered = [
        "recency_days",
        "basket_frequency",
        "monetary_value",
        "avg_basket_value",
        "active_days",
        "active_span_days",
        "median_days_between_shops",
        "unique_products",
        "unique_departments",
        "department_spend_hhi",
        "discount_share_of_gross",
        "discounted_basket_rate",
        "coupon_basket_rate",
        "private_label_spend_share",
        "dominant_store_basket_share",
    ]
    features = features[ordered].sort_index()
    features.index.name = "household_id"
    return SnapshotResult(features=features, eligibility=audit)
