"""Deterministic cluster identity alignment and semantic naming helpers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

from marketmind.segmentation.preprocessing import FINAL_FEATURES


@dataclass(frozen=True)
class SegmentDefinition:
    """Stable semantic contract independent of a model's raw integer label."""

    segment_code: str
    display_name: str
    description: str


SEGMENT_DEFINITIONS = {
    "HIGH_ENGAGEMENT_BROAD": SegmentDefinition(
        "HIGH_ENGAGEMENT_BROAD",
        "High-Engagement Broad Shoppers",
        "Recent, frequent, high-spend households purchasing across a broad assortment.",
    ),
    "PROMOTION_BASKET_BUILDERS": SegmentDefinition(
        "PROMOTION_BASKET_BUILDERS",
        "Promotion-Oriented Basket Builders",
        "Moderate-frequency households with larger baskets and stronger observed discount/coupon use.",
    ),
    "LOWER_ENGAGEMENT_FOCUSED": SegmentDefinition(
        "LOWER_ENGAGEMENT_FOCUSED",
        "Lower-Engagement Focused Shoppers",
        "Less-recent, lower-frequency and lower-spend households with narrower assortments.",
    ),
}


def relative_profile_signatures(
    features: pd.DataFrame,
    labels: np.ndarray,
    *,
    columns: tuple[str, ...] = FINAL_FEATURES,
) -> pd.DataFrame:
    """Return cluster medians relative to the snapshot population median/IQR.

    Snapshot-relative signatures make independently scaled cumulative snapshots
    comparable without reusing a future snapshot's scaler during model fitting.
    """

    if len(features) != len(labels):
        raise ValueError("features and labels must have equal row counts")
    selected = features.loc[:, columns].astype(float)
    iqr = selected.quantile(0.75) - selected.quantile(0.25)
    if (iqr <= 0).any():
        raise ValueError("Profile signature columns must have positive IQR")
    grouped = selected.assign(_cluster=np.asarray(labels)).groupby("_cluster").median()
    return grouped.subtract(selected.median()).divide(iqr)


def align_to_reference(
    candidate_signatures: pd.DataFrame, reference_signatures: pd.DataFrame
) -> tuple[dict[int, int], pd.DataFrame]:
    """Optimally map candidate raw IDs to reference IDs using Euclidean distance."""

    if set(candidate_signatures.columns) != set(reference_signatures.columns):
        raise ValueError("Candidate and reference signatures need identical features")
    candidate = candidate_signatures.loc[:, reference_signatures.columns]
    if candidate.shape != reference_signatures.shape:
        raise ValueError("Cluster alignment requires the same number of clusters")
    distances = np.linalg.norm(
        candidate.to_numpy()[:, None, :] - reference_signatures.to_numpy()[None, :, :],
        axis=2,
    )
    rows, cols = linear_sum_assignment(distances)
    mapping = {
        int(candidate.index[row]): int(reference_signatures.index[col])
        for row, col in zip(rows, cols)
    }
    matrix = pd.DataFrame(
        distances,
        index=candidate.index.rename("candidate_cluster"),
        columns=reference_signatures.index.rename("reference_cluster"),
    )
    return mapping, matrix


def remap_labels(labels: np.ndarray, mapping: dict[int, int]) -> np.ndarray:
    """Apply a complete raw-label mapping."""

    observed = set(np.unique(labels).astype(int))
    if observed != set(mapping):
        raise ValueError("Mapping keys must exactly cover observed labels")
    return np.array([mapping[int(label)] for label in labels], dtype=int)


def semantic_mapping_from_profiles(
    profiles: pd.DataFrame,
) -> dict[int, SegmentDefinition]:
    """Derive semantic identities from behavior, never raw-label position.

    The most frequent profile is the high-engagement/broad segment. Of the two
    remaining profiles, the one with greatest coupon use is promotion-oriented;
    the final profile is lower-engagement/focused. Unique maxima are required.
    """

    required = {"basket_frequency", "coupon_basket_rate"}
    missing = required.difference(profiles.columns)
    if missing or len(profiles) != 3:
        raise ValueError("Expected three profiles with frequency and coupon rate")
    most_frequent = profiles["basket_frequency"].idxmax()
    if (profiles["basket_frequency"] == profiles.loc[most_frequent, "basket_frequency"]).sum() != 1:
        raise ValueError("Semantic mapping requires a unique frequency maximum")
    remaining = profiles.index.difference([most_frequent])
    promotion = profiles.loc[remaining, "coupon_basket_rate"].idxmax()
    if (
        profiles.loc[remaining, "coupon_basket_rate"]
        == profiles.loc[promotion, "coupon_basket_rate"]
    ).sum() != 1:
        raise ValueError("Semantic mapping requires a unique coupon-rate maximum")
    lower = remaining.difference([promotion])[0]
    return {
        int(most_frequent): SEGMENT_DEFINITIONS["HIGH_ENGAGEMENT_BROAD"],
        int(promotion): SEGMENT_DEFINITIONS["PROMOTION_BASKET_BUILDERS"],
        int(lower): SEGMENT_DEFINITIONS["LOWER_ENGAGEMENT_FOCUSED"],
    }
