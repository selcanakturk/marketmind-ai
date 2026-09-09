import unittest

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

from marketmind.segmentation.evaluation import evaluate_kmeans, size_summary
from marketmind.segmentation.preprocessing import (
    BOUNDED_RATIO_FEATURES,
    FINAL_FEATURES,
    LOG1P_FEATURES,
    apply_preprocessor,
    prepare_features,
    transform_features,
)


def _frame(rows: int = 4) -> pd.DataFrame:
    values = {}
    for i, feature in enumerate(FINAL_FEATURES):
        if feature in BOUNDED_RATIO_FEATURES:
            values[feature] = np.linspace(0.1, 0.8, rows)
        else:
            values[feature] = np.arange(rows, dtype=float) + i + 1
    return pd.DataFrame(values, index=[f"h{i}" for i in range(rows)])


class SegmentationPreprocessingTests(unittest.TestCase):
    def test_feature_order_and_log1p_policy(self):
        frame = _frame()
        transformed = transform_features(frame[reversed(frame.columns)])
        self.assertEqual(tuple(transformed.columns), FINAL_FEATURES)
        for feature in LOG1P_FEATURES:
            np.testing.assert_allclose(transformed[feature], np.log1p(frame[feature]))

    def test_ratio_features_remain_bounded_and_unchanged(self):
        frame = _frame()
        transformed = transform_features(frame)
        for feature in BOUNDED_RATIO_FEATURES:
            np.testing.assert_allclose(transformed[feature], frame[feature])
            self.assertTrue(transformed[feature].between(0, 1).all())

    def test_fitted_scaler_does_not_refit_on_later_frame(self):
        train = _frame()
        prepared = prepare_features(train)
        center_before = prepared.scaler.center_.copy()
        later = _frame()
        later.loc[:, [c for c in FINAL_FEATURES if c not in BOUNDED_RATIO_FEATURES]] *= 10
        apply_preprocessor(later, prepared.scaler)
        np.testing.assert_array_equal(prepared.scaler.center_, center_before)

    def test_label_permutation_safe_agreement_and_size_shape(self):
        left = np.array([0, 0, 1, 1])
        right = np.array([1, 1, 0, 0])
        self.assertEqual(adjusted_rand_score(left, right), 1.0)
        summary = size_summary(left)
        self.assertEqual(summary["counts"], {0: 2, 1: 2})
        self.assertAlmostEqual(summary["min_share"], 0.5)

    def test_clustering_metrics_reject_wrong_matrix_shape(self):
        with self.assertRaises(ValueError):
            evaluate_kmeans(np.array([1.0, 2.0, 3.0]), 2)


if __name__ == "__main__":
    unittest.main()
