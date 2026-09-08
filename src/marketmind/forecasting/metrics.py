"""Leakage-safe evaluation metrics for time-series forecasts."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike


def _paired(actual: ArrayLike, forecast: ArrayLike) -> tuple[np.ndarray, np.ndarray]:
    """Return finite, equally shaped one-dimensional metric inputs."""
    actual_array = np.asarray(actual, dtype=float)
    forecast_array = np.asarray(forecast, dtype=float)
    if actual_array.shape != forecast_array.shape:
        raise ValueError("actual and forecast must have identical shapes")
    if actual_array.size == 0:
        raise ValueError("actual and forecast must not be empty")
    if not (np.isfinite(actual_array).all() and np.isfinite(forecast_array).all()):
        raise ValueError("actual and forecast must contain only finite values")
    return actual_array.ravel(), forecast_array.ravel()


def mae(actual: ArrayLike, forecast: ArrayLike) -> float:
    """Return mean absolute error in target units."""
    actual_array, forecast_array = _paired(actual, forecast)
    return float(np.mean(np.abs(actual_array - forecast_array)))


def wape(actual: ArrayLike, forecast: ArrayLike) -> float:
    """Return WAPE, or NaN when total actual demand is not positive."""
    actual_array, forecast_array = _paired(actual, forecast)
    denominator = float(np.sum(actual_array))
    if denominator <= 0:
        return float("nan")
    return float(np.sum(np.abs(actual_array - forecast_array)) / denominator)


def forecast_bias(actual: ArrayLike, forecast: ArrayLike) -> float:
    """Return signed relative bias; positive means overforecasting.

    The result is NaN when total actual demand is not positive.
    """
    actual_array, forecast_array = _paired(actual, forecast)
    denominator = float(np.sum(actual_array))
    if denominator <= 0:
        return float("nan")
    return float(np.sum(forecast_array - actual_array) / denominator)


def rmsse(actual: ArrayLike, forecast: ArrayLike, training: ArrayLike) -> float:
    """Return RMSSE using one-step changes from this fold's training data.

    A NaN result explicitly represents an undefined scale: fewer than two
    training observations, a non-positive scale, or a non-finite scale.
    """
    actual_array, forecast_array = _paired(actual, forecast)
    training_array = np.asarray(training, dtype=float).ravel()
    if training_array.size < 2 or not np.isfinite(training_array).all():
        return float("nan")
    scale = float(np.mean(np.diff(training_array) ** 2))
    if not np.isfinite(scale) or scale <= 0:
        return float("nan")
    mean_squared_error = float(np.mean((actual_array - forecast_array) ** 2))
    return float(np.sqrt(mean_squared_error / scale))
