"""Customer segmentation functionality."""
"""Leakage-safe customer segmentation feature utilities."""

from marketmind.segmentation.snapshot import (
    EligibilityAudit,
    SnapshotResult,
    build_household_snapshot,
)
from marketmind.segmentation.preprocessing import FINAL_FEATURES, prepare_features
from marketmind.segmentation.assignment import assign_eligible_households

__all__ = [
    "EligibilityAudit",
    "FINAL_FEATURES",
    "SnapshotResult",
    "build_household_snapshot",
    "assign_eligible_households",
    "prepare_features",
]
