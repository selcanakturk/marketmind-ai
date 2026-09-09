"""Serializable frozen segmentation bundle and persistence helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib

from marketmind.segmentation.config import (
    FEATURE_ORDER,
    KMEANS_PARAMETERS,
    LOG_FEATURES,
    SEGMENT_CODES,
    UNCHANGED_FEATURES,
)


@dataclass
class SegmentationModelBundle:
    """All fitted state, schema, and semantics required for assignment."""

    scaler: Any
    estimator: Any
    feature_order: tuple[str, ...]
    log_features: tuple[str, ...]
    unchanged_features: tuple[str, ...]
    eligibility_policy: dict[str, int]
    semantic_mapping: dict[int, dict[str, str]]
    model_version: str
    schema_version: str
    reference_snapshot: str
    kmeans_parameters: dict[str, Any]
    centroid_profiles: list[dict[str, Any]]
    library_versions: dict[str, str]


def save_bundle(bundle: SegmentationModelBundle, path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, destination, compress=3)


def load_bundle(path: str | Path) -> SegmentationModelBundle:
    bundle = joblib.load(Path(path))
    if not isinstance(bundle, SegmentationModelBundle):
        raise TypeError("artifact is not a SegmentationModelBundle")
    if len(bundle.semantic_mapping) != 3 or bundle.estimator.n_clusters != 3:
        raise ValueError("segmentation bundle must contain three mapped clusters")
    if bundle.feature_order != FEATURE_ORDER:
        raise ValueError("bundle feature order does not match the frozen schema")
    if bundle.log_features != LOG_FEATURES or bundle.unchanged_features != UNCHANGED_FEATURES:
        raise ValueError("bundle transformation policy does not match the frozen schema")
    if bundle.kmeans_parameters != KMEANS_PARAMETERS:
        raise ValueError("bundle KMeans parameters do not match frozen configuration")
    codes = {item["segment_code"] for item in bundle.semantic_mapping.values()}
    if codes != set(SEGMENT_CODES):
        raise ValueError("bundle semantic mapping is incomplete or unexpected")
    return bundle
