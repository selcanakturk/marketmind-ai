import unittest

import numpy as np
import pandas as pd

from marketmind.return_risk.evaluation import capacity_metrics
from marketmind.return_risk.features import (
    BASELINE_FEATURE_ORDER,
    LOG1P_FEATURES,
    baseline_features,
    build_candidate_features,
    make_logistic_preprocessor,
)


def _sources():
    rows = []
    dates = ["2019-11-01", "2019-12-01", "2020-01-15", "2020-02-04"]
    for household in ("a", "b"):
        for i, date in enumerate(dates):
            rows.append({
                "household_id": household,
                "store_id": "s",
                "basket_id": f"{household}-{i}",
                "product_id": "p1" if i % 2 == 0 else "p2",
                "sales_value": 10.0,
                "retail_disc": 1.0,
                "coupon_disc": 0.0,
                "coupon_match_disc": 0.0,
                "transaction_timestamp": pd.Timestamp(date),
            })
    # Snapshot-day history, exact window boundaries, and forbidden future target row.
    for basket, date in [("a-t56", "2019-12-16"), ("a-t28", "2020-01-13"),
                         ("a-t14", "2020-01-27"), ("a-t7", "2020-02-03"),
                         ("a-t", "2020-02-10"), ("a-future", "2020-02-11")]:
        rows.append({
            "household_id": "a", "store_id": "s", "basket_id": basket,
            "product_id": "p1", "sales_value": 10.0, "retail_disc": 0.0,
            "coupon_disc": 0.0, "coupon_match_disc": 0.0,
            "transaction_timestamp": pd.Timestamp(date),
        })
    products = pd.DataFrame({
        "product_id": ["p1", "p2"], "department": ["D1", "D2"],
        "brand": ["National", "Private"],
    })
    return pd.DataFrame(rows), products


class ReturnRiskFeatureEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tx, products = _sources()
        cls.features = build_candidate_features(tx, products, "2020-02-10")

    def test_window_boundaries_and_snapshot_day_are_history(self):
        a = self.features.loc["a"]
        self.assertEqual(a.baskets_last_7d, 2)   # Feb 4 and Feb 10; Feb 3 excluded
        self.assertEqual(a.baskets_last_14d, 3)  # Jan 27 excluded; open left
        self.assertEqual(a.baskets_last_28d, 5)  # Jan 13 excluded; Jan 15 included
        self.assertEqual(a.baskets_last_56d, 6)  # Dec 16 excluded; open left
        self.assertEqual(a.recency_days, 0)

    def test_future_target_transaction_never_enters_features(self):
        tx, products = _sources()
        without_future = tx.loc[tx.basket_id.ne("a-future")]
        expected = build_candidate_features(without_future, products, "2020-02-10")
        pd.testing.assert_frame_equal(self.features, expected)

    def test_previous_window_and_recent_window_do_not_overlap(self):
        a = self.features.loc["a"]
        # T-56 is excluded, T-28 is previous, and recent starts strictly after it.
        self.assertEqual(a.baskets_28d_change, 4)

    def test_zero_denominator_features_are_finite(self):
        self.assertTrue(np.isfinite(self.features.to_numpy()).all())

    def test_frozen_feature_order_is_deterministic(self):
        selected = baseline_features(self.features)
        self.assertEqual(tuple(selected.columns), BASELINE_FEATURE_ORDER)

    def test_scaler_is_fit_only_from_passed_training_data(self):
        train = pd.DataFrame(np.ones((3, len(BASELINE_FEATURE_ORDER))), columns=BASELINE_FEATURE_ORDER)
        validation = pd.DataFrame(np.full((2, len(BASELINE_FEATURE_ORDER)), 1e9), columns=BASELINE_FEATURE_ORDER)
        pipeline = make_logistic_preprocessor().fit(train)
        transformed_train = train.copy()
        transformed_train.loc[:, LOG1P_FEATURES] = np.log1p(transformed_train.loc[:, LOG1P_FEATURES])
        np.testing.assert_allclose(pipeline.named_steps["scale"].center_, transformed_train.median().to_numpy())
        pipeline.transform(validation)  # transform-only; does not alter fitted center
        np.testing.assert_allclose(pipeline.named_steps["scale"].center_, transformed_train.median().to_numpy())

    def test_capacity_selects_exact_highest_scores(self):
        result = capacity_metrics([1, 0, 1, 0], [0.9, 0.8, 0.1, 0.0], fractions=(0.5,))
        self.assertEqual(result.loc[0, "selected"], 2)
        self.assertEqual(result.loc[0, "positives_captured"], 1)
        self.assertEqual(result.loc[0, "precision"], 0.5)
        self.assertEqual(result.loc[0, "recall"], 0.5)


if __name__ == "__main__":
    unittest.main()
