"""Customer segmentation functionality."""
"""Leakage-safe customer segmentation feature utilities."""

from marketmind.segmentation.snapshot import (
    EligibilityAudit,
    SnapshotResult,
    build_household_snapshot,
)
from marketmind.segmentation.preprocessing import FINAL_FEATURES, prepare_features
from marketmind.segmentation.assignment import (
    assign_eligible_households,
    assign_from_transactions,
)
from marketmind.segmentation.bundle import SegmentationModelBundle, load_bundle

__all__ = [
    "EligibilityAudit",
    "FINAL_FEATURES",
    "SnapshotResult",
    "SegmentationModelBundle",
    "build_household_snapshot",
    "assign_eligible_households",
    "assign_from_transactions",
    "load_bundle",
    "prepare_features",
]
