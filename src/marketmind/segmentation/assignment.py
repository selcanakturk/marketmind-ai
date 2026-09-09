"""Non-serving assignment contract helpers for the frozen segmentation design."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import RobustScaler

from marketmind.segmentation.alignment import SegmentDefinition
from marketmind.segmentation.preprocessing import apply_preprocessor


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
    semantic_mapping: dict[int, SegmentDefinition],
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
    return pd.DataFrame(
        {
            "household_id": features.index,
            "snapshot_date": pd.Timestamp(snapshot_date),
            "cluster_id": labels,
            "segment_code": [semantic_mapping[int(x)].segment_code for x in labels],
            "segment_name": [semantic_mapping[int(x)].display_name for x in labels],
            "distance_to_centroid": distances,
        }
    ).reset_index(drop=True)
