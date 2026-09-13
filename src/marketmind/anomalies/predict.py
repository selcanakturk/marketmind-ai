"""Pure scoring and explicit chronological state updates for production anomalies."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from marketmind.anomalies.bundle import RobustResidualState
from marketmind.anomalies.config import OUTPUT_COLUMNS, REVIEW_CAPACITY_PER_DAY, ROBUST_THRESHOLD
from marketmind.anomalies.isolation_forest import anomaly_score as score_if, build_features


ACTUAL_COLUMNS = ("date", "store_id", "dept_id", "actual_sales")
FORECAST_COLUMNS = ("date", "store_id", "dept_id", "expected_sales")


def _prepared(frame: pd.DataFrame, required: tuple[str, ...], value: str) -> pd.DataFrame:
    missing = set(required) - set(frame.columns)
    if missing: raise ValueError(f"missing required columns: {sorted(missing)}")
    result = frame.loc[:, required].copy()
    try: result["date"] = pd.to_datetime(result["date"], errors="raise").dt.normalize()
    except Exception as exc: raise ValueError("date must be parseable") from exc
    if result.duplicated(["date", "store_id", "dept_id"]).any(): raise ValueError("duplicate series-date rows")
    numeric = pd.to_numeric(result[value], errors="coerce")
    if not np.isfinite(numeric).all(): raise ValueError(f"{value} must be finite")
    if value == "actual_sales" and (numeric < 0).any(): raise ValueError("actual_sales must be nonnegative")
    result[value] = numeric.astype(float)
    return result


def _calendar(dates: pd.Series, calendar_context: pd.DataFrame | None) -> tuple[pd.DataFrame, pd.DataFrame]:
    base = pd.DataFrame({"date": pd.Series(dates.unique())})
    if calendar_context is None:
        base = base.assign(event_name=pd.NA, event_type=pd.NA, snap_CA=0, snap_TX=0, snap_WI=0)
    else:
        context = calendar_context.copy(); context["date"] = pd.to_datetime(context["date"], errors="raise").dt.normalize()
        if context.duplicated("date").any(): raise ValueError("calendar context must contain one row per date")
        for column in ("event_name", "event_type", "snap_CA", "snap_TX", "snap_WI"):
            if column not in context: context[column] = pd.NA if column.startswith("event") else 0
        base = base.merge(context[["date", "event_name", "event_type", "snap_CA", "snap_TX", "snap_WI"]], on="date", how="left", validate="one_to_one")
    for column in ("snap_CA", "snap_TX", "snap_WI"): base[column] = base[column].fillna(0).astype(int)
    if_calendar = base.rename(columns={"event_name": "event_name_1"})
    return base, if_calendar


def score_batch(actual_sales: pd.DataFrame, forecast_predictions: pd.DataFrame,
                residual_state: RobustResidualState, calendar_context: pd.DataFrame | None = None,
                isolation_forest_bundle: IsolationForest | None = None) -> pd.DataFrame:
    """Score one complete date without mutating state."""
    residual_state.validate()
    actual = _prepared(actual_sales, ACTUAL_COLUMNS, "actual_sales")
    forecast = _prepared(forecast_predictions, FORECAST_COLUMNS, "expected_sales")
    if actual.date.nunique() != 1: raise ValueError("score_batch accepts exactly one date")
    keys = ["date", "store_id", "dept_id"]
    if set(map(tuple, actual[keys].itertuples(index=False, name=None))) != set(map(tuple, forecast[keys].itertuples(index=False, name=None))):
        raise ValueError("actual and forecast series-date rows must align exactly")
    result = actual.merge(forecast, on=keys, validate="one_to_one")
    catalog = residual_state.series_metadata
    result = result.merge(catalog, on=["store_id", "dept_id"], how="left", validate="many_to_one")
    if result.state_id.isna().any(): raise ValueError("unknown store or department series")
    if result.date.min() <= pd.Timestamp(residual_state.state_updated_through): raise ValueError("scoring dates must follow state cutoff")
    summary = residual_state.summary().drop(columns=["state_id", "state_updated_through"])
    result = result.merge(summary, on=["store_id", "dept_id"], validate="many_to_one")
    result["residual"] = result.actual_sales - result.expected_sales
    reason = np.where(result.residual_count < 28, "insufficient_prior_residuals",
             np.where(~np.isfinite(result.robust_scale), "nonfinite_scale", np.where(result.robust_scale <= 0, "zero_mad", "")))
    result["undefined_score_reason"] = reason
    result["anomaly_score"] = np.where(reason == "", (result.residual - result.residual_median) / result.robust_scale, np.nan)
    result["direction"] = np.where(reason != "", "undefined", np.where(result.anomaly_score > 0, "spike", np.where(result.anomaly_score < 0, "drop", "neutral")))
    result["is_statistical_alert"] = result.anomaly_score.abs().ge(ROBUST_THRESHOLD).fillna(False)
    result = result.sort_values(["anomaly_score", "store_id", "dept_id"], ascending=[False, True, True])
    defined = result.anomaly_score.notna()
    ranked = result.loc[defined].assign(_abs=result.loc[defined, "anomaly_score"].abs()).sort_values(["_abs", "store_id", "dept_id"], ascending=[False, True, True])
    ranks = pd.Series(np.arange(1, len(ranked) + 1), index=ranked.index, dtype="Int64")
    result["daily_review_rank"] = ranks.reindex(result.index).astype("Int64")
    result["is_review_priority"] = result.daily_review_rank.le(REVIEW_CAPACITY_PER_DAY).fillna(False)
    context, if_calendar = _calendar(result.date, calendar_context)
    result = result.merge(context[["date", "event_name", "event_type", "snap_CA", "snap_TX", "snap_WI"]], on="date", validate="many_to_one")
    result["snap_active"] = np.fromiter((getattr(row, f"snap_{row.state_id}") for row in result.itertuples()), int, len(result))
    result["if_anomaly_score"] = np.nan
    if isolation_forest_bundle is not None:
        feature_input = result.drop(columns=["event_name", "event_type", "snap_CA", "snap_TX", "snap_WI"])
        result["if_anomaly_score"] = score_if(isolation_forest_bundle, build_features(feature_input, if_calendar))
    return result.loc[:, OUTPUT_COLUMNS].sort_values(["date", "store_id", "dept_id"]).reset_index(drop=True)


def update_state(residual_state: RobustResidualState, scored: pd.DataFrame) -> RobustResidualState:
    """Return a new state after appending a fully scored date; never mutate the input."""
    if scored.date.nunique() != 1: raise ValueError("update_state requires one scored date")
    updated = residual_state.copy()
    for row in scored.itertuples():
        key = (row.store_id, row.dept_id)
        if key not in updated.histories: raise ValueError("cannot update unknown series")
        updated.histories[key] = np.append(updated.histories[key], float(row.residual))
    date = pd.Timestamp(scored.date.iloc[0]); previous = pd.Timestamp(updated.state_updated_through)
    if date <= previous: raise ValueError("state updates must be chronological")
    updated.state_updated_through_d += int((date - previous).days)
    updated.state_updated_through = date.date().isoformat()
    updated.validate()
    return updated


def score_and_update(actual_sales: pd.DataFrame, forecast_predictions: pd.DataFrame,
                     residual_state: RobustResidualState, calendar_context: pd.DataFrame | None = None,
                     isolation_forest_bundle: IsolationForest | None = None):
    """Chronologically score each date, updating only after its complete batch."""
    actual = _prepared(actual_sales, ACTUAL_COLUMNS, "actual_sales")
    forecast = _prepared(forecast_predictions, FORECAST_COLUMNS, "expected_sales")
    state = residual_state.copy(); outputs = []
    for date in sorted(actual.date.unique()):
        a = actual[actual.date == date]; f = forecast[forecast.date == date]
        scored = score_batch(a, f, state, calendar_context, isolation_forest_bundle)
        outputs.append(scored); state = update_state(state, scored)
    if set(forecast.date.unique()) != set(actual.date.unique()): raise ValueError("actual and forecast dates must align exactly")
    return pd.concat(outputs, ignore_index=True), state
