"""Deterministic development-only return-risk policy helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd

from marketmind.return_risk.features import BASELINE_FEATURE_ORDER
from marketmind.return_risk.models import EXTRA_TREES_CANDIDATE_PARAMETERS


def top_capacity_flags(scores, capacity: float, stable_keys=None) -> np.ndarray:
    """Flag exactly ceil(capacity * n) highest scores with deterministic ties."""

    score = np.asarray(scores, dtype=float)
    if len(score) == 0 or not np.isfinite(score).all():
        raise ValueError("scores must be nonempty and finite")
    if not 0 < capacity <= 1:
        raise ValueError("capacity must lie in (0, 1]")
    keys = np.arange(len(score)) if stable_keys is None else np.asarray(stable_keys)
    if len(keys) != len(score):
        raise ValueError("stable_keys must align with scores")
    selected = max(1, int(np.ceil(capacity * len(score))))
    order = np.lexsort((keys.astype(str), -score))
    flags = np.zeros(len(score), dtype=bool)
    flags[order[:selected]] = True
    return flags


def threshold_summary(y_true, scores, thresholds) -> pd.DataFrame:
    """Return deterministic classification summaries for a supplied grid."""

    y = np.asarray(y_true, dtype=int)
    score = np.asarray(scores, dtype=float)
    if set(np.unique(y)).difference({0, 1}) or len(y) != len(score):
        raise ValueError("target must be aligned binary return_risk_target")
    rows = []
    for threshold in thresholds:
        pred = score >= threshold
        tp = int(((y == 1) & pred).sum())
        fp = int(((y == 0) & pred).sum())
        fn = int(((y == 1) & ~pred).sum())
        tn = int(((y == 0) & ~pred).sum())
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        rows.append({
            "threshold": float(threshold), "flagged": int(pred.sum()),
            "positive_prediction_rate": float(pred.mean()),
            "precision": precision, "recall": recall,
            "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
            "tn": tn, "fp": fp, "fn": fn, "tp": tp,
        })
    return pd.DataFrame(rows)


def point_in_time_segment_join(
    scores: pd.DataFrame, assignments: pd.DataFrame
) -> pd.DataFrame:
    """Join post-hoc segments only when household and snapshot keys agree."""

    keys = ["household_id", "snapshot_at"]
    required_scores = set(keys + ["score"])
    required_segments = {"household_id", "snapshot_date", "segment_code"}
    if not required_scores.issubset(scores) or not required_segments.issubset(assignments):
        raise ValueError("score or assignment columns are incomplete")
    segment = assignments.rename(columns={"snapshot_date": "snapshot_at"}).copy()
    for frame in (scores, segment):
        frame["snapshot_at"] = pd.to_datetime(frame["snapshot_at"])
    if scores.duplicated(keys).any() or segment.duplicated(keys).any():
        raise ValueError("household-snapshot keys must be unique")
    result = scores.merge(
        segment[keys + ["segment_code"]], on=keys, how="left", validate="one_to_one"
    )
    if result["segment_code"].isna().any():
        raise ValueError("every score requires an assignment from the same snapshot")
    return result


def freeze_lockbox_scores(
    features: pd.DataFrame,
    model,
    *,
    snapshot_at: str | pd.Timestamp,
) -> pd.DataFrame:
    """Create the outcome-free frozen score/rank/capacity artifact.

    This function deliberately accepts features only and cannot join labels.
    It also verifies the selected ET-2 contract before score generation.
    """

    if "return_risk_target" in features.columns:
        raise ValueError("lockbox scores must be frozen before target access")
    if tuple(features.columns) != BASELINE_FEATURE_ORDER:
        raise ValueError("lockbox features must match the frozen 16-column order")
    expected = EXTRA_TREES_CANDIDATE_PARAMETERS["ET-2"]
    actual = model.get_params()
    if any(actual.get(key) != value for key, value in expected.items()):
        raise ValueError("model parameters do not match frozen ET-2")
    if features.index.has_duplicates:
        raise ValueError("eligible household IDs must be unique")
    score = model.predict_proba(features)[:, 1]
    if not np.isfinite(score).all() or ((score < 0) | (score > 1)).any():
        raise ValueError("ET-2 scores must be finite and in [0, 1]")
    household = features.index.astype(str)
    order = np.lexsort((household, -score))
    ranks = np.empty(len(features), dtype=int)
    ranks[order] = np.arange(1, len(features) + 1)
    result = pd.DataFrame({
        "household_id": household,
        "snapshot_date": pd.Timestamp(snapshot_at),
        "risk_score": score,
        "risk_rank": ranks,
    })
    keys = result["household_id"].to_numpy()
    for capacity, column in ((0.05, "top_05_flag"), (0.10, "top_10_flag"), (0.20, "top_20_flag")):
        result[column] = top_capacity_flags(score, capacity, keys)
    return result.sort_values("risk_rank").reset_index(drop=True)
