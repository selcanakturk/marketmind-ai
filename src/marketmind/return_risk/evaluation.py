"""Evaluation helpers for temporally held-out return-risk scores."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)


def score_metrics(y_true, scores, threshold: float = 0.5) -> dict[str, object]:
    """Return discrimination, loss, and descriptive threshold metrics."""

    y = np.asarray(y_true, dtype=int)
    score = np.asarray(scores, dtype=float)
    if len(y) != len(score) or len(y) == 0:
        raise ValueError("y_true and scores must have equal nonzero length")
    pred = score >= threshold
    return {
        "n": len(y),
        "prevalence": float(y.mean()),
        "pr_auc": float(average_precision_score(y, score)),
        "roc_auc": float(roc_auc_score(y, score)),
        "log_loss": float(log_loss(y, np.clip(score, 1e-15, 1 - 1e-15))),
        "brier": float(brier_score_loss(y, score)),
        "precision_at_0_5": float(precision_score(y, pred, zero_division=0)),
        "recall_at_0_5": float(recall_score(y, pred, zero_division=0)),
        "f1_at_0_5": float(f1_score(y, pred, zero_division=0)),
        "confusion_matrix": confusion_matrix(y, pred, labels=[0, 1]).tolist(),
    }


def capacity_metrics(y_true, scores, fractions=(0.05, 0.10, 0.20)) -> pd.DataFrame:
    """Evaluate deterministic top-score intervention capacities."""

    frame = pd.DataFrame({"y": np.asarray(y_true, int), "score": np.asarray(scores, float)})
    if frame.empty or frame.isna().any().any():
        raise ValueError("capacity inputs must be nonempty and complete")
    frame["order"] = np.arange(len(frame))
    ranked = frame.sort_values(["score", "order"], ascending=[False, True])
    positives = int(frame.y.sum())
    rows = []
    for fraction in fractions:
        if not 0 < fraction <= 1:
            raise ValueError("capacity fractions must lie in (0, 1]")
        selected_n = max(1, int(np.ceil(len(frame) * fraction)))
        caught = int(ranked.head(selected_n).y.sum())
        rows.append({
            "capacity": float(fraction),
            "selected": selected_n,
            "positives_captured": caught,
            "precision": caught / selected_n,
            "recall": caught / positives if positives else np.nan,
        })
    return pd.DataFrame(rows)


def calibration_bins(y_true, scores, n_bins: int = 10) -> pd.DataFrame:
    """Return observed versus mean predicted risk in quantile bins."""

    y = np.asarray(y_true, int)
    score = np.asarray(scores, float)
    observed, predicted = calibration_curve(y, score, n_bins=n_bins, strategy="quantile")
    return pd.DataFrame({"mean_score": predicted, "observed_rate": observed})


def expected_calibration_error(y_true, scores, n_bins: int = 10) -> float:
    """Return equal-width expected calibration error, weighted by bin size."""

    frame = pd.DataFrame({"y": np.asarray(y_true, int), "score": np.asarray(scores, float)})
    if frame.empty or frame.isna().any().any() or ((frame.score < 0) | (frame.score > 1)).any():
        raise ValueError("calibration inputs must be complete scores in [0, 1]")
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    frame["bin"] = pd.cut(frame.score, edges, include_lowest=True, labels=False)
    grouped = frame.groupby("bin", observed=True).agg(n=("y", "size"), observed=("y", "mean"), predicted=("score", "mean"))
    return float((grouped.n / len(frame) * (grouped.observed - grouped.predicted).abs()).sum())


def clustered_bootstrap_auc(
    frame: pd.DataFrame,
    *,
    household_column: str,
    target_column: str,
    score_column: str,
    n_bootstrap: int = 300,
    random_state: int = 42,
) -> dict[str, tuple[float, float]]:
    """Percentile intervals from resampling household clusters with replacement."""

    groups = list(frame.groupby(household_column, sort=True))
    rng = np.random.default_rng(random_state)
    pr, roc = [], []
    for _ in range(n_bootstrap):
        sampled = rng.integers(0, len(groups), len(groups))
        boot = pd.concat([groups[i][1] for i in sampled], ignore_index=True)
        if boot[target_column].nunique() < 2:
            continue
        pr.append(average_precision_score(boot[target_column], boot[score_column]))
        roc.append(roc_auc_score(boot[target_column], boot[score_column]))
    return {
        "pr_auc_95ci": tuple(float(x) for x in np.quantile(pr, [0.025, 0.975])),
        "roc_auc_95ci": tuple(float(x) for x in np.quantile(roc, [0.025, 0.975])),
    }
