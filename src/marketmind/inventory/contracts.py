"""Frozen Phase 6 inventory contract primitives, not a replenishment engine."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil, isfinite, sqrt

import numpy as np
import pandas as pd
from scipy.stats import norm

FORECAST_HORIZON_DAYS = 28
PLANNING_GRAIN = ("store_id", "dept_id", "day")
SERVICE_LEVEL_MIN = 0.50
SERVICE_LEVEL_MAX = 0.999


@dataclass(frozen=True)
class InventoryScenarioInput:
    """Business-owned values required for one store-department snapshot."""

    snapshot_date: str | pd.Timestamp
    store_id: str
    dept_id: str
    on_hand_inventory: float
    on_order_inventory: float
    backorders: float
    lead_time_days: int
    review_period_days: int
    service_level_target: float
    minimum_order_quantity: float | None = None
    case_pack_size: float | None = None
    maximum_order_quantity: float | None = None

    def validate(self) -> None:
        pd.to_datetime(self.snapshot_date, errors="raise")
        if not self.store_id or not self.dept_id:
            raise ValueError("store_id and dept_id are required")
        for name in ("on_hand_inventory", "on_order_inventory", "backorders"):
            value = getattr(self, name)
            if not isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and nonnegative")
        if isinstance(self.lead_time_days, bool) or not isinstance(self.lead_time_days, (int, np.integer)) or self.lead_time_days < 0:
            raise ValueError("lead_time_days must be an integer >= 0")
        if isinstance(self.review_period_days, bool) or not isinstance(self.review_period_days, (int, np.integer)) or self.review_period_days < 1:
            raise ValueError("review_period_days must be an integer >= 1")
        validate_protection_period(self.lead_time_days, self.review_period_days)
        if not isfinite(self.service_level_target) or not SERVICE_LEVEL_MIN <= self.service_level_target <= SERVICE_LEVEL_MAX:
            raise ValueError("service_level_target must be in [0.50, 0.999]")
        for name in ("minimum_order_quantity", "case_pack_size", "maximum_order_quantity"):
            value = getattr(self, name)
            if value is not None and (not isfinite(value) or value <= 0):
                raise ValueError(f"{name} must be finite and > 0 when supplied")


def inventory_position(on_hand: float, on_order: float, backorders: float) -> float:
    """Available plus inbound minus owed units; result may be negative."""
    values = (on_hand, on_order, backorders)
    if any(not isfinite(value) or value < 0 for value in values):
        raise ValueError("inventory components must be finite and nonnegative")
    return float(on_hand + on_order - backorders)


def validate_protection_period(lead_time_days: int, review_period_days: int) -> int:
    if isinstance(lead_time_days, bool) or not isinstance(lead_time_days, (int, np.integer)) or lead_time_days < 0:
        raise ValueError("lead time must be an integer >= 0")
    if isinstance(review_period_days, bool) or not isinstance(review_period_days, (int, np.integer)) or review_period_days < 1:
        raise ValueError("review period must be an integer >= 1")
    period = int(lead_time_days + review_period_days)
    if period > FORECAST_HORIZON_DAYS:
        raise ValueError("protection period exceeds the frozen 28-day forecast horizon")
    return period


def aggregate_forecast(forecast: pd.DataFrame, scenario: InventoryScenarioInput) -> dict[str, float]:
    """Validate snapshot-aligned daily forecasts and expose lead/protection demand."""
    scenario.validate()
    required = {"forecast_date", "store_id", "dept_id", "predicted_sales"}
    if not required.issubset(forecast.columns):
        raise ValueError(f"forecast missing columns: {sorted(required - set(forecast.columns))}")
    frame = forecast[list(required)].copy()
    frame["forecast_date"] = pd.to_datetime(frame["forecast_date"], errors="raise").dt.normalize()
    if frame.duplicated(["forecast_date", "store_id", "dept_id"]).any():
        raise ValueError("forecast contains duplicate series-date rows")
    if len(frame) != FORECAST_HORIZON_DAYS or frame.store_id.nunique() != 1 or frame.dept_id.nunique() != 1:
        raise ValueError("one series requires exactly 28 forecast rows")
    if frame.store_id.iloc[0] != scenario.store_id or frame.dept_id.iloc[0] != scenario.dept_id:
        raise ValueError("forecast identity does not match inventory snapshot")
    values = pd.to_numeric(frame.predicted_sales, errors="coerce")
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("forecast demand must be finite and nonnegative")
    frame["predicted_sales"] = values
    frame = frame.sort_values("forecast_date")
    expected_dates = pd.date_range(pd.Timestamp(scenario.snapshot_date).normalize() + pd.Timedelta(days=1), periods=28)
    if not frame.forecast_date.reset_index(drop=True).equals(pd.Series(expected_dates)):
        raise ValueError("forecast must cover the 28 consecutive days immediately after snapshot_date")
    protection = validate_protection_period(scenario.lead_time_days, scenario.review_period_days)
    return {
        "forecast_lead_time_demand": float(frame.predicted_sales.iloc[:scenario.lead_time_days].sum()),
        "forecast_protection_demand": float(frame.predicted_sales.iloc[:protection].sum()),
        "expected_daily_demand": float(frame.predicted_sales.iloc[:protection].mean()),
    }


def normal_scale_safety_stock(daily_error_scale: float, protection_days: int, service_level: float) -> float:
    """Candidate A only; assumes independent normal-like daily forecast errors."""
    if not isfinite(daily_error_scale) or daily_error_scale < 0 or protection_days < 1:
        raise ValueError("uncertainty scale must be nonnegative and protection positive")
    if not SERVICE_LEVEL_MIN <= service_level <= SERVICE_LEVEL_MAX:
        raise ValueError("service level outside frozen range")
    return float(norm.ppf(service_level) * daily_error_scale * sqrt(protection_days))


def target_and_unconstrained_order(protection_demand: float, safety_stock: float, position: float) -> tuple[float, float]:
    if any(not isfinite(value) for value in (protection_demand, safety_stock, position)) or protection_demand < 0 or safety_stock < 0:
        raise ValueError("demand and safety stock must be finite and nonnegative")
    target = protection_demand + safety_stock
    return target, max(0.0, target - position)


def apply_order_constraints(raw_quantity: float, minimum_order_quantity: float | None = None,
                            case_pack_size: float | None = None, maximum_order_quantity: float | None = None) -> tuple[int, str | None]:
    """Frozen adjustment order: MOQ, case-pack ceiling, maximum clip, final units."""
    from marketmind.inventory.policy import apply_operational_constraints
    if case_pack_size is not None and float(case_pack_size).is_integer(): case_pack_size=int(case_pack_size)
    if maximum_order_quantity is not None and float(maximum_order_quantity).is_integer(): maximum_order_quantity=int(maximum_order_quantity)
    result=apply_operational_constraints(raw_quantity,minimum_order_quantity,case_pack_size,maximum_order_quantity)
    return result["recommended_order_quantity"],result["constraint_warning"]


def days_of_cover(position: float, expected_daily_demand: float) -> float | None:
    if not isfinite(position) or not isfinite(expected_daily_demand):
        raise ValueError("coverage inputs must be finite")
    return None if expected_daily_demand <= 0 else float(position / expected_daily_demand)
