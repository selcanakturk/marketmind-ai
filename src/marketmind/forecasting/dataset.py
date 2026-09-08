"""Construction of direct, horizon-conditioned forecasting tables."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd

from .features import historical_features
from .config import (
    CATEGORICAL_FEATURES,
    FORECAST_HORIZON,
    IDENTITY_COLUMNS as CONFIG_IDENTITY_COLUMNS,
    NUMERIC_FEATURES,
)


IDENTITY_COLUMNS = list(CONFIG_IDENTITY_COLUMNS)
CATEGORICAL_COLUMNS = list(CATEGORICAL_FEATURES)
NUMERIC_COLUMNS = list(NUMERIC_FEATURES)


def weekly_training_origins(train_end: int, minimum_origin: int = 56) -> np.ndarray:
    """Return weekly origins aligned backward from ``train_end - 28``."""
    last_origin = train_end - 28
    if last_origin < minimum_origin:
        raise ValueError("training period is too short for a 28-day target")
    return np.arange(last_origin, minimum_origin - 1, -7, dtype=np.int16)[::-1]


def prepare_calendar(calendar: pd.DataFrame) -> pd.DataFrame:
    """Return calendar fields indexed by one-based M5 day number."""
    required = {"d", "date", "event_name_1", "event_type_1", "snap_CA", "snap_TX", "snap_WI"}
    missing = required.difference(calendar.columns)
    if missing:
        raise ValueError(f"calendar is missing columns: {sorted(missing)}")
    result = calendar.copy()
    result["day_index"] = result["d"].str.removeprefix("d_").astype(int)
    result["date"] = pd.to_datetime(result["date"])
    return result.set_index("day_index", drop=False)


def _origin_frame(
    series: pd.DataFrame,
    values: np.ndarray,
    calendar: pd.DataFrame,
    origin: int,
    include_target: bool,
) -> tuple[pd.DataFrame, np.ndarray | None]:
    """Build all series × 28 horizons for one issuance origin."""
    if origin + 28 > values.shape[1] and include_target:
        raise ValueError("target horizon extends beyond supplied sales values")
    hist = historical_features(values, origin)
    n_series, horizon = len(series), FORECAST_HORIZON
    target_days = np.tile(np.arange(origin + 1, origin + horizon + 1), n_series)
    target_calendar = calendar.loc[target_days]
    state = np.repeat(series["state_id"].to_numpy(), horizon)
    snap = np.fromiter(
        (calendar.at[day, f"snap_{st}"] for st, day in zip(state, target_days, strict=True)),
        dtype=np.int8,
        count=n_series * horizon,
    )
    data: dict[str, np.ndarray] = {
        col: np.repeat(series[col].to_numpy(), horizon) for col in IDENTITY_COLUMNS
    }
    data["event_name"] = target_calendar["event_name_1"].fillna("none").to_numpy()
    data["event_type"] = target_calendar["event_type_1"].fillna("none").to_numpy()
    data["forecast_horizon"] = np.tile(np.arange(1, horizon + 1, dtype=np.int8), n_series)
    for name, feature in hist.items():
        data[name] = np.repeat(feature.astype(np.float32), horizon)
    dates = target_calendar["date"]
    data.update({
        "day_of_week": dates.dt.dayofweek.to_numpy(dtype=np.int8),
        "day_of_month": dates.dt.day.to_numpy(dtype=np.int8),
        "month": dates.dt.month.to_numpy(dtype=np.int8),
        "year": dates.dt.year.to_numpy(dtype=np.int16),
        "day_index": target_days.astype(np.int16),
        "snap": snap,
    })
    features = pd.DataFrame(data)[CATEGORICAL_COLUMNS + NUMERIC_COLUMNS]
    target = None
    if include_target:
        target = np.concatenate([values[i, origin : origin + horizon] for i in range(n_series)]).astype(np.float32)
    return features, target


def build_training_table(
    series: pd.DataFrame,
    values: np.ndarray,
    calendar: pd.DataFrame,
    origins: Iterable[int],
) -> tuple[pd.DataFrame, np.ndarray]:
    """Build a compact direct training table from predeclared origins."""
    feature_blocks, target_blocks = [], []
    for origin in origins:
        features, target = _origin_frame(series, values, calendar, int(origin), True)
        feature_blocks.append(features)
        target_blocks.append(target)
    return pd.concat(feature_blocks, ignore_index=True), np.concatenate(target_blocks)


def build_prediction_table(
    series: pd.DataFrame,
    training_values: np.ndarray,
    calendar: pd.DataFrame,
    origin: int,
    target_start_day: int | None = None,
) -> pd.DataFrame:
    """Build the 70 × 28 issuance table without accessing future targets."""
    if target_start_day is None or target_start_day == origin + 1:
        features, _ = _origin_frame(series, training_values, calendar, origin, False)
        return features
    # Production inputs may provide only the required recent history while M5
    # day identifiers continue from a later absolute day number.
    shifted = calendar.copy()
    offset = target_start_day - (origin + 1)
    shifted.index = shifted.index - offset
    shifted["day_index"] = shifted["day_index"] - offset
    features, _ = _origin_frame(series, training_values, shifted, origin, False)
    features["day_index"] = features["day_index"] + offset
    return features


def _one_step_frame(
    series: pd.DataFrame,
    values: np.ndarray,
    calendar: pd.DataFrame,
    origin: int,
    include_target: bool,
) -> tuple[pd.DataFrame, np.ndarray | None]:
    """Build one row per series for target day ``origin + 1``."""
    if include_target and origin + 1 > values.shape[1]:
        raise ValueError("one-step target extends beyond supplied sales values")
    hist = historical_features(values, origin)
    target_day = origin + 1
    target_calendar = calendar.loc[target_day]
    data: dict[str, np.ndarray] = {col: series[col].to_numpy() for col in IDENTITY_COLUMNS}
    data["event_name"] = np.repeat(target_calendar["event_name_1"] if pd.notna(target_calendar["event_name_1"]) else "none", len(series))
    data["event_type"] = np.repeat(target_calendar["event_type_1"] if pd.notna(target_calendar["event_type_1"]) else "none", len(series))
    for name, feature in hist.items():
        data[name] = feature.astype(np.float32)
    date = target_calendar["date"]
    data.update({
        "day_of_week": np.repeat(date.dayofweek, len(series)).astype(np.int8),
        "day_of_month": np.repeat(date.day, len(series)).astype(np.int8),
        "month": np.repeat(date.month, len(series)).astype(np.int8),
        "year": np.repeat(date.year, len(series)).astype(np.int16),
        "day_index": np.repeat(target_day, len(series)).astype(np.int16),
        "snap": np.fromiter(
            (calendar.at[target_day, f"snap_{state}"] for state in series["state_id"]),
            dtype=np.int8,
            count=len(series),
        ),
    })
    numeric = [column for column in NUMERIC_COLUMNS if column != "forecast_horizon"]
    features = pd.DataFrame(data)[CATEGORICAL_COLUMNS + numeric]
    target = values[:, origin].astype(np.float32) if include_target else None
    return features, target


def build_one_step_training_table(
    series: pd.DataFrame,
    values: np.ndarray,
    calendar: pd.DataFrame,
    origins: Iterable[int],
) -> tuple[pd.DataFrame, np.ndarray]:
    """Build daily one-step rows with every label inside supplied history."""
    feature_blocks, target_blocks = [], []
    for origin in origins:
        features, target = _one_step_frame(series, values, calendar, int(origin), True)
        feature_blocks.append(features)
        target_blocks.append(target)
    return pd.concat(feature_blocks, ignore_index=True), np.concatenate(target_blocks)


def build_one_step_prediction_table(
    series: pd.DataFrame,
    history: np.ndarray,
    calendar: pd.DataFrame,
    origin: int,
) -> pd.DataFrame:
    """Build one-step features from observed-plus-predicted history."""
    features, _ = _one_step_frame(series, history, calendar, origin, False)
    return features
