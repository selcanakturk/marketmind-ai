import json
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from marketmind.anomalies.lockbox_experiment import (
    IF_CONFIG, REFERENCE_BLOCKS, REVIEW_CAPACITY, ROBUST_THRESHOLD,
    build_reference, complete_evaluation,
)
from marketmind.anomalies.isolation_forest import CONFIGURATIONS


class AnomalyLockboxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).parents[1]
        cls.artifacts = cls.root / "reports/anomalies/artifacts"
        cls.authentic_path = cls.artifacts / "lockbox_robust_scores_authentic.csv"
        cls.synthetic_path = cls.artifacts / "lockbox_synthetic_confirmation.csv"
        cls.authentic = pd.read_csv(cls.authentic_path, parse_dates=["date"])
        cls.synthetic = pd.read_csv(cls.synthetic_path, parse_dates=["date"])
        cls.metadata = json.loads((cls.artifacts / "lockbox_evaluation_metadata.json").read_text())

    def test_forecast_cutoff_boundary_and_row_count(self):
        self.assertEqual(self.metadata["forecast_training_cutoff"], "d_1913")
        self.assertEqual(self.metadata["scored_start"], "d_1914")
        self.assertEqual(len(self.authentic), 1960)
        days = self.authentic.d.str.removeprefix("d_").astype(int)
        self.assertEqual((days.min(), days.max()), (1914, 1941))

    def test_prelockbox_reference_exact_and_excludes_lockbox(self):
        residuals = pd.read_csv(self.artifacts / "oos_residual_blocks.csv")
        reference = build_reference(residuals)
        self.assertEqual(len(reference), 11760)
        self.assertEqual(tuple(REFERENCE_BLOCKS), tuple(reference.block.drop_duplicates()))
        self.assertLessEqual(reference.d.str.removeprefix("d_").astype(int).max(), 1913)

    def test_entire_lockbox_uses_one_frozen_series_scale(self):
        counts = self.authentic.groupby(["store_id", "dept_id"])[
            ["prior_residual_median", "prior_residual_mad", "prior_robust_scale"]
        ].nunique()
        self.assertTrue((counts == 1).all().all())
        self.assertEqual(self.authentic.anomaly_score.isna().sum(), 0)

    def test_threshold_review_capacity_and_order_are_frozen(self):
        self.assertEqual(ROBUST_THRESHOLD, 3)
        self.assertEqual(REVIEW_CAPACITY, 5)
        expected = self.authentic.anomaly_score.abs().ge(3)
        self.assertTrue((expected == self.authentic.is_statistical_alert).all())
        review = self.authentic[self.authentic.is_daily_review_candidate]
        self.assertTrue((review.groupby("date").size() == 5).all())
        for _, group in self.authentic.groupby("date"):
            expected_ids = group.assign(a=group.anomaly_score.abs()).sort_values(
                ["a", "store_id", "dept_id"], ascending=[False, True, True]
            ).head(5)[["store_id", "dept_id"]].apply(tuple, axis=1).tolist()
            actual_ids = group[group.daily_review_rank <= 5].sort_values("daily_review_rank")[["store_id", "dept_id"]].apply(tuple, axis=1).tolist()
            self.assertEqual(actual_ids, expected_ids)

    def test_if_config_unchanged(self):
        self.assertEqual(IF_CONFIG, "IF-3")
        self.assertEqual(self.metadata["if_parameters"], CONFIGURATIONS["IF-3"])

    def test_authentic_was_frozen_before_separate_synthetic_artifact(self):
        self.assertTrue(self.authentic_path.exists() and self.synthetic_path.exists())
        self.assertLessEqual(self.authentic_path.stat().st_mtime_ns, self.synthetic_path.stat().st_mtime_ns)
        self.assertNotIn("synthetic", self.authentic.columns)
        self.assertTrue(self.synthetic.synthetic.all())

    def test_synthetic_changes_actual_only_not_expected_or_scale(self):
        keys = ["block", "store_id", "dept_id", "date"]
        authentic = self.authentic.rename(columns={"expected_sales": "auth_expected", "prior_robust_scale": "auth_scale"})
        joined = self.synthetic.merge(authentic[keys + ["auth_expected", "auth_scale"]], on=keys, validate="many_to_one")
        self.assertTrue(np.allclose(joined.expected_sales, joined.auth_expected))
        self.assertTrue(np.allclose(joined.prior_robust_scale, joined.auth_scale))
        self.assertTrue((joined.injected_actual_sales >= 0).all())

    def test_consumed_metadata_is_final_and_blocks_updates(self):
        self.assertEqual(self.metadata["lockbox_status"], "consumed")
        self.assertFalse(self.metadata["configuration_mutable"])
        with self.assertRaisesRegex(RuntimeError, "permanently consumed"):
            complete_evaluation(self.root / "data/raw/m5", self.artifacts)


if __name__ == "__main__":
    unittest.main()
