"""Serializable forecasting bundle and persistence helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib


@dataclass
class ForecastModelBundle:
    """All fitted state and schema information required for inference."""

    estimator: Any
    categorical_encoder: Any
    feature_columns: tuple[str, ...]
    categorical_features: tuple[str, ...]
    numeric_features: tuple[str, ...]
    model_params: dict[str, Any]
    feature_schema: dict[str, str]
    training_cutoff: int
    forecast_horizon: int
    required_history: int
    series_metadata: list[dict[str, str]]
    model_version: str
    schema_version: str
    postprocessing: str


def save_bundle(bundle: ForecastModelBundle, path: str | Path) -> None:
    """Serialize a model bundle with compression."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, destination, compress=3)


def load_bundle(path: str | Path) -> ForecastModelBundle:
    """Load and minimally validate a serialized model bundle."""
    bundle = joblib.load(Path(path))
    if not isinstance(bundle, ForecastModelBundle):
        raise TypeError("artifact is not a ForecastModelBundle")
    return bundle
