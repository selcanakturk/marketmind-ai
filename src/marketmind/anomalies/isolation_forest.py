"""Controlled, temporally safe Isolation Forest challenger primitives."""

from __future__ import annotations

import io
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

FEATURE_COLUMNS = (
    "robust_residual_score", "residual", "absolute_residual", "expected_sales",
    "day_of_week_sin", "day_of_week_cos", "event_present", "snap",
)
CONFIGURATIONS = {
    "IF-1": {"n_estimators": 200, "max_samples": "auto", "contamination": "auto", "max_features": 1.0, "bootstrap": False, "random_state": 42, "n_jobs": 1},
    "IF-2": {"n_estimators": 300, "max_samples": 512, "contamination": "auto", "max_features": 1.0, "bootstrap": False, "random_state": 42, "n_jobs": 1},
    "IF-3": {"n_estimators": 300, "max_samples": 1024, "contamination": "auto", "max_features": 1.0, "bootstrap": False, "random_state": 42, "n_jobs": 1},
}


def add_calendar_context(frame: pd.DataFrame, calendar: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["date"] = pd.to_datetime(result["date"])
    context = calendar.copy()
    context["date"] = pd.to_datetime(context["date"])
    keep = ["date", "event_name_1", "snap_CA", "snap_TX", "snap_WI"]
    result = result.merge(context[keep], on="date", how="left", validate="many_to_one")
    result["event_present"] = result.event_name_1.notna().astype(np.int8)
    result["snap"] = np.fromiter(
        (getattr(row, f"snap_{row.state_id}") for row in result.itertuples()), dtype=np.int8, count=len(result)
    )
    return result


def _training_robust_score(frame: pd.DataFrame) -> pd.Series:
    """Normalize from the complete prior-only training corpus."""
    grouped = frame.groupby(["store_id", "dept_id"])["residual"]
    center = grouped.transform("median")
    mad = grouped.transform(lambda value: np.median(np.abs(value - np.median(value))))
    scale = 1.4826 * mad
    return (frame.residual - center) / scale.replace(0, np.nan)


def build_features(frame: pd.DataFrame, calendar: pd.DataFrame, *, training_corpus: bool = False) -> pd.DataFrame:
    contextual = add_calendar_context(frame, calendar)
    robust = _training_robust_score(contextual) if training_corpus else contextual["anomaly_score"]
    robust = robust.fillna(0.0)  # neutral finite representation for rare undefined baseline rows
    day = contextual.date.dt.dayofweek.to_numpy(float)
    features = pd.DataFrame({
        "robust_residual_score": robust.to_numpy(float),
        "residual": contextual.residual.to_numpy(float),
        "absolute_residual": contextual.residual.abs().to_numpy(float),
        "expected_sales": contextual.expected_sales.to_numpy(float),
        "day_of_week_sin": np.sin(2 * np.pi * day / 7),
        "day_of_week_cos": np.cos(2 * np.pi * day / 7),
        "event_present": contextual.event_present.to_numpy(float),
        "snap": contextual.snap.to_numpy(float),
    }, index=frame.index)
    if tuple(features.columns) != FEATURE_COLUMNS or not np.isfinite(features.to_numpy()).all():
        raise ValueError("Isolation Forest features must be finite and exactly ordered")
    return features


def fit_isolation_forest(features: pd.DataFrame, config_name: str):
    if config_name not in CONFIGURATIONS:
        raise ValueError("unknown predeclared Isolation Forest configuration")
    started = time.perf_counter()
    model = IsolationForest(**CONFIGURATIONS[config_name]).fit(features.loc[:, FEATURE_COLUMNS])
    runtime = time.perf_counter() - started
    buffer = io.BytesIO(); joblib.dump(model, buffer)
    return model, runtime, len(buffer.getvalue())


def anomaly_score(model: IsolationForest, features: pd.DataFrame) -> np.ndarray:
    """Invert sklearn score_samples so larger values mean more anomalous."""
    score = -model.score_samples(features.loc[:, FEATURE_COLUMNS])
    if not np.isfinite(score).all():
        raise ValueError("Isolation Forest returned non-finite scores")
    return score
