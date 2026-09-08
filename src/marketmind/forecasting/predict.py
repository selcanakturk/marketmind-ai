"""Validated inference for the frozen MarketMind forecasting bundle."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .bundle import ForecastModelBundle, load_bundle
from .config import FORECAST_HORIZON, OUTPUT_COLUMNS
from .dataset import build_prediction_table, prepare_calendar

HISTORY_COLUMNS = ("d", "date", "store_id", "dept_id", "state_id", "sales")
FUTURE_CALENDAR_COLUMNS = (
    "d", "date", "event_name", "event_type", "snap_CA", "snap_TX", "snap_WI",
)


def _require_columns(frame: pd.DataFrame, required: tuple[str, ...], label: str) -> None:
    missing = sorted(set(required).difference(frame.columns))
    if missing:
        raise ValueError(f"{label} is missing mandatory columns: {missing}")


def validate_inputs(
    history: pd.DataFrame,
    future_calendar: pd.DataFrame,
    bundle: ForecastModelBundle,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, np.ndarray, int]:
    """Validate and reshape long-form history plus known future calendar."""
    _require_columns(history, HISTORY_COLUMNS, "history")
    _require_columns(future_calendar, FUTURE_CALENDAR_COLUMNS, "future_calendar")
    history = history.copy()
    future = future_calendar.copy()
    if history[list(HISTORY_COLUMNS)].isna().any().any():
        raise ValueError("history contains missing mandatory values")
    if future[list(FUTURE_CALENDAR_COLUMNS)].isna().any().any():
        raise ValueError("future_calendar contains missing mandatory values; use 'none' for no event")
    history["date"] = pd.to_datetime(history["date"], errors="raise")
    future["date"] = pd.to_datetime(future["date"], errors="raise")
    history["day_index"] = history["d"].str.removeprefix("d_").astype(int)
    future["day_index"] = future["d"].str.removeprefix("d_").astype(int)
    if history.duplicated(["store_id", "dept_id", "date"]).any():
        raise ValueError("history contains duplicate series-date rows")
    if len(future) != bundle.forecast_horizon or future["date"].nunique() != bundle.forecast_horizon:
        raise ValueError(f"future_calendar must contain exactly {bundle.forecast_horizon} unique dates")
    future = future.sort_values("date").reset_index(drop=True)
    if not future["date"].is_monotonic_increasing or not np.all(np.diff(future["date"].values).astype("timedelta64[D]") == np.timedelta64(1, "D")):
        raise ValueError("future_calendar dates must be consecutive and chronological")
    if not np.all(np.diff(future["day_index"]) == 1):
        raise ValueError("future_calendar d values must be consecutive")
    metadata = pd.DataFrame(bundle.series_metadata)
    requested = history[["state_id", "store_id", "dept_id"]].drop_duplicates()
    series = metadata.merge(requested, on=["state_id", "store_id", "dept_id"], how="inner").sort_values(["state_id", "store_id", "dept_id"]).reset_index(drop=True)
    if len(series) != len(requested):
        raise ValueError("history contains unknown or inconsistent store/department/state identity")
    counts = history.groupby(["state_id", "store_id", "dept_id"]).size()
    if counts.min() < bundle.required_history or counts.nunique() != 1:
        raise ValueError(f"each series must contain the same consecutive history with at least {bundle.required_history} days")
    expected_dates = pd.date_range(history.date.min(), history.date.max(), freq="D")
    if len(expected_dates) != counts.iloc[0] or history.date.nunique() != len(expected_dates):
        raise ValueError("history dates must be consecutive and shared across series")
    if future.date.min() != history.date.max() + pd.Timedelta(days=1):
        raise ValueError("future_calendar must begin one day after the historical cutoff")
    if future.day_index.iloc[0] != history.day_index.max() + 1:
        raise ValueError("future_calendar d values must follow the historical cutoff")
    ordered = history.sort_values(["state_id", "store_id", "dept_id", "date"])
    values = ordered.pivot_table(index=["state_id", "store_id", "dept_id"], columns="date", values="sales", aggfunc="first").reindex(pd.MultiIndex.from_frame(series[["state_id", "store_id", "dept_id"]])).to_numpy(float)
    if not np.isfinite(values).all():
        raise ValueError("historical sales must be finite and may not be silently imputed")
    if (values < 0).any():
        raise ValueError("historical sales must be nonnegative")
    calendar_input = future.rename(columns={"event_name": "event_name_1", "event_type": "event_type_1"})
    calendar = prepare_calendar(calendar_input[["d", "date", "event_name_1", "event_type_1", "snap_CA", "snap_TX", "snap_WI"]])
    return history, future, series, values, int(history.day_index.max())


def forecast(
    bundle: ForecastModelBundle,
    history: pd.DataFrame,
    future_calendar: pd.DataFrame,
) -> pd.DataFrame:
    """Generate 28-day nonnegative forecasts without future actuals."""
    _, future, series, values, absolute_origin = validate_inputs(history, future_calendar, bundle)
    relative_origin = values.shape[1]
    features = build_prediction_table(
        series, values, prepare_calendar(future.rename(columns={"event_name": "event_name_1", "event_type": "event_type_1"})),
        relative_origin, target_start_day=absolute_origin + 1,
    )
    encoded = np.column_stack([
        bundle.categorical_encoder.transform(features[list(bundle.categorical_features)]),
        features[list(bundle.numeric_features)].to_numpy(np.float32),
    ])
    raw = bundle.estimator.predict(encoded)
    if raw.size != len(series) * FORECAST_HORIZON or not np.isfinite(raw).all():
        raise ValueError("estimator returned an invalid forecast")
    prediction = np.clip(raw, 0, None)
    result = pd.DataFrame({
        "store_id": np.repeat(series.store_id.to_numpy(), FORECAST_HORIZON),
        "dept_id": np.repeat(series.dept_id.to_numpy(), FORECAST_HORIZON),
        "state_id": np.repeat(series.state_id.to_numpy(), FORECAST_HORIZON),
        "forecast_date": np.tile(future.date.to_numpy(), len(series)),
        "forecast_horizon": np.tile(np.arange(1, FORECAST_HORIZON + 1), len(series)),
        "predicted_sales": prediction,
    })
    return result[list(OUTPUT_COLUMNS)]


def forecast_from_artifact(
    model_path: str | Path,
    history: pd.DataFrame,
    future_calendar: pd.DataFrame,
) -> pd.DataFrame:
    """Load a bundle and generate forecasts."""
    return forecast(load_bundle(model_path), history, future_calendar)
