import unittest

import numpy as np
import pandas as pd

from marketmind.anomalies.evaluation import (
    OUTPUT_COLUMNS, inject_engineered_anomaly, robust_residual_score,
    signed_residual, trailing_median, validate_output,
)
from marketmind.anomalies.splits import (
    ANOMALY_LOCKBOX, DEVELOPMENT_BLOCKS, VALIDATION_BLOCK,
    assert_partition_integrity, development_blocks,
)


class AnomalyMethodologyTests(unittest.TestCase):
    def test_split_chronology_and_no_overlap(self):
        assert_partition_integrity()
        blocks = (*DEVELOPMENT_BLOCKS, VALIDATION_BLOCK, ANOMALY_LOCKBOX)
        days = [day for block in blocks for day in block.score_days]
        self.assertEqual(len(days), len(set(days)))
        self.assertTrue(all(block.train_end < block.score_start for block in blocks))

    def test_development_utility_excludes_lockbox(self):
        blocks = development_blocks()
        self.assertNotIn(ANOMALY_LOCKBOX, blocks)
        self.assertLess(max(day for block in blocks for day in block.score_days), ANOMALY_LOCKBOX.score_start)

    def test_rolling_expectation_uses_past_only(self):
        values = np.arange(1, 8, dtype=float)
        expected = trailing_median(values, window=3)
        self.assertTrue(np.isnan(expected[:3]).all())
        self.assertEqual(expected[3], 2.0)
        changed = values.copy()
        changed[3:] = 999
        self.assertEqual(trailing_median(changed, 3)[3], expected[3])

    def test_signed_residual_direction(self):
        residual = signed_residual([12, 8, 10], [10, 10, 10])
        self.assertEqual(residual.tolist(), [2.0, -2.0, 0.0])

    def test_robust_score_uses_passed_historical_archive(self):
        score = robust_residual_score([5.0], [-2, -1, 0, 1, 2])
        self.assertGreater(score[0], 0)
        self.assertTrue(np.isnan(robust_residual_score([1], [0, 0, 0])[0]))

    def test_engineered_injection_is_deterministic_and_nonnegative(self):
        values = np.array([4.0, 10.0, 20.0])
        first = inject_engineered_anomaly(values, [0, 1], "sustained_drop", 50)
        second = inject_engineered_anomaly(values, [0, 1], "sustained_drop", 50)
        np.testing.assert_array_equal(first, second)
        self.assertTrue((first >= 0).all())
        self.assertEqual(inject_engineered_anomaly(values, [2], "positive_spike", 5)[2], 25)

    def test_future_output_schema(self):
        row = {column: 0 for column in OUTPUT_COLUMNS}
        row.update({"date": "2016-01-01", "store_id": "CA_1", "dept_id": "FOODS_1", "direction": "normal"})
        frame = pd.DataFrame([row])
        validate_output(frame)
        with self.assertRaisesRegex(ValueError, "missing columns"):
            validate_output(frame.drop(columns="residual"))


if __name__ == "__main__":
    unittest.main()
