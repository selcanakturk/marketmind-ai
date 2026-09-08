"""Leakage-sensitive feature helpers for origin-based forecasting."""

from __future__ import annotations

import numpy as np


LAGS = (1, 7, 14, 28, 56)
ROLLING_WINDOWS = (7, 28, 56)


def historical_features(values: np.ndarray, origin: int) -> dict[str, np.ndarray]:
    """Create per-series features using observations no later than ``origin``.

    ``origin`` is a one-based M5 day number. ``lag_1`` is the value on the
    origin day, ``lag_7`` is six days earlier, and rolling windows include the
    origin day. This convention makes every feature available at issuance.
    """
    array = np.asarray(values, dtype=float)
    if array.ndim != 2:
        raise ValueError("values must have shape (series, time)")
    if origin < max(LAGS) or origin > array.shape[1]:
        raise ValueError("origin must provide all lags and lie inside values")
    result = {f"lag_{lag}": array[:, origin - lag] for lag in LAGS}
    for window in ROLLING_WINDOWS:
        history = array[:, origin - window : origin]
        result[f"rolling_mean_{window}"] = history.mean(axis=1)
        result[f"rolling_std_{window}"] = history.std(axis=1, ddof=0)
    return result
