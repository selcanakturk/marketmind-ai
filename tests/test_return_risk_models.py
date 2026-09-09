import unittest

import numpy as np
import pandas as pd

from marketmind.return_risk.features import BASELINE_FEATURE_ORDER
from marketmind.return_risk.models import (
    HGB_CANDIDATE_PARAMETERS,
    LOCKBOX_SNAPSHOT,
    TRAINING_SNAPSHOTS,
    VALIDATION_SNAPSHOTS,
    fit_hgb_candidate,
    make_hgb_candidate,
)


def _features(n=40):
    rng = np.random.default_rng(42)
    return pd.DataFrame(
        rng.uniform(0, 2, size=(n, len(BASELINE_FEATURE_ORDER))),
        columns=BASELINE_FEATURE_ORDER,
    )


class ReturnRiskModelTests(unittest.TestCase):
    def test_exactly_five_candidate_parameter_sets_are_deterministic(self):
        self.assertEqual(tuple(HGB_CANDIDATE_PARAMETERS), ("HGB-1", "HGB-2", "HGB-3", "HGB-4", "HGB-5"))
        for name, expected in HGB_CANDIDATE_PARAMETERS.items():
            first, second = make_hgb_candidate(name), make_hgb_candidate(name)
            self.assertEqual(first.get_params(), second.get_params())
            for parameter, value in expected.items():
                self.assertEqual(first.get_params()[parameter], value)

    def test_fit_accepts_training_snapshots_and_scores_are_valid(self):
        X = _features()
        y = np.tile([0, 1], 20)  # 1 remains the no-return positive class.
        model = fit_hgb_candidate("HGB-1", X, y, [TRAINING_SNAPSHOTS[0]] * len(X))
        scores = model.predict_proba(X.iloc[:7])[:, 1]
        self.assertEqual(scores.shape, (7,))
        self.assertTrue(np.isfinite(scores).all())
        self.assertTrue(((scores >= 0) & (scores <= 1)).all())

    def test_fit_rejects_validation_and_lockbox_snapshots(self):
        X = _features()
        y = np.tile([0, 1], 20)
        for forbidden in (*VALIDATION_SNAPSHOTS, LOCKBOX_SNAPSHOT):
            with self.assertRaises(ValueError):
                fit_hgb_candidate("HGB-1", X, y, [forbidden] * len(X))

    def test_feature_order_must_remain_frozen(self):
        X = _features()[list(reversed(BASELINE_FEATURE_ORDER))]
        with self.assertRaises(ValueError):
            fit_hgb_candidate("HGB-1", X, np.tile([0, 1], 20), [TRAINING_SNAPSHOTS[0]] * len(X))


if __name__ == "__main__":
    unittest.main()
