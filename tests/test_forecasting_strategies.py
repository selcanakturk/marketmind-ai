"""Tests proving recursive forecasts append predictions, never actuals."""

import unittest

import numpy as np

from marketmind.forecasting.features import historical_features
from marketmind.forecasting.strategies import recursive_forecast


class RecursiveStrategyTests(unittest.TestCase):
    def test_predictions_replace_unknown_future_and_keep_alignment(self) -> None:
        observed = np.arange(1, 61, dtype=float)[None, :]
        forbidden_actuals = np.array([999.0, 998.0, 997.0])
        histories = []

        def predictor(history: np.ndarray, horizon: int) -> np.ndarray:
            histories.append(history.copy())
            features = historical_features(history, history.shape[1])
            self.assertEqual(features["lag_1"][0], history[0, -1])
            self.assertEqual(features["rolling_mean_7"][0], history[0, -7:].mean())
            return np.array([100.0 + horizon])

        result = recursive_forecast(observed, 3, predictor)
        np.testing.assert_array_equal(result, [[101.0, 102.0, 103.0]])
        self.assertEqual(histories[1][0, -1], 101.0)
        self.assertEqual(histories[2][0, -1], 102.0)
        self.assertFalse(any(np.isin(history, forbidden_actuals).any() for history in histories))

    def test_output_has_exactly_28_steps_per_series(self) -> None:
        observed = np.ones((2, 56))
        result = recursive_forecast(observed, 28, lambda history, horizon: np.array([horizon, horizon]))
        self.assertEqual(result.shape, (2, 28))


if __name__ == "__main__":
    unittest.main()
