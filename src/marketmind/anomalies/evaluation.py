"""Model-free anomaly semantics and engineered-test helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd

OUTPUT_COLUMNS = (
    "date", "store_id", "dept_id", "actual_sales", "expected_sales",
    "residual", "anomaly_score", "direction", "is_alert", "severity_rank",
)


def signed_residual(actual_sales, expected_sales):
    """Positive means an unusual-spike direction; negative means drop."""
    actual = np.asarray(actual_sales, dtype=float)
    expected = np.asarray(expected_sales, dtype=float)
    if actual.shape != expected.shape or not np.isfinite(actual).all() or not np.isfinite(expected).all():
        raise ValueError("actual and expected sales must be aligned and finite")
    return actual - expected


def robust_residual_score(residual, historical_residuals):
    """Standardize residuals from an earlier OOS archive only.

    The caller owns temporal separation. A zero/non-finite historical MAD
    produces NaN rather than an invented scale or alert.
    """
    residual = np.asarray(residual, dtype=float)
    history = np.asarray(historical_residuals, dtype=float)
    history = history[np.isfinite(history)]
    if not len(history):
        return np.full(residual.shape, np.nan)
    center = np.median(history)
    scale = 1.4826 * np.median(np.abs(history - center))
    if not np.isfinite(scale) or scale <= 0:
        return np.full(residual.shape, np.nan)
    return (residual - center) / scale


def trailing_median(values, window: int = 28) -> np.ndarray:
    """Past-only rolling expectation; the current observation is excluded."""
    if window <= 0:
        raise ValueError("window must be positive")
    series = pd.Series(np.asarray(values, dtype=float))
    return series.shift(1).rolling(window, min_periods=window).median().to_numpy()


def inject_engineered_anomaly(values, positions, kind: str, magnitude: float) -> np.ndarray:
    """Create deterministic ENGINEERED TEST CASES without negative sales."""
    if kind not in {"positive_spike", "negative_drop", "sustained_spike", "sustained_drop"}:
        raise ValueError("unsupported engineered perturbation")
    if not np.isfinite(magnitude) or magnitude <= 0:
        raise ValueError("magnitude must be finite and positive")
    result = np.asarray(values, dtype=float).copy()
    indexes = np.asarray(tuple(positions), dtype=int)
    if len(indexes) == 0 or (indexes < 0).any() or (indexes >= len(result)).any():
        raise ValueError("positions must identify observations")
    sign = 1 if "spike" in kind else -1
    result[indexes] = np.maximum(0.0, result[indexes] + sign * magnitude)
    return result


def validate_output(frame: pd.DataFrame) -> None:
    missing = set(OUTPUT_COLUMNS).difference(frame.columns)
    if missing:
        raise ValueError(f"anomaly output missing columns: {sorted(missing)}")
    if not frame["direction"].isin(["high", "low", "normal"]).all():
        raise ValueError("direction must be high, low, or normal")
    if (frame[["actual_sales", "expected_sales"]] < 0).any().any():
        raise ValueError("sales fields must be nonnegative")
