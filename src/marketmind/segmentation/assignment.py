"""Non-serving assignment contract helpers for the frozen segmentation design."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import RobustScaler

from marketmind.segmentation.alignment import SegmentDefinition
from marketmind.segmentation.bundle import SegmentationModelBundle
from marketmind.segmentation.config import ASSIGNMENT_OUTPUT_COLUMNS
from marketmind.segmentation.preprocessing import apply_preprocessor
from marketmind.segmentation.snapshot import (
    build_household_snapshot,
    household_eligibility_table,
    validate_snapshot_inputs,
)


INSUFFICIENT_HISTORY = "insufficient_history"


def eligibility_status(
    *, observed_history_days: int, basket_count: int, active_span_days: int
) -> str:
    """Return eligibility without treating ineligible households as a segment."""

    eligible = (
        observed_history_days >= 90
        and basket_count >= 5
        and active_span_days >= 30
    )
    return "eligible" if eligible else INSUFFICIENT_HISTORY


def assign_eligible_households(
    features: pd.DataFrame,
    *,
    scaler: RobustScaler,
    model: KMeans,
    semantic_mapping: dict[int, SegmentDefinition | dict[str, str]],
    snapshot_date: str | pd.Timestamp,
) -> pd.DataFrame:
    """Assign eligible feature rows to nearest fitted KMeans centroids."""

    scaled = apply_preprocessor(features, scaler)
    labels = model.predict(scaled)
    if not set(np.unique(labels)).issubset(semantic_mapping):
        raise ValueError("Every predicted cluster requires a semantic mapping")
    distances = np.linalg.norm(
        scaled.to_numpy() - model.cluster_centers_[labels], axis=1
    )
    if not np.isfinite(distances).all() or (distances < 0).any():
        raise ValueError("Centroid distances must be finite and nonnegative")
    def value(label: int, field: str) -> str:
        definition = semantic_mapping[int(label)]
        if isinstance(definition, SegmentDefinition):
            return (
                definition.segment_code
                if field == "segment_code"
                else definition.display_name
            )
        return definition[field]

    result = pd.DataFrame(
        {
            "household_id": features.index,
            "snapshot_date": pd.Timestamp(snapshot_date),
            "eligibility_status": "eligible",
            "cluster_id": labels,
            "segment_code": [value(x, "segment_code") for x in labels],
            "segment_name": [value(x, "display_name") for x in labels],
            "distance_to_centroid": distances,
        }
    ).reset_index(drop=True)
    return result.loc[:, ASSIGNMENT_OUTPUT_COLUMNS]


def assign_from_transactions(
    bundle: SegmentationModelBundle,
    transactions: pd.DataFrame,
    products: pd.DataFrame,
    *,
    snapshot_date: str | pd.Timestamp,
) -> pd.DataFrame:
    """Build point-in-time features and assign all observed households.

    Households failing eligibility receive null assignment fields and are not
    forced into a learned segment.
    """

    tx, product = validate_snapshot_inputs(transactions, products)
    policy = bundle.eligibility_policy
    eligibility = household_eligibility_table(
        tx,
        snapshot_at=snapshot_date,
        min_observed_history_days=policy["min_observed_history_days"],
        min_baskets=policy["min_baskets"],
        min_active_span_days=policy["min_active_span_days"],
    )
    if not eligibility["eligible"].any():
        result = pd.DataFrame(
            {
                "household_id": eligibility.index,
                "snapshot_date": pd.Timestamp(snapshot_date),
                "eligibility_status": INSUFFICIENT_HISTORY,
                "cluster_id": pd.array([pd.NA] * len(eligibility), dtype="Int64"),
                "segment_code": pd.NA,
                "segment_name": pd.NA,
                "distance_to_centroid": np.nan,
            }
        )
        return result.loc[:, ASSIGNMENT_OUTPUT_COLUMNS]
    snapshot = build_household_snapshot(
        tx,
        product,
        snapshot_at=snapshot_date,
        min_observed_history_days=policy["min_observed_history_days"],
        min_baskets=policy["min_baskets"],
        min_active_span_days=policy["min_active_span_days"],
    )
    assigned = assign_eligible_households(
        snapshot.features,
        scaler=bundle.scaler,
        model=bundle.estimator,
        semantic_mapping=bundle.semantic_mapping,
        snapshot_date=snapshot_date,
    ).set_index("household_id")
    result = pd.DataFrame(index=eligibility.index)
    result.index.name = "household_id"
    result["snapshot_date"] = pd.Timestamp(snapshot_date)
    result["eligibility_status"] = np.where(
        eligibility["eligible"], "eligible", INSUFFICIENT_HISTORY
    )
    for column in ("cluster_id", "segment_code", "segment_name", "distance_to_centroid"):
        result[column] = assigned[column]
    result = result.reset_index()
    result["cluster_id"] = result["cluster_id"].astype("Int64")
    return result.loc[:, ASSIGNMENT_OUTPUT_COLUMNS]
