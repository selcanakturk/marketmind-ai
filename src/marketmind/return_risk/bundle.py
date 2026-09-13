"""Serializable, validated production bundle for return-risk scoring."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
from sklearn.ensemble import ExtraTreesClassifier

from marketmind.return_risk.config import (
    DEFAULT_CAPACITY, ET2_PARAMETERS, FROZEN_FEATURE_NAMES, MODEL_VERSION,
    SCHEMA_VERSION, TARGET_HORIZON_DAYS,
)


@dataclass
class ReturnRiskModelBundle:
    estimator: ExtraTreesClassifier
    feature_names: tuple[str, ...]
    model_version: str
    schema_version: str
    training_cutoff: str
    outcome_observation_cutoff: str
    training_cohorts: list[dict[str, Any]]
    training_rows: int
    target_horizon_days: int
    eligibility_rule: dict[str, int]
    score_semantics: str
    default_capacity: float
    secondary_capacities: tuple[float, ...]
    model_parameters: dict[str, Any]
    library_versions: dict[str, str]
    research_metrics: dict[str, Any]
    lockbox_status: str

    def validate(self) -> None:
        if not isinstance(self.estimator, ExtraTreesClassifier):
            raise TypeError("bundle estimator must be ExtraTreesClassifier")
        if tuple(self.feature_names) != FROZEN_FEATURE_NAMES:
            raise ValueError("bundle feature schema does not match the frozen contract")
        if self.model_version != MODEL_VERSION or self.schema_version != SCHEMA_VERSION:
            raise ValueError("bundle version does not match the production contract")
        if self.target_horizon_days != TARGET_HORIZON_DAYS:
            raise ValueError("bundle target horizon does not match the frozen contract")
        if self.default_capacity != DEFAULT_CAPACITY:
            raise ValueError("bundle default capacity does not match the frozen policy")
        actual = self.estimator.get_params()
        if self.model_parameters != ET2_PARAMETERS or any(actual.get(k) != v for k, v in ET2_PARAMETERS.items()):
            raise ValueError("bundle estimator does not match frozen ET-2")
        if hasattr(self, "calibrator"):
            raise ValueError("the frozen production bundle must not contain a calibrator")


def save_bundle(bundle: ReturnRiskModelBundle, path: str | Path) -> None:
    bundle.validate()
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, destination)


def load_bundle(path: str | Path) -> ReturnRiskModelBundle:
    bundle = joblib.load(Path(path))
    if not isinstance(bundle, ReturnRiskModelBundle):
        raise TypeError("artifact is not a ReturnRiskModelBundle")
    bundle.validate()
    return bundle
