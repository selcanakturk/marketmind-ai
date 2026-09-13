"""Point-in-time forecast residual construction for frozen anomaly blocks."""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pandas as pd

from marketmind.anomalies.splits import AnomalyBlock
from marketmind.forecasting.config import CATEGORICAL_FEATURES, FEATURE_COLUMNS, FROZEN_MODEL_PARAMS, NUMERIC_FEATURES
from marketmind.forecasting.dataset import build_prediction_table
from marketmind.forecasting.train import aggregate_core_series, load_training_sources, train_frozen_model

RESIDUAL_COLUMNS = ("block", "d", "date", "store_id", "dept_id", "state_id", "actual_sales", "expected_sales", "residual")


def forecast_residual_block(data_dir: str | Path, block: AnomalyBlock, *, authorize_final_lockbox: bool = False):
    """Fit only through block.train_end and forecast its complete 28-day block."""
    block.validate()
    if block.score_end > 1913 and not authorize_final_lockbox:
        raise ValueError("baseline runner cannot access the anomaly lockbox")
    if authorize_final_lockbox and not (block.train_end == 1913 and block.score_start == 1914 and block.score_end == 1941):
        raise ValueError("final lockbox authorization is restricted to the frozen boundary")
    started = time.perf_counter()
    bundle, stats = train_frozen_model(data_dir, block.train_end)
    sales, calendar = load_training_sources(data_dir, block.train_end)
    series, values = aggregate_core_series(sales, block.train_end)
    features = build_prediction_table(series, values, calendar, block.train_end)
    encoded = np.column_stack([
        bundle.categorical_encoder.transform(features[list(CATEGORICAL_FEATURES)]),
        features[list(NUMERIC_FEATURES)].to_numpy(np.float32),
    ])
    expected = np.clip(bundle.estimator.predict(encoded), 0, None)
    score_days = [f"d_{day}" for day in block.score_days]
    sales_file = "sales_train_evaluation.csv" if block.score_end > 1913 else "sales_train_validation.csv"
    actual_raw = pd.read_csv(Path(data_dir) / sales_file, usecols=["state_id", "store_id", "dept_id", *score_days])
    actual_core = actual_raw.groupby(["state_id", "store_id", "dept_id"], sort=True, observed=True)[score_days].sum().reset_index()
    actual = actual_core[score_days].to_numpy(float).reshape(-1)
    dates = calendar.loc[list(block.score_days), "date"].to_numpy()
    output = pd.DataFrame({
        "block": block.name, "d": np.tile(score_days, len(series)), "date": np.tile(dates, len(series)),
        "store_id": np.repeat(series.store_id.to_numpy(), 28),
        "dept_id": np.repeat(series.dept_id.to_numpy(), 28),
        "state_id": np.repeat(series.state_id.to_numpy(), 28),
        "actual_sales": actual, "expected_sales": expected,
    })
    output["residual"] = output.actual_sales - output.expected_sales
    output = output.sort_values(["date", "store_id", "dept_id"]).reset_index(drop=True)
    provenance = {
        "block": block.name, "forecast_origin": f"d_{block.train_end}", "training_start": "d_1",
        "training_end": f"d_{block.train_end}", "score_start": f"d_{block.score_start}",
        "score_end": f"d_{block.score_end}", "training_rows": stats["training_rows"],
        "feature_specification": "forecasting-v1.0.0 Full Direct",
        "feature_columns": "|".join(FEATURE_COLUMNS), "model_configuration": str(FROZEN_MODEL_PARAMS),
        "forecast_runtime_seconds": time.perf_counter() - started,
    }
    if len(output) != 1960 or not np.allclose(output.residual, output.actual_sales - output.expected_sales):
        raise RuntimeError("invalid OOS residual block")
    return output.loc[:, RESIDUAL_COLUMNS], provenance
