import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from marketmind.anomalies.baseline_experiment import run_validation
from marketmind.anomalies.policy import fixed_threshold, top_n_per_day
from marketmind.anomalies.scoring import SCALE_FACTOR, score_block, score_blocks_strict
from marketmind.anomalies.splits import ANOMALY_LOCKBOX
from marketmind.anomalies.synthetic import engineered_cases
from marketmind.anomalies.residuals import forecast_residual_block


def _block(name, residuals, actual=None):
    n = len(residuals)
    actual = np.asarray(actual if actual is not None else np.arange(10, 10 + n), dtype=float)
    return pd.DataFrame({
        "block": name, "date": pd.date_range("2020-01-01", periods=n),
        "store_id": "CA_1", "dept_id": "FOODS_1", "state_id": "CA",
        "actual_sales": actual, "expected_sales": actual - np.asarray(residuals), "residual": residuals,
    })


class AnomalyResidualBaselineTests(unittest.TestCase):
    def test_median_mad_factor_and_residual_sign(self):
        prior = _block("seed", list(range(28)))
        current = _block("dev", [30])
        scored = score_block(current, prior).iloc[0]
        expected_mad = np.median(np.abs(np.arange(28) - np.median(np.arange(28))))
        self.assertEqual(scored.prior_residual_median, 13.5)
        self.assertEqual(scored.prior_residual_mad, expected_mad)
        self.assertAlmostEqual(scored.prior_robust_scale, SCALE_FACTOR * expected_mad)
        self.assertGreater(scored.anomaly_score, 0)

    def test_current_and_future_blocks_excluded_then_whole_block_update(self):
        seed = _block("seed", list(range(28)))
        first = _block("first", [100, -100])
        future = _block("future", [10000])
        scored_first, scored_future = score_blocks_strict([first, future], seed)
        self.assertTrue((scored_first.prior_residual_count == 28).all())
        self.assertTrue((scored_future.prior_residual_count == 30).all())
        self.assertEqual(scored_first.prior_residual_median.nunique(), 1)

    def test_zero_mad_is_undefined_and_not_alerted(self):
        scored = score_block(_block("dev", [1]), _block("seed", [0] * 28))
        self.assertTrue(scored.anomaly_score.isna().all())
        self.assertEqual(scored.undefined_score_reason.iloc[0], "zero_mad")
        self.assertFalse(fixed_threshold(scored, 3).any())

    def test_fixed_threshold_and_top_n_deterministic_ties(self):
        frame = pd.DataFrame({
            "date": ["2020-01-01"] * 4, "store_id": ["TX_1", "CA_2", "CA_1", "WI_1"],
            "dept_id": ["A", "A", "B", "A"], "anomaly_score": [4, -4, 4, 1],
        })
        self.assertEqual(fixed_threshold(frame, 4).tolist(), [True, True, True, False])
        # top-5 is the smallest allowed capacity; pad to verify stable selection ordering.
        padded = pd.concat([frame, pd.DataFrame({"date": ["2020-01-01"] * 2, "store_id": ["ZZ", "ZY"], "dept_id": ["A", "A"], "anomaly_score": [0.5, 0.4]})], ignore_index=True)
        mask = top_n_per_day(padded, 5)
        self.assertEqual(mask.sum(), 5)
        tied = padded.loc[mask & padded.anomaly_score.abs().eq(4), "store_id"].tolist()
        self.assertEqual(set(tied), {"TX_1", "CA_2", "CA_1"})

    def test_synthetic_changes_actual_only_preserves_scale_and_window_lengths(self):
        prior = _block("seed", list(range(28)))
        scored = score_block(_block("dev", np.linspace(-2, 2, 28), actual=np.arange(50, 78)), prior)
        unchanged = scored.copy(deep=True)
        cases = engineered_cases(scored, 3, series_limit=1)
        pd.testing.assert_frame_equal(scored, unchanged)
        self.assertTrue((cases.prior_robust_scale > 0).all())
        self.assertTrue((cases.injected_actual_sales >= 0).all())
        lengths = cases.groupby(["family", "magnitude"]).size()
        self.assertEqual(lengths["one_day_positive_spike", 2], 1)
        self.assertEqual(lengths["two_day_positive_sustained_spike", 2], 2)
        self.assertEqual(lengths["three_day_positive_sustained_spike", 2], 3)
        starts = cases[cases.magnitude == 2].groupby("family").date.agg(["min", "max"])
        windows = [set(pd.date_range(row["min"], row["max"])) for _, row in starts.iterrows()]
        self.assertTrue(all(not windows[i].intersection(windows[j]) for i in range(len(windows)) for j in range(i + 1, len(windows))))

    def test_lockbox_and_unfrozen_validation_are_inaccessible(self):
        with self.assertRaisesRegex(ValueError, "lockbox"):
            forecast_residual_block("does-not-matter", ANOMALY_LOCKBOX)
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError, "frozen"):
                run_validation(Path(directory), 3, 5)


if __name__ == "__main__":
    unittest.main()
