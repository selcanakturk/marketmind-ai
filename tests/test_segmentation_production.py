import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from marketmind.segmentation.assignment import assign_eligible_households, assign_from_transactions
from marketmind.segmentation.bundle import SegmentationModelBundle, load_bundle, save_bundle
from marketmind.segmentation.config import (
    ASSIGNMENT_OUTPUT_COLUMNS,
    FEATURE_ORDER,
    KMEANS_PARAMETERS,
    LOG_FEATURES,
    SEGMENTS,
    UNCHANGED_FEATURES,
)
from marketmind.segmentation.preprocessing import prepare_features
from marketmind.segmentation.snapshot import build_household_snapshot


def _raw_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    products = pd.DataFrame(
        {
            "product_id": ["p1", "p2", "p3"],
            "department": ["grocery", "produce", "bakery"],
            "brand": ["National", "Private", "National"],
        }
    )
    rows = []
    dates = pd.to_datetime(["2020-01-01", "2020-02-01", "2020-03-01", "2020-03-15", "2020-03-31"])
    for h, multiplier, coupon in [("h1", 1.0, 0.0), ("h2", 10.0, 1.0), ("h3", 5.0, 0.0)]:
        for i, date in enumerate(dates):
            rows.append(
                {
                    "household_id": h,
                    "store_id": "s1",
                    "basket_id": f"{h}-{i}",
                    "product_id": f"p{(i % 3) + 1}",
                    "sales_value": multiplier * (i + 1),
                    "retail_disc": 2.0 if h == "h2" else 0.1,
                    "coupon_disc": coupon,
                    "coupon_match_disc": 0.0,
                    "transaction_timestamp": date,
                }
            )
    rows.append(
        {
            "household_id": "new",
            "store_id": "s1",
            "basket_id": "new-0",
            "product_id": "p1",
            "sales_value": 2.0,
            "retail_disc": 0.0,
            "coupon_disc": 0.0,
            "coupon_match_disc": 0.0,
            "transaction_timestamp": pd.Timestamp("2020-03-31"),
        }
    )
    return pd.DataFrame(rows), products


def _bundle() -> SegmentationModelBundle:
    transactions, products = _raw_inputs()
    snapshot = build_household_snapshot(transactions, products, snapshot_at="2020-04-01 23:59:59")
    prepared = prepare_features(snapshot.features)
    model = KMeans(**KMEANS_PARAMETERS).fit(prepared.scaled)
    codes = list(SEGMENTS)
    mapping = {
        int(cluster): {
            "segment_code": codes[i],
            "display_name": SEGMENTS[codes[i]]["display_name"],
            "description": SEGMENTS[codes[i]]["description"],
        }
        for i, cluster in enumerate(sorted(np.unique(model.labels_)))
    }
    return SegmentationModelBundle(
        scaler=prepared.scaler,
        estimator=model,
        feature_order=FEATURE_ORDER,
        log_features=LOG_FEATURES,
        unchanged_features=UNCHANGED_FEATURES,
        eligibility_policy={"min_observed_history_days": 90, "min_baskets": 5, "min_active_span_days": 30},
        semantic_mapping=mapping,
        model_version="test-v1",
        schema_version="1.0",
        reference_snapshot="2020-04-01 23:59:59",
        kmeans_parameters=dict(KMEANS_PARAMETERS),
        centroid_profiles=[],
        library_versions={"scikit_learn": "test"},
    )


class SegmentationProductionTests(unittest.TestCase):
    def test_bundle_round_trip_preserves_schema_and_semantics(self):
        bundle = _bundle()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.joblib"
            save_bundle(bundle, path)
            loaded = load_bundle(path)
        self.assertEqual(loaded.feature_order, FEATURE_ORDER)
        self.assertEqual(loaded.semantic_mapping, bundle.semantic_mapping)
        self.assertEqual(len({v["segment_code"] for v in loaded.semantic_mapping.values()}), 3)

    def test_assignment_does_not_refit_frozen_objects_and_has_schema(self):
        bundle = _bundle()
        transactions, products = _raw_inputs()
        snapshot = build_household_snapshot(transactions, products, snapshot_at=bundle.reference_snapshot)
        center_before = bundle.scaler.center_.copy()
        centroids_before = bundle.estimator.cluster_centers_.copy()
        result = assign_eligible_households(
            snapshot.features,
            scaler=bundle.scaler,
            model=bundle.estimator,
            semantic_mapping=bundle.semantic_mapping,
            snapshot_date=bundle.reference_snapshot,
        )
        np.testing.assert_array_equal(bundle.scaler.center_, center_before)
        np.testing.assert_array_equal(bundle.estimator.cluster_centers_, centroids_before)
        self.assertEqual(tuple(result.columns), ASSIGNMENT_OUTPUT_COLUMNS)
        self.assertTrue(np.isfinite(result.distance_to_centroid).all())
        self.assertTrue((result.distance_to_centroid >= 0).all())

    def test_raw_assignment_leaves_insufficient_history_null(self):
        bundle = _bundle()
        transactions, products = _raw_inputs()
        result = assign_from_transactions(
            bundle, transactions, products, snapshot_date=bundle.reference_snapshot
        ).set_index("household_id")
        self.assertEqual(result.loc["new", "eligibility_status"], "insufficient_history")
        self.assertTrue(
            result.loc["new", ["cluster_id", "segment_code", "segment_name", "distance_to_centroid"]].isna().all()
        )
        self.assertTrue((result.loc[["h1", "h2", "h3"], "eligibility_status"] == "eligible").all())

    def test_malformed_raw_input_is_rejected(self):
        bundle = _bundle()
        transactions, products = _raw_inputs()
        with self.assertRaisesRegex(ValueError, "missing required columns"):
            assign_from_transactions(
                bundle,
                transactions.drop(columns="sales_value"),
                products,
                snapshot_date=bundle.reference_snapshot,
            )

    def test_all_new_population_returns_only_insufficient_history(self):
        bundle = _bundle()
        transactions, products = _raw_inputs()
        only_new = transactions.query("household_id == 'new'")
        result = assign_from_transactions(
            bundle, only_new, products, snapshot_date=bundle.reference_snapshot
        )
        self.assertEqual(result.loc[0, "eligibility_status"], "insufficient_history")
        self.assertTrue(result.loc[0, ["cluster_id", "segment_code", "segment_name", "distance_to_centroid"]].isna().all())


if __name__ == "__main__":
    unittest.main()
