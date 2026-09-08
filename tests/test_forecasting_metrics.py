"""Focused tests for the frozen forecasting metric definitions."""

import unittest

import numpy as np

from marketmind.forecasting.metrics import forecast_bias, mae, rmsse, wape


class ForecastingMetricTests(unittest.TestCase):
    def test_perfect_forecast(self) -> None:
        actual = [1, 2, 3]
        self.assertEqual(mae(actual, actual), 0.0)
        self.assertEqual(wape(actual, actual), 0.0)
        self.assertEqual(forecast_bias(actual, actual), 0.0)
        self.assertEqual(rmsse(actual, actual, [1, 2, 4, 3]), 0.0)

    def test_overforecast_has_positive_bias(self) -> None:
        self.assertEqual(forecast_bias([1, 2, 3], [2, 3, 4]), 0.5)

    def test_underforecast_has_negative_bias(self) -> None:
        self.assertEqual(forecast_bias([2, 2], [1, 1]), -0.5)

    def test_zero_actual_total_makes_ratio_metrics_undefined(self) -> None:
        self.assertTrue(np.isnan(wape([0, 0], [1, 0])))
        self.assertTrue(np.isnan(forecast_bias([0, 0], [1, 0])))

    def test_zero_rmsse_scale_is_undefined(self) -> None:
        self.assertTrue(np.isnan(rmsse([1, 2], [1, 1], [3, 3, 3])))

    def test_normal_nonzero_example(self) -> None:
        actual, forecast, training = [2, 4], [1, 5], [1, 2, 4]
        self.assertTrue(np.isclose(rmsse(actual, forecast, training), np.sqrt(1 / 2.5)))
        self.assertEqual(mae(actual, forecast), 1.0)
        self.assertTrue(np.isclose(wape(actual, forecast), 2 / 6))

    def test_shape_mismatch_raises(self) -> None:
        with self.assertRaises(ValueError):
            mae([1, 2], [1])


if __name__ == "__main__":
    unittest.main()
