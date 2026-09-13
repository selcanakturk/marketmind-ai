"""Serializable exact residual-history state and secondary IF artifact."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from marketmind.anomalies.config import MAD_MULTIPLIER, MODEL_VERSION, SCHEMA_VERSION


@dataclass
class RobustResidualState:
    histories: dict[tuple[str, str], np.ndarray]
    series_metadata: pd.DataFrame
    state_updated_through: str
    state_updated_through_d: int
    source: str
    model_version: str = MODEL_VERSION
    schema_version: str = SCHEMA_VERSION

    def validate(self) -> None:
        required = {"state_id", "store_id", "dept_id"}
        if set(self.series_metadata.columns) != required or len(self.series_metadata) != 70:
            raise ValueError("state requires exactly 70 series with state/store/department metadata")
        keys = set(map(tuple, self.series_metadata[["store_id", "dept_id"]].itertuples(index=False, name=None)))
        if set(self.histories) != keys:
            raise ValueError("residual histories do not match the 70-series catalog")
        if any(len(values) < 28 or not np.isfinite(values).all() for values in self.histories.values()):
            raise ValueError("each residual history must contain at least 28 finite OOS values")
        if self.model_version != MODEL_VERSION or self.schema_version != SCHEMA_VERSION:
            raise ValueError("state version violates production contract")

    def copy(self) -> "RobustResidualState":
        return deepcopy(self)

    def summary(self) -> pd.DataFrame:
        rows = []
        for metadata in self.series_metadata.sort_values(["store_id", "dept_id"]).itertuples(index=False):
            values = self.histories[(metadata.store_id, metadata.dept_id)]
            median = float(np.median(values)); mad = float(np.median(np.abs(values - median)))
            rows.append({"state_id": metadata.state_id, "store_id": metadata.store_id, "dept_id": metadata.dept_id,
                         "residual_count": len(values), "residual_median": median, "residual_mad": mad,
                         "robust_scale": MAD_MULTIPLIER * mad, "state_updated_through": self.state_updated_through})
        return pd.DataFrame(rows)


@dataclass
class AnomalyArtifacts:
    residual_state: RobustResidualState
    isolation_forest: IsolationForest | None
    if_feature_columns: tuple[str, ...]
    if_role: str

    def validate(self) -> None:
        self.residual_state.validate()
        if self.isolation_forest is not None and not isinstance(self.isolation_forest, IsolationForest):
            raise TypeError("secondary artifact must be IsolationForest")


def save_artifacts(artifacts: AnomalyArtifacts, path: str | Path) -> None:
    artifacts.validate(); destination = Path(path); destination.parent.mkdir(parents=True, exist_ok=True); joblib.dump(artifacts, destination, compress=3)


def load_artifacts(path: str | Path) -> AnomalyArtifacts:
    result = joblib.load(Path(path))
    if not isinstance(result, AnomalyArtifacts):
        raise TypeError("artifact is not AnomalyArtifacts")
    result.validate(); return result
