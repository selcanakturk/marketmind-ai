"""Strict blockwise robust scoring from prior OOS residuals."""

from __future__ import annotations

import numpy as np
import pandas as pd

from marketmind.anomalies.config import MAD_MULTIPLIER, MIN_RESIDUAL_COUNT

SCALE_FACTOR = MAD_MULTIPLIER
MIN_PRIOR_RESIDUALS = MIN_RESIDUAL_COUNT


def score_block(block: pd.DataFrame, prior: pd.DataFrame) -> pd.DataFrame:
    """Score the entire block from a frozen prior corpus, then return it unchanged."""
    required = {"store_id", "dept_id", "residual"}
    if not required.issubset(block) or not required.issubset(prior):
        raise ValueError("block and prior must contain series keys and residual")
    reference = prior.groupby(["store_id", "dept_id"])["residual"].agg(
        prior_residual_count="count", prior_residual_median="median"
    ).reset_index()
    mad = prior.groupby(["store_id", "dept_id"])["residual"].apply(
        lambda value: float(np.median(np.abs(value - np.median(value))))
    ).rename("prior_residual_mad").reset_index()
    reference = reference.merge(mad, on=["store_id", "dept_id"], validate="one_to_one")
    reference["prior_robust_scale"] = SCALE_FACTOR * reference.prior_residual_mad
    sales_mad = prior.groupby(["store_id", "dept_id"])["actual_sales"].apply(
        lambda value: float(np.median(np.abs(value - np.median(value))))
    ).rename("prior_sales_mad").reset_index()
    reference = reference.merge(sales_mad, on=["store_id", "dept_id"], validate="one_to_one")
    reference["prior_sales_robust_scale"] = SCALE_FACTOR * reference.prior_sales_mad
    result = block.merge(reference, on=["store_id", "dept_id"], how="left", validate="many_to_one")
    reason = np.where(result.prior_residual_count.fillna(0) < MIN_PRIOR_RESIDUALS, "insufficient_prior_residuals",
             np.where(~np.isfinite(result.prior_robust_scale), "nonfinite_scale",
             np.where(result.prior_robust_scale <= 0, "zero_mad", "")))
    defined = reason == ""
    result["anomaly_score"] = np.where(
        defined, (result.residual - result.prior_residual_median) / result.prior_robust_scale, np.nan
    )
    result["undefined_score_reason"] = reason
    result["direction"] = np.where(~defined, "undefined",
                          np.where(result.anomaly_score > 0, "spike",
                          np.where(result.anomaly_score < 0, "drop", "neutral")))
    return result


def score_blocks_strict(blocks: list[pd.DataFrame], seed: pd.DataFrame) -> list[pd.DataFrame]:
    """Update reference only after each complete block has been scored."""
    prior = seed.copy()
    scored = []
    for block in blocks:
        result = score_block(block, prior)
        scored.append(result)
        prior = pd.concat([prior, block], ignore_index=True)
    return scored
