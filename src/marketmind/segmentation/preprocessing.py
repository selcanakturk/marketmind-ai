"""Frozen preprocessing contract for Phase 2 clustering experiments."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler


FINAL_FEATURES: tuple[str, ...] = (
    "recency_days",
    "basket_frequency",
    "monetary_value",
    "avg_basket_value",
    "unique_departments",
    "department_spend_hhi",
    "discount_share_of_gross",
    "coupon_basket_rate",
    "private_label_spend_share",
)

LOG1P_FEATURES: tuple[str, ...] = (
    "recency_days",
    "basket_frequency",
    "monetary_value",
    "avg_basket_value",
)

BOUNDED_RATIO_FEATURES: tuple[str, ...] = (
    "department_spend_hhi",
    "discount_share_of_gross",
    "coupon_basket_rate",
    "private_label_spend_share",
)


@dataclass(frozen=True)
class PreparedFeatures:
    """Transformed/scaled values plus the fitted experiment-only scaler."""

    transformed: pd.DataFrame
    scaled: pd.DataFrame
    scaler: RobustScaler


def transform_features(features: pd.DataFrame) -> pd.DataFrame:
    """Select deterministic columns and apply the frozen `log1p` policy."""

    missing = set(FINAL_FEATURES).difference(features.columns)
    if missing:
        raise ValueError(f"Missing final clustering features: {sorted(missing)}")
    selected = features.loc[:, FINAL_FEATURES].astype(float).copy()
    if selected.isna().any().any():
        raise ValueError("Clustering features must not contain missing values")
    if (selected.loc[:, LOG1P_FEATURES] < 0).any().any():
        raise ValueError("log1p features must be nonnegative")
    for column in LOG1P_FEATURES:
        selected[column] = np.log1p(selected[column])
    for column in BOUNDED_RATIO_FEATURES:
        if not selected[column].between(0, 1, inclusive="both").all():
            raise ValueError(f"Bounded ratio feature outside [0, 1]: {column}")
    return selected


def prepare_features(features: pd.DataFrame) -> PreparedFeatures:
    """Fit the frozen RobustScaler on the supplied snapshot only."""

    transformed = transform_features(features)
    scaler = RobustScaler()
    scaled_values = scaler.fit_transform(transformed)
    scaled = pd.DataFrame(
        scaled_values, index=transformed.index, columns=transformed.columns
    )
    return PreparedFeatures(transformed=transformed, scaled=scaled, scaler=scaler)


def apply_preprocessor(features: pd.DataFrame, scaler: RobustScaler) -> pd.DataFrame:
    """Transform another point-in-time frame with an already-fitted scaler."""

    transformed = transform_features(features)
    return pd.DataFrame(
        scaler.transform(transformed),
        index=transformed.index,
        columns=transformed.columns,
    )
