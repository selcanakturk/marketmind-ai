"""Authoritative frozen configuration for production sales anomalies."""

from __future__ import annotations

GRAIN = ("store_id", "dept_id")
MODEL_VERSION = "m5-robust-residual-anomaly-v1"
SCHEMA_VERSION = "1.0"
MAD_MULTIPLIER = 1.4826
ROBUST_THRESHOLD = 3.0
REVIEW_CAPACITY_PER_DAY = 5
MIN_RESIDUAL_COUNT = 28
IF_ROLE = "secondary_diagnostic"
IF_CONFIG_NAME = "IF-3"
IF_FEATURE_COLUMNS = (
    "robust_residual_score", "residual", "absolute_residual", "expected_sales",
    "day_of_week_sin", "day_of_week_cos", "event_present", "snap",
)
IF_PARAMETERS = {
    "n_estimators": 300, "max_samples": 1024, "contamination": "auto",
    "max_features": 1.0, "bootstrap": False, "random_state": 42, "n_jobs": 1,
}
OUTPUT_COLUMNS = (
    "date", "store_id", "dept_id", "actual_sales", "expected_sales", "residual",
    "anomaly_score", "direction", "is_statistical_alert", "daily_review_rank",
    "is_review_priority", "if_anomaly_score", "event_name", "event_type",
    "snap_active", "undefined_score_reason",
)
LOCKBOX_STATUS = "consumed"
