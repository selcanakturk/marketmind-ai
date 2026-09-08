"""Small forecasting-strategy helpers."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np


def recursive_forecast(
    observed_history: np.ndarray,
    steps: int,
    predict_next: Callable[[np.ndarray, int], np.ndarray],
) -> np.ndarray:
    """Forecast recursively, appending predictions rather than future actuals.

    ``predict_next`` receives a copy of observed history plus prior predictions
    and the one-based horizon. It must return one prediction per series.
    """
    history = np.asarray(observed_history, dtype=float).copy()
    if history.ndim != 2 or steps <= 0:
        raise ValueError("history must be 2D and steps must be positive")
    forecasts = []
    for horizon in range(1, steps + 1):
        prediction = np.asarray(predict_next(history.copy(), horizon), dtype=float).reshape(-1)
        if prediction.shape != (history.shape[0],) or not np.isfinite(prediction).all():
            raise ValueError("predict_next must return one finite value per series")
        forecasts.append(prediction)
        history = np.column_stack([history, prediction])
    return np.column_stack(forecasts)
