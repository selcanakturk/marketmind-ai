"""Predeclared statistical and review-capacity alert policies."""

from __future__ import annotations

import numpy as np
import pandas as pd


def fixed_threshold(scores: pd.DataFrame, threshold: int) -> pd.Series:
    if threshold not in (3, 4):
        raise ValueError("only predeclared thresholds 3 and 4 are allowed")
    return scores.anomaly_score.abs().ge(threshold).fillna(False)


def top_n_per_day(scores: pd.DataFrame, n: int) -> pd.Series:
    if n not in (5, 10):
        raise ValueError("only predeclared capacities 5 and 10 are allowed")
    result = pd.Series(False, index=scores.index)
    defined = scores.loc[scores.anomaly_score.notna()].copy()
    defined["absolute_score"] = defined.anomaly_score.abs()
    ordered = defined.sort_values(
        ["date", "absolute_score", "store_id", "dept_id"],
        ascending=[True, False, True, True], kind="mergesort",
    )
    selected = ordered.groupby("date", sort=True).head(n).index
    result.loc[selected] = True
    return result


def severity_rank(scores: pd.DataFrame) -> pd.Series:
    output = pd.Series(pd.NA, index=scores.index, dtype="Int64")
    defined = scores.loc[scores.anomaly_score.notna()].copy()
    defined["absolute_score"] = defined.anomaly_score.abs()
    ordered = defined.sort_values(["date", "absolute_score", "store_id", "dept_id"], ascending=[True, False, True, True])
    ranks = ordered.groupby("date").cumcount() + 1
    output.loc[ordered.index] = ranks.astype("Int64")
    return output
