"""Fast tests for the production forecasting contract."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from marketmind.forecasting.bundle import ForecastModelBundle, load_bundle, save_bundle
from marketmind.forecasting.config import (
    CATEGORICAL_FEATURES, FEATURE_COLUMNS, FORECAST_HORIZON,
    FROZEN_MODEL_PARAMS, MINIMUM_HISTORY, NUMERIC_FEATURES, OUTPUT_COLUMNS,
)
from marketmind.forecasting.predict import forecast


class DummyEncoder:
    def transform(self, frame: pd.DataFrame) -> np.ndarray:
        return np.zeros((len(frame), len(CATEGORICAL_FEATURES)), dtype=np.float32)


class DummyEstimator:
    def predict(self, frame: np.ndarray) -> np.ndarray:
        return np.linspace(-2, 10, len(frame))


def make_bundle() -> ForecastModelBundle:
    return ForecastModelBundle(
        estimator=DummyEstimator(), categorical_encoder=DummyEncoder(),
        feature_columns=FEATURE_COLUMNS, categorical_features=CATEGORICAL_FEATURES,
        numeric_features=NUMERIC_FEATURES, model_params=dict(FROZEN_MODEL_PARAMS),
        feature_schema={column: "fixture" for column in FEATURE_COLUMNS},
        training_cutoff=56, forecast_horizon=FORECAST_HORIZON,
        required_history=MINIMUM_HISTORY,
        series_metadata=[{"state_id": "CA", "store_id": "CA_1", "dept_id": "FOODS_1"}],
        model_version="test", schema_version="test",
        postprocessing="clip predictions below zero to zero",
    )


def make_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    historical_dates = pd.date_range("2020-01-01", periods=56)
    future_dates = pd.date_range("2020-02-26", periods=28)
    history = pd.DataFrame({
        "d": [f"d_{i}" for i in range(1, 57)], "date": historical_dates,
        "store_id": "CA_1", "dept_id": "FOODS_1", "state_id": "CA",
        "sales": np.arange(56, dtype=float),
    })
    future = pd.DataFrame({
        "d": [f"d_{i}" for i in range(57, 85)], "date": future_dates,
        "event_name": "none", "event_type": "none",
        "snap_CA": 0, "snap_TX": 0, "snap_WI": 0,
    })
    return history, future


class ProductionForecastTests(unittest.TestCase):
    def test_frozen_configuration_consistency(self) -> None:
        self.assertEqual(FORECAST_HORIZON, 28)
        self.assertEqual(MINIMUM_HISTORY, 56)
        self.assertEqual(FROZEN_MODEL_PARAMS["max_iter"], 160)
        self.assertEqual(FROZEN_MODEL_PARAMS["max_leaf_nodes"], 63)
        self.assertEqual(FEATURE_COLUMNS, (*CATEGORICAL_FEATURES, *NUMERIC_FEATURES))

    def test_bundle_round_trip_preserves_feature_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.joblib"
            save_bundle(make_bundle(), path)
            loaded = load_bundle(path)
            self.assertEqual(loaded.feature_columns, FEATURE_COLUMNS)
            self.assertEqual(loaded.model_params, FROZEN_MODEL_PARAMS)

    def test_forecast_shape_schema_and_nonnegative_clipping(self) -> None:
        history, future = make_inputs()
        result = forecast(make_bundle(), history, future)
        self.assertEqual(result.shape, (28, 6))
        self.assertEqual(result.columns.tolist(), list(OUTPUT_COLUMNS))
        np.testing.assert_array_equal(result.forecast_horizon, np.arange(1, 29))
        self.assertGreaterEqual(result.predicted_sales.min(), 0)
        self.assertEqual(result.predicted_sales.iloc[0], 0)

    def test_missing_history_column_rejected(self) -> None:
        history, future = make_inputs()
        with self.assertRaisesRegex(ValueError, "missing mandatory columns"):
            forecast(make_bundle(), history.drop(columns="sales"), future)

    def test_duplicate_history_rejected(self) -> None:
        history, future = make_inputs()
        history = pd.concat([history, history.iloc[[0]]], ignore_index=True)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            forecast(make_bundle(), history, future)

    def test_insufficient_history_rejected(self) -> None:
        history, future = make_inputs()
        with self.assertRaisesRegex(ValueError, "at least 56 days"):
            forecast(make_bundle(), history.iloc[1:], future)

    def test_invalid_future_length_rejected(self) -> None:
        history, future = make_inputs()
        with self.assertRaisesRegex(ValueError, "exactly 28"):
            forecast(make_bundle(), history, future.iloc[:-1])

    def test_nonconsecutive_future_calendar_rejected(self) -> None:
        history, future = make_inputs()
        future.loc[27, "date"] += pd.Timedelta(days=1)
        with self.assertRaisesRegex(ValueError, "consecutive and chronological"):
            forecast(make_bundle(), history, future)


if __name__ == "__main__":
    unittest.main()
