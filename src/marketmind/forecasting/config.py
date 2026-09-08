"""Frozen production configuration for MarketMind demand forecasting."""

from __future__ import annotations

FORECAST_HORIZON = 28
LAGS = (1, 7, 14, 28, 56)
ROLLING_WINDOWS = (7, 28, 56)
MINIMUM_HISTORY = 56
MODEL_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"
CORE_GRAIN = ("store_id", "dept_id", "date")
IDENTITY_COLUMNS = ("store_id", "dept_id", "state_id")
CATEGORICAL_FEATURES = (*IDENTITY_COLUMNS, "event_name", "event_type")
NUMERIC_FEATURES = (
    "forecast_horizon", "lag_1", "lag_7", "lag_14", "lag_28", "lag_56",
    "rolling_mean_7", "rolling_std_7", "rolling_mean_28", "rolling_std_28",
    "rolling_mean_56", "rolling_std_56", "day_of_week", "day_of_month",
    "month", "year", "day_index", "snap",
)
FEATURE_COLUMNS = (*CATEGORICAL_FEATURES, *NUMERIC_FEATURES)
CALENDAR_FEATURES = (
    "day_of_week", "day_of_month", "month", "year", "day_index",
    "event_name", "event_type", "snap",
)
FROZEN_MODEL_PARAMS = {
    "loss": "squared_error",
    "learning_rate": 0.05,
    "max_iter": 160,
    "max_leaf_nodes": 63,
    "max_depth": None,
    "min_samples_leaf": 100,
    "l2_regularization": 1.0,
    "early_stopping": False,
    "random_state": 42,
}
RESEARCH_TRAINING_CUTOFF = 1913
PRODUCTION_TRAINING_CUTOFF = 1941
POSTPROCESSING = "clip predictions below zero to zero"
TARGET_DEFINITION = "observed daily unit sales aggregated by store and department"
OUTPUT_COLUMNS = (
    "store_id", "dept_id", "state_id", "forecast_date",
    "forecast_horizon", "predicted_sales",
)
