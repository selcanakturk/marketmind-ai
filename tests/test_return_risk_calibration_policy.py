import unittest

import numpy as np
import pandas as pd

from marketmind.return_risk.calibration import CALIBRATION_SNAPSHOT, ScoreCalibrator
from marketmind.return_risk.models import LOCKBOX_SNAPSHOT
from marketmind.return_risk.models import make_extra_trees_candidate
from marketmind.return_risk.features import BASELINE_FEATURE_ORDER
from marketmind.return_risk.policy import (
    freeze_lockbox_scores,
    point_in_time_segment_join,
    threshold_summary,
    top_capacity_flags,
)


class ReturnRiskCalibrationPolicyTests(unittest.TestCase):
    def test_calibration_uses_only_august_and_outputs_valid_scores(self):
        scores = np.linspace(0.01, 0.99, 20)
        target = np.tile([0, 1], 10)
        for method in ("sigmoid", "isotonic"):
            calibrator = ScoreCalibrator(method).fit(
                scores, target, [CALIBRATION_SNAPSHOT] * len(scores)
            )
            result = calibrator.transform(scores)
            self.assertTrue(np.isfinite(result).all())
            self.assertTrue(((result >= 0) & (result <= 1)).all())

    def test_calibration_rejects_non_august_including_lockbox(self):
        for forbidden in (pd.Timestamp("2017-07-31 23:59:59"), LOCKBOX_SNAPSHOT):
            with self.assertRaises(ValueError):
                ScoreCalibrator("sigmoid").fit([0.1, 0.9], [0, 1], [forbidden] * 2)

    def test_sigmoid_preserves_score_ordering(self):
        scores = np.linspace(0.01, 0.99, 20)
        target = np.array([0] * 10 + [1] * 10)
        result = ScoreCalibrator("sigmoid").fit(
            scores, target, [CALIBRATION_SNAPSHOT] * len(scores)
        ).transform(scores)
        self.assertTrue((np.diff(result) > 0).all())

    def test_top_capacity_is_exact_and_deterministic(self):
        first = top_capacity_flags([0.9, 0.8, 0.8, 0.1], 0.5, ["d", "b", "a", "c"])
        second = top_capacity_flags([0.9, 0.8, 0.8, 0.1], 0.5, ["d", "b", "a", "c"])
        np.testing.assert_array_equal(first, second)
        np.testing.assert_array_equal(first, [True, False, True, False])

    def test_threshold_summary_uses_one_as_positive_no_return(self):
        result = threshold_summary([1, 0, 1, 0], [0.9, 0.8, 0.2, 0.1], [0.5]).iloc[0]
        self.assertEqual(result.tp, 1)
        self.assertEqual(result.fp, 1)
        self.assertEqual(result.fn, 1)
        self.assertEqual(result.tn, 1)

    def test_segment_join_requires_same_snapshot(self):
        scores = pd.DataFrame({"household_id": ["h"], "snapshot_at": ["2017-09-30"], "score": [0.7]})
        correct = pd.DataFrame({"household_id": ["h"], "snapshot_date": ["2017-09-30"], "segment_code": ["S"]})
        self.assertEqual(point_in_time_segment_join(scores, correct).segment_code.iloc[0], "S")
        future = correct.assign(snapshot_date="2017-10-31")
        with self.assertRaises(ValueError):
            point_in_time_segment_join(scores, future)

    def test_lockbox_scores_are_frozen_without_target_and_with_exact_model(self):
        rng = np.random.default_rng(42)
        X = pd.DataFrame(
            rng.uniform(size=(40, len(BASELINE_FEATURE_ORDER))),
            columns=BASELINE_FEATURE_ORDER,
            index=[f"h{i:02d}" for i in range(40)],
        )
        model = make_extra_trees_candidate("ET-2").fit(X, np.tile([0, 1], 20))
        frozen = freeze_lockbox_scores(X, model, snapshot_at=LOCKBOX_SNAPSHOT)
        self.assertNotIn("return_risk_target", frozen.columns)
        self.assertEqual(frozen.risk_rank.tolist(), list(range(1, 41)))
        self.assertEqual(int(frozen.top_10_flag.sum()), 4)
        self.assertTrue(frozen.risk_score.between(0, 1).all())
        with self.assertRaises(ValueError):
            freeze_lockbox_scores(
                X.assign(return_risk_target=0), model, snapshot_at=LOCKBOX_SNAPSHOT
            )


if __name__ == "__main__":
    unittest.main()
