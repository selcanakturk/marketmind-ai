"""Deterministic nonlinear challenger definitions for return-risk research."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

from marketmind.return_risk.features import BASELINE_FEATURE_ORDER

TRAINING_SNAPSHOTS = (
    pd.Timestamp("2017-04-30 23:59:59"),
    pd.Timestamp("2017-05-31 23:59:59"),
    pd.Timestamp("2017-06-30 23:59:59"),
    pd.Timestamp("2017-07-31 23:59:59"),
    pd.Timestamp("2017-08-31 23:59:59"),
)
VALIDATION_SNAPSHOTS = (
    pd.Timestamp("2017-09-30 23:59:59"),
    pd.Timestamp("2017-10-31 23:59:59"),
)
LOCKBOX_SNAPSHOT = pd.Timestamp("2017-11-30 23:59:59")

HGB_CANDIDATE_PARAMETERS: Mapping[str, dict[str, object]] = {
    "HGB-1": {
        "learning_rate": 0.05, "max_iter": 150, "max_leaf_nodes": 15,
        "min_samples_leaf": 50, "l2_regularization": 1.0,
        "early_stopping": False, "random_state": 42,
    },
    "HGB-2": {
        "learning_rate": 0.05, "max_iter": 200, "max_leaf_nodes": 31,
        "min_samples_leaf": 50, "l2_regularization": 1.0,
        "early_stopping": False, "random_state": 42,
    },
    "HGB-3": {
        "learning_rate": 0.03, "max_iter": 250, "max_leaf_nodes": 31,
        "min_samples_leaf": 50, "l2_regularization": 1.0,
        "early_stopping": False, "random_state": 42,
    },
    "HGB-4": {
        "learning_rate": 0.05, "max_iter": 200, "max_leaf_nodes": 31,
        "min_samples_leaf": 100, "l2_regularization": 1.0,
        "early_stopping": False, "random_state": 42,
    },
    "HGB-5": {
        "learning_rate": 0.05, "max_iter": 200, "max_leaf_nodes": 15,
        "min_samples_leaf": 50, "l2_regularization": 5.0,
        "early_stopping": False, "random_state": 42,
    },
}


def make_hgb_candidate(name: str) -> HistGradientBoostingClassifier:
    """Construct exactly one predeclared, unweighted HGB candidate."""

    if name not in HGB_CANDIDATE_PARAMETERS:
        raise ValueError(f"unknown HGB candidate: {name}")
    return HistGradientBoostingClassifier(**HGB_CANDIDATE_PARAMETERS[name])


def validate_model_frame(features: pd.DataFrame) -> pd.DataFrame:
    """Enforce the unchanged 16-feature order and finite/raw input contract."""

    if tuple(features.columns) != BASELINE_FEATURE_ORDER:
        raise ValueError("HGB features must match the frozen baseline order")
    values = features.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("the audited HGB baseline features must be finite")
    return features


def fit_hgb_candidate(
    name: str,
    features: pd.DataFrame,
    target,
    snapshot_at,
) -> HistGradientBoostingClassifier:
    """Fit a candidate only when every row belongs to a frozen training snapshot."""

    X = validate_model_frame(features)
    snapshots = pd.to_datetime(pd.Series(snapshot_at)).unique()
    if not set(pd.Timestamp(value) for value in snapshots).issubset(TRAINING_SNAPSHOTS):
        raise ValueError("HGB fit may use only April-August training snapshots")
    y = np.asarray(target, dtype=int)
    if len(X) != len(y) or set(np.unique(y)).difference({0, 1}):
        raise ValueError("target must be aligned binary return_risk_target")
    return make_hgb_candidate(name).fit(X, y)
