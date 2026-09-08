"""Train and export the frozen MarketMind production forecasting model."""

from __future__ import annotations

import argparse
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.preprocessing import OrdinalEncoder

from .bundle import ForecastModelBundle, save_bundle
from .config import (
    CALENDAR_FEATURES, CATEGORICAL_FEATURES, FEATURE_COLUMNS, FORECAST_HORIZON,
    FROZEN_MODEL_PARAMS, LAGS, MINIMUM_HISTORY, MODEL_VERSION, NUMERIC_FEATURES,
    POSTPROCESSING, PRODUCTION_TRAINING_CUTOFF, RESEARCH_TRAINING_CUTOFF,
    ROLLING_WINDOWS, SCHEMA_VERSION, TARGET_DEFINITION,
)
from .dataset import build_training_table, prepare_calendar, weekly_training_origins


def load_training_sources(data_dir: str | Path, cutoff: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load authentic M5 sales through ``cutoff`` and the calendar."""
    directory = Path(data_dir)
    if cutoff < MINIMUM_HISTORY + FORECAST_HORIZON or cutoff > PRODUCTION_TRAINING_CUTOFF:
        raise ValueError(f"cutoff must be between {MINIMUM_HISTORY + FORECAST_HORIZON} and 1941")
    sales_name = "sales_train_validation.csv" if cutoff <= RESEARCH_TRAINING_CUTOFF else "sales_train_evaluation.csv"
    days = [f"d_{day}" for day in range(1, cutoff + 1)]
    sales = pd.read_csv(directory / sales_name, usecols=["dept_id", "store_id", "state_id", *days])
    calendar = prepare_calendar(pd.read_csv(directory / "calendar.csv"))
    return sales, calendar


def aggregate_core_series(sales: pd.DataFrame, cutoff: int) -> tuple[pd.DataFrame, np.ndarray]:
    """Aggregate M5 item-store rows to the frozen 70-series grain."""
    days = [f"d_{day}" for day in range(1, cutoff + 1)]
    core = sales.groupby(["state_id", "store_id", "dept_id"], sort=True, observed=True)[days].sum().reset_index()
    if len(core) != 70 or core[["store_id", "dept_id"]].drop_duplicates().shape[0] != 70:
        raise ValueError("full production training requires exactly 70 department-store series")
    return core[["state_id", "store_id", "dept_id"]], core[days].to_numpy(np.float32)


def train_frozen_model(data_dir: str | Path, cutoff: int = PRODUCTION_TRAINING_CUTOFF) -> tuple[ForecastModelBundle, dict[str, Any]]:
    """Fit the frozen configuration; calculate no evaluation metric."""
    sales, calendar = load_training_sources(data_dir, cutoff)
    series, values = aggregate_core_series(sales, cutoff)
    origins = weekly_training_origins(cutoff, MINIMUM_HISTORY)
    started = time.perf_counter()
    features, target = build_training_table(series, values, calendar, origins)
    build_seconds = time.perf_counter() - started
    encoder = OrdinalEncoder(
        handle_unknown="use_encoded_value", unknown_value=-1,
        encoded_missing_value=-1, dtype=np.float32,
    )
    encoded = np.column_stack([
        encoder.fit_transform(features[list(CATEGORICAL_FEATURES)]),
        features[list(NUMERIC_FEATURES)].to_numpy(np.float32),
    ])
    estimator = HistGradientBoostingRegressor(
        categorical_features=list(range(len(CATEGORICAL_FEATURES))),
        **FROZEN_MODEL_PARAMS,
    )
    started = time.perf_counter()
    estimator.fit(encoded, target)
    fit_seconds = time.perf_counter() - started
    feature_schema = {column: str(features[column].dtype) for column in FEATURE_COLUMNS}
    bundle = ForecastModelBundle(
        estimator=estimator,
        categorical_encoder=encoder,
        feature_columns=FEATURE_COLUMNS,
        categorical_features=CATEGORICAL_FEATURES,
        numeric_features=NUMERIC_FEATURES,
        model_params=dict(FROZEN_MODEL_PARAMS),
        feature_schema=feature_schema,
        training_cutoff=cutoff,
        forecast_horizon=FORECAST_HORIZON,
        required_history=MINIMUM_HISTORY,
        series_metadata=series.to_dict(orient="records"),
        model_version=MODEL_VERSION,
        schema_version=SCHEMA_VERSION,
        postprocessing=POSTPROCESSING,
    )
    stats = {
        "training_origins": int(len(origins)),
        "training_rows": int(len(features)),
        "training_memory_mb": float((features.memory_usage(deep=True).sum() + target.nbytes) / 1024**2),
        "build_seconds": build_seconds,
        "fit_seconds": fit_seconds,
    }
    return bundle, stats


def build_metadata(bundle: ForecastModelBundle, stats: dict[str, Any]) -> dict[str, Any]:
    """Build human-readable metadata without raw M5 observations."""
    return {
        "module": "demand_forecasting",
        "model_name": "MarketMind Frozen Global HGBR",
        "model_family": "sklearn.ensemble.HistGradientBoostingRegressor",
        "model_version": bundle.model_version,
        "schema_version": bundle.schema_version,
        "artifact_role": "production_retrained_artifact",
        "validated_research_candidate": "HGBR-4 Full Direct trained through d_1913",
        "strategy": "global_horizon_conditioned_full_direct",
        "forecast_grain": ["department", "store", "day"],
        "forecast_horizon": bundle.forecast_horizon,
        "research_training_cutoff": "d_1913",
        "production_training_cutoff": f"d_{bundle.training_cutoff}",
        "training_date": datetime.now(timezone.utc).isoformat(),
        "feature_schema": bundle.feature_schema,
        "feature_columns": list(bundle.feature_columns),
        "categorical_features": list(bundle.categorical_features),
        "historical_lags": list(LAGS),
        "rolling_windows": list(ROLLING_WINDOWS),
        "calendar_features": list(CALENDAR_FEATURES),
        "target_definition": TARGET_DEFINITION,
        "postprocessing": bundle.postprocessing,
        "hyperparameters": bundle.model_params,
        "library_versions": {
            "python": platform.python_version(), "numpy": np.__version__,
            "pandas": pd.__version__, "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
        },
        "development_validation_protocol": "six frozen expanding-window 28-day folds within d_1-d_1913",
        "development_metrics": {"macro_rmsse": 0.74604, "macro_mae": 57.35, "pooled_wape": 0.1029, "pooled_bias": -0.0037},
        "final_lockbox_metrics": {"period": "d_1914-d_1941", "macro_rmsse": 0.80073, "macro_mae": 60.13, "pooled_wape": 0.0957, "pooled_bias": -0.0476},
        "lockbox_status": "consumed",
        "training_statistics": stats,
        "known_limitations": [
            "Observed sales are not unconstrained latent demand.",
            "Price features are excluded; future realized prices are never assumed available.",
            "Late-horizon underforecast bias was observed in the consumed lockbox.",
            "Operational inventory state is unavailable.",
            "The model operates at department-store grain.",
            "Production retraining through d_1941 has no new unbiased test estimate.",
        ],
    }


def export_artifacts(bundle: ForecastModelBundle, metadata: dict[str, Any], output_dir: str | Path) -> None:
    """Write the binary bundle and JSON metadata."""
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    save_bundle(bundle, directory / "model.joblib")
    (directory / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw/m5"))
    parser.add_argument("--output-dir", type=Path, default=Path("models/forecasting"))
    parser.add_argument("--training-cutoff", type=int, default=PRODUCTION_TRAINING_CUTOFF)
    args = parser.parse_args()
    bundle, stats = train_frozen_model(args.data_dir, args.training_cutoff)
    metadata = build_metadata(bundle, stats)
    export_artifacts(bundle, metadata, args.output_dir)
    print(f"Trained {metadata['model_name']} through d_{bundle.training_cutoff}: {stats['training_rows']:,} rows")
    print(f"Saved model bundle and metadata to {args.output_dir}")
    print("No production-retraining evaluation metric was calculated.")


if __name__ == "__main__":
    main()
