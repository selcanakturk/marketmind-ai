"""Frozen production contract for the Customer Return Risk engine."""

from __future__ import annotations

import pandas as pd

MODEL_VERSION = "return-risk-extratrees-et2-2017-11-v1"
SCHEMA_VERSION = "1.0"
TARGET_HORIZON_DAYS = 28
MIN_OBSERVED_HISTORY_DAYS = 90
MIN_BASKETS = 5
MIN_ACTIVE_SPAN_DAYS = 30
DEFAULT_CAPACITY = 0.10
SECONDARY_CAPACITIES = (0.05, 0.20)

FROZEN_FEATURE_NAMES = (
    "recency_days", "basket_frequency_lifetime", "monetary_lifetime",
    "average_basket_value", "baskets_last_7d", "baskets_last_28d",
    "spend_last_28d", "median_days_between_baskets",
    "std_days_between_baskets", "active_span_days", "unique_departments",
    "department_spend_hhi", "discount_share_of_gross",
    "coupon_basket_rate", "baskets_28d_change", "spend_28d_change",
)

ET2_PARAMETERS = {
    "n_estimators": 300, "max_depth": 12, "min_samples_leaf": 10,
    "max_features": "sqrt", "class_weight": None, "n_jobs": -1,
    "random_state": 42,
}

PRODUCTION_TRAINING_SNAPSHOTS = tuple(
    pd.Timestamp(value) for value in (
        "2017-04-30 23:59:59", "2017-05-31 23:59:59",
        "2017-06-30 23:59:59", "2017-07-31 23:59:59",
        "2017-08-31 23:59:59", "2017-09-30 23:59:59",
        "2017-10-31 23:59:59", "2017-11-30 23:59:59",
    )
)
TRAINING_CUTOFF = PRODUCTION_TRAINING_SNAPSHOTS[-1]
OUTCOME_OBSERVATION_CUTOFF = pd.Timestamp("2017-12-28 23:59:59")
EXPECTED_TRAINING_ROWS = 17_074

RESEARCH_METRICS = {
    "development": {"pr_auc": 0.4827, "roc_auc": 0.8576, "brier": 0.0916, "log_loss": 0.2944},
    "consumed_lockbox": {
        "eligible": 2322, "prevalence": 0.146856, "pr_auc": 0.4999,
        "roc_auc": 0.8691, "brier": 0.0953, "log_loss": 0.2995,
        "top_10_flagged": 233, "top_10_precision": 0.5536,
        "top_10_recall": 0.3783, "top_10_lift": 3.77,
    },
}
