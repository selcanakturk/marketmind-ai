"""Temporal calibration utilities for frozen return-risk scores."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

CALIBRATION_SNAPSHOT = pd.Timestamp("2017-08-31 23:59:59")


@dataclass
class ScoreCalibrator:
    """Calibrate one-dimensional scores on the frozen August cohort only."""

    method: str
    estimator: object | None = None

    def fit(self, scores, target, snapshot_at) -> "ScoreCalibrator":
        snapshots = set(pd.to_datetime(pd.Series(snapshot_at)))
        if snapshots != {CALIBRATION_SNAPSHOT}:
            raise ValueError("calibration may use only the August 31 cohort")
        score = np.asarray(scores, dtype=float)
        y = np.asarray(target, dtype=int)
        if len(score) != len(y) or len(score) == 0 or not np.isfinite(score).all():
            raise ValueError("calibration scores and target must be aligned and finite")
        if set(np.unique(y)) != {0, 1}:
            raise ValueError("calibration target must contain binary no-return outcomes")
        if self.method == "sigmoid":
            self.estimator = LogisticRegression(
                solver="lbfgs", max_iter=2000, random_state=42
            ).fit(score.reshape(-1, 1), y)
        elif self.method == "isotonic":
            self.estimator = IsotonicRegression(
                y_min=0.0, y_max=1.0, out_of_bounds="clip"
            ).fit(score, y)
        else:
            raise ValueError("method must be 'sigmoid' or 'isotonic'")
        return self

    def transform(self, scores) -> np.ndarray:
        if self.estimator is None:
            raise ValueError("calibrator is not fitted")
        score = np.asarray(scores, dtype=float)
        if not np.isfinite(score).all():
            raise ValueError("scores must be finite")
        if self.method == "sigmoid":
            result = self.estimator.predict_proba(score.reshape(-1, 1))[:, 1]
        else:
            result = self.estimator.predict(score)
        if not np.isfinite(result).all() or ((result < 0) | (result > 1)).any():
            raise ValueError("calibrated scores must lie in [0, 1]")
        return result
