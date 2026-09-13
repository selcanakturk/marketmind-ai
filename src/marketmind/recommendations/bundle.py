"""Compact, validated production bundle for the frozen Item-CF engine."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from marketmind.recommendations.config import MODEL_VERSION, NEIGHBOR_COUNT, SCHEMA_VERSION


@dataclass
class RecommendationBundle:
    item_ids: np.ndarray
    neighbor_indptr: np.ndarray
    neighbor_indices: np.ndarray
    neighbor_similarities: np.ndarray
    popularity_item_ids: np.ndarray
    popularity_counts: np.ndarray
    item_first_seen_ms: np.ndarray
    training_cutoff_ms: int
    model_version: str
    schema_version: str
    configuration: dict[str, Any]
    training_statistics: dict[str, Any]
    library_versions: dict[str, str]
    research_metrics: dict[str, Any]
    lockbox_status: str

    @cached_property
    def item_to_index(self) -> dict[int, int]:
        return {int(item): index for index, item in enumerate(self.item_ids)}

    def validate(self) -> None:
        n_items = len(self.item_ids)
        if self.model_version != MODEL_VERSION or self.schema_version != SCHEMA_VERSION:
            raise ValueError("bundle version does not match the production contract")
        if self.configuration.get("neighbors") != NEIGHBOR_COUNT:
            raise ValueError("bundle does not use the frozen neighborhood")
        if n_items == 0 or len(np.unique(self.item_ids)) != n_items or np.any(np.diff(self.item_ids) <= 0):
            raise ValueError("item mapping must be nonempty, unique, and ascending")
        if len(self.item_first_seen_ms) != n_items:
            raise ValueError("first-seen metadata is not aligned with item IDs")
        if len(self.neighbor_indptr) != n_items + 1 or self.neighbor_indptr[0] != 0:
            raise ValueError("invalid sparse neighbor row pointers")
        if self.neighbor_indptr[-1] != len(self.neighbor_indices) or len(self.neighbor_indices) != len(self.neighbor_similarities):
            raise ValueError("invalid sparse neighbor graph")
        if np.any(np.diff(self.neighbor_indptr) < 0) or np.any(np.diff(self.neighbor_indptr) > NEIGHBOR_COUNT):
            raise ValueError("neighbor rows must contain at most 50 entries")
        if len(self.neighbor_indices) and (self.neighbor_indices.min() < 0 or self.neighbor_indices.max() >= n_items):
            raise ValueError("neighbor index is outside the item mapping")
        if not np.isfinite(self.neighbor_similarities).all() or np.any(self.neighbor_similarities <= 0):
            raise ValueError("neighbor similarities must be finite and positive")
        for row in range(n_items):
            values = self.neighbor_indices[self.neighbor_indptr[row]:self.neighbor_indptr[row + 1]]
            if len(values) != len(np.unique(values)):
                raise ValueError("duplicate neighbor in sparse graph")
        if len(self.popularity_item_ids) != n_items or set(self.popularity_item_ids) != set(self.item_ids):
            raise ValueError("popularity state must cover the trained catalog")
        if len(self.popularity_counts) != n_items or np.any(self.popularity_counts <= 0):
            raise ValueError("popularity counts must be positive and aligned")
        if not isinstance(self.training_cutoff_ms, (int, np.integer)):
            raise ValueError("training cutoff must be epoch milliseconds")


def save_bundle(bundle: RecommendationBundle, path: str | Path) -> None:
    bundle.validate()
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, destination, compress=3)


def load_bundle(path: str | Path) -> RecommendationBundle:
    bundle = joblib.load(Path(path))
    if not isinstance(bundle, RecommendationBundle):
        raise TypeError("artifact is not a RecommendationBundle")
    bundle.validate()
    return bundle
