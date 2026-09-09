"""Customer segmentation functionality."""
"""Leakage-safe customer segmentation feature utilities."""

from marketmind.segmentation.snapshot import (
    EligibilityAudit,
    SnapshotResult,
    build_household_snapshot,
)

__all__ = ["EligibilityAudit", "SnapshotResult", "build_household_snapshot"]
