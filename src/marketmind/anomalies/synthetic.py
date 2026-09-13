"""Deterministic engineered anomaly sensitivity cases."""

from __future__ import annotations

import numpy as np
import pandas as pd

FAMILIES = {
    "one_day_positive_spike": (1, 1), "one_day_negative_drop": (1, -1),
    "two_day_positive_sustained_spike": (2, 1), "two_day_negative_sustained_drop": (2, -1),
    "three_day_positive_sustained_spike": (3, 1), "three_day_negative_sustained_drop": (3, -1),
}


def engineered_cases(scored: pd.DataFrame, threshold: int, series_limit: int = 10) -> pd.DataFrame:
    """Inject into actual only; expected and frozen residual scale are copied."""
    required = {"block", "date", "store_id", "dept_id", "actual_sales", "expected_sales",
                "prior_residual_median", "prior_robust_scale", "prior_sales_robust_scale", "anomaly_score"}
    if not required.issubset(scored):
        raise ValueError("scored rows missing engineered-case inputs")
    selected_series = scored[["store_id", "dept_id"]].drop_duplicates().sort_values(["store_id", "dept_id"]).head(series_limit)
    cases = []
    for block_name, block in scored.groupby("block", sort=True):
        dates = sorted(block.date.unique())
        for series_number, key in enumerate(selected_series.itertuples(index=False)):
            group = block[(block.store_id == key.store_id) & (block.dept_id == key.dept_id)].sort_values("date")
            base = 1 + 12 * (series_number % 2)
            offset = 0
            for family, (length, sign) in FAMILIES.items():
                start = base + offset
                offset += length
                window = group.iloc[start:start + length]
                if len(window) != length or window[["prior_robust_scale", "prior_sales_robust_scale"]].isna().any().any():
                    continue
                for magnitude in (2, 4):
                    for position, row in enumerate(window.itertuples(index=False), start=1):
                        delta = magnitude * row.prior_sales_robust_scale
                        injected_actual = max(0.0, row.actual_sales + sign * delta)
                        injected_residual = injected_actual - row.expected_sales
                        injected_score = (injected_residual - row.prior_residual_median) / row.prior_robust_scale
                        cases.append({
                            "block": block_name, "family": family, "magnitude": magnitude,
                            "store_id": row.store_id, "dept_id": row.dept_id, "date": row.date,
                            "window_position": position, "original_actual_sales": row.actual_sales,
                            "injected_actual_sales": injected_actual, "expected_sales": row.expected_sales,
                            "prior_robust_scale": row.prior_robust_scale,
                            "prior_residual_median": row.prior_residual_median,
                            "prior_sales_robust_scale": row.prior_sales_robust_scale,
                            "score_before": row.anomaly_score, "score_after": injected_score,
                            "detected": abs(injected_score) >= threshold,
                            "direction_correct": injected_score > 0 if sign > 0 else injected_score < 0,
                        })
    return pd.DataFrame(cases)
