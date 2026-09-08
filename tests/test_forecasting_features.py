"""Alignment tests for leakage-sensitive forecast feature construction."""

import unittest

import numpy as np
import pandas as pd

from marketmind.forecasting.dataset import (
    build_prediction_table,
    build_one_step_prediction_table,
    build_one_step_training_table,
    build_training_table,
    prepare_calendar,
    weekly_training_origins,
)
from marketmind.forecasting.features import historical_features


class ForecastFeatureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.values = np.vstack([np.arange(1, 101), np.arange(101, 201)])
        self.series = pd.DataFrame({
            "store_id": ["CA_1", "TX_1"], "dept_id": ["A", "B"], "state_id": ["CA", "TX"]
        })
        dates = pd.date_range("2020-01-01", periods=130)
        self.calendar = prepare_calendar(pd.DataFrame({
            "d": [f"d_{i}" for i in range(1, 131)], "date": dates,
            "event_name_1": [None] * 130, "event_type_1": [None] * 130,
            "snap_CA": np.arange(130) % 2, "snap_TX": (np.arange(130) + 1) % 2,
            "snap_WI": np.zeros(130),
        }))

    def test_lag_and_rolling_alignment(self) -> None:
        features = historical_features(self.values, 60)
        self.assertEqual(features["lag_1"][0], 60)
        self.assertEqual(features["lag_7"][0], 54)
        self.assertEqual(features["lag_56"][0], 5)
        self.assertEqual(features["rolling_mean_7"][0], np.mean(np.arange(54, 61)))
        self.assertEqual(features["rolling_mean_28"][0], np.mean(np.arange(33, 61)))

    def test_target_and_calendar_alignment(self) -> None:
        features, target = build_training_table(self.series, self.values, self.calendar, [60])
        self.assertEqual(len(features), 2 * 28)
        np.testing.assert_array_equal(target[:28], np.arange(61, 89))
        self.assertEqual(features.iloc[0].day_index, 61)
        self.assertEqual(features.iloc[27].day_index, 88)
        self.assertEqual(features.iloc[0].day_of_week, self.calendar.at[61, "date"].dayofweek)

    def test_historical_features_do_not_change_with_future_values(self) -> None:
        altered = self.values.copy()
        altered[:, 60:] = -9999
        original = historical_features(self.values, 60)
        changed = historical_features(altered, 60)
        for name in original:
            np.testing.assert_array_equal(original[name], changed[name])

    def test_prediction_table_has_28_steps_per_series(self) -> None:
        features = build_prediction_table(self.series, self.values[:, :60], self.calendar, 60)
        self.assertEqual(len(features), 56)
        np.testing.assert_array_equal(features.forecast_horizon[:28], np.arange(1, 29))

    def test_weekly_origins_leave_targets_in_training(self) -> None:
        origins = weekly_training_origins(100)
        self.assertTrue(np.all(np.diff(origins) == 7))
        self.assertLessEqual(origins.max() + 28, 100)
        self.assertGreaterEqual(origins.min(), 56)

    def test_one_step_target_and_calendar_alignment(self) -> None:
        features, target = build_one_step_training_table(self.series, self.values, self.calendar, [60])
        np.testing.assert_array_equal(target, [61, 161])
        self.assertTrue((features.day_index == 61).all())
        prediction = build_one_step_prediction_table(self.series, self.values[:, :60], self.calendar, 60)
        self.assertEqual(len(prediction), 2)


if __name__ == "__main__":
    unittest.main()
