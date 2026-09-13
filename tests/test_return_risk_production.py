import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from marketmind.return_risk.bundle import ReturnRiskModelBundle, load_bundle, save_bundle
from marketmind.return_risk.config import DEFAULT_CAPACITY, ET2_PARAMETERS, FROZEN_FEATURE_NAMES, MODEL_VERSION, SCHEMA_VERSION, SECONDARY_CAPACITIES, TARGET_HORIZON_DAYS
from marketmind.return_risk.features import baseline_features, build_candidate_features
from marketmind.return_risk.models import make_extra_trees_candidate
from marketmind.return_risk.predict import OUTPUT_COLUMNS, score_return_risk


def _sources(n=20, include_future=True):
    rows = []
    dates = pd.to_datetime(["2019-10-01", "2019-11-01", "2019-12-01", "2020-01-01", "2020-02-10"])
    for household in range(n):
        for i, date in enumerate(dates):
            rows.append({"household_id": household, "store_id": "s", "basket_id": f"{household}-{i}", "product_id": "p1", "sales_value": float(5 + household % 4), "retail_disc": 0.0, "coupon_disc": 0.0, "coupon_match_disc": 0.0, "transaction_timestamp": date})
    for i, date in enumerate(pd.to_datetime(["2019-11-13", "2019-12-01", "2019-12-20", "2020-01-15", "2020-02-10"])):
        rows.append({"household_id": 999, "store_id": "s", "basket_id": f"999-{i}", "product_id": "p1", "sales_value": 5.0, "retail_disc": 0.0, "coupon_disc": 0.0, "coupon_match_disc": 0.0, "transaction_timestamp": date})
    if include_future:
        rows.append({"household_id": 0, "store_id": "s", "basket_id": "future", "product_id": "p1", "sales_value": 999.0, "retail_disc": 0.0, "coupon_disc": 0.0, "coupon_match_disc": 0.0, "transaction_timestamp": pd.Timestamp("2020-02-11")})
    return pd.DataFrame(rows), pd.DataFrame({"product_id": ["p1"], "department": ["D"], "brand": ["B"]})


def _bundle(tx, products):
    X = baseline_features(build_candidate_features(tx, products, "2020-02-10"))
    estimator = make_extra_trees_candidate("ET-2").fit(X, np.arange(len(X)) % 2)
    return ReturnRiskModelBundle(estimator, FROZEN_FEATURE_NAMES, MODEL_VERSION, SCHEMA_VERSION, "2017-11-30T23:59:59", "2017-12-28T23:59:59", [], len(X), TARGET_HORIZON_DAYS, {"min_observed_history_days": 90, "min_baskets": 5, "min_active_span_days": 30}, "uncalibrated ranking score", DEFAULT_CAPACITY, SECONDARY_CAPACITIES, dict(ET2_PARAMETERS), {}, {}, "consumed")


class ReturnRiskProductionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tx, cls.products = _sources()
        cls.bundle = _bundle(cls.tx, cls.products)

    def test_frozen_contract_and_no_calibrator(self):
        self.assertEqual(len(FROZEN_FEATURE_NAMES), 16)
        self.assertEqual(self.bundle.estimator.get_params()["max_depth"], 12)
        self.assertFalse(hasattr(self.bundle, "calibrator"))

    def test_schema_eligibility_score_bounds_and_future_exclusion(self):
        result = score_return_risk(self.tx, self.products, "2020-02-10", self.bundle)
        self.assertEqual(tuple(result.columns), OUTPUT_COLUMNS)
        self.assertEqual(result.eligibility_status.eq("eligible").sum(), 20)
        self.assertTrue(result.loc[result.eligibility_status.eq("eligible"), "risk_score"].between(0, 1).all())
        self.assertTrue(result.loc[result.household_id.eq(999), "risk_score"].isna().all())
        without_future = self.tx.loc[self.tx.basket_id.ne("future")]
        pd.testing.assert_frame_equal(result, score_return_risk(without_future, self.products, "2020-02-10", self.bundle))

    def test_capacity_counts_and_invalid_capacity(self):
        for capacity, expected in ((0.05, 1), (0.10, 2), (0.20, 4)):
            self.assertEqual(score_return_risk(self.tx, self.products, "2020-02-10", self.bundle, capacity).flagged.sum(), expected)
        with self.assertRaises(ValueError):
            score_return_risk(self.tx, self.products, "2020-02-10", self.bundle, 0)

    def test_determinism_and_round_trip(self):
        first = score_return_risk(self.tx, self.products, "2020-02-10", self.bundle)
        second = score_return_risk(self.tx.sample(frac=1, random_state=9), self.products, "2020-02-10", self.bundle)
        pd.testing.assert_frame_equal(first, second)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.joblib"
            save_bundle(self.bundle, path)
            pd.testing.assert_frame_equal(first, score_return_risk(self.tx, self.products, "2020-02-10", load_bundle(path)))


if __name__ == "__main__":
    unittest.main()
