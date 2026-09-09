import unittest

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from marketmind.segmentation.alignment import (
    align_to_reference,
    remap_labels,
    semantic_mapping_from_profiles,
)
from marketmind.segmentation.assignment import (
    assign_eligible_households,
    eligibility_status,
)
from marketmind.segmentation.preprocessing import FINAL_FEATURES, prepare_features


class AlignmentAssignmentTests(unittest.TestCase):
    def test_alignment_handles_label_permutation(self):
        reference = pd.DataFrame([[0, 0], [3, 3], [8, 8]], index=[0, 1, 2], columns=["a", "b"])
        candidate = reference.rename(index={0: 2, 1: 0, 2: 1}).sort_index()
        mapping, _ = align_to_reference(candidate, reference)
        labels = np.array([0, 1, 2])
        np.testing.assert_array_equal(remap_labels(labels, mapping), [1, 2, 0])

    def test_semantics_depend_on_profiles_not_raw_ids(self):
        profiles = pd.DataFrame(
            {"basket_frequency": [20, 80, 40], "coupon_basket_rate": [0.0, 0.1, 0.5]},
            index=[91, 7, 42],
        )
        mapping = semantic_mapping_from_profiles(profiles)
        self.assertEqual(mapping[7].segment_code, "HIGH_ENGAGEMENT_BROAD")
        self.assertEqual(mapping[42].segment_code, "PROMOTION_BASKET_BUILDERS")
        self.assertEqual(mapping[91].segment_code, "LOWER_ENGAGEMENT_FOCUSED")

    def test_insufficient_history_is_not_assigned_as_segment(self):
        self.assertEqual(
            eligibility_status(observed_history_days=89, basket_count=20, active_span_days=80),
            "insufficient_history",
        )
        self.assertEqual(
            eligibility_status(observed_history_days=90, basket_count=5, active_span_days=30),
            "eligible",
        )

    def test_assignment_order_and_distance_contract(self):
        frame = pd.DataFrame(
            {feature: np.linspace(i + 1, i + 5, 5) for i, feature in enumerate(FINAL_FEATURES)},
            index=[f"h{i}" for i in range(5)],
        )
        for feature in ("department_spend_hhi", "discount_share_of_gross", "coupon_basket_rate", "private_label_spend_share"):
            frame[feature] = np.linspace(0.1, 0.5, 5)
        prepared = prepare_features(frame)
        model = KMeans(n_clusters=3, n_init=20, random_state=42).fit(prepared.scaled)
        profiles = frame.assign(cluster=model.labels_).groupby("cluster").median()
        mapping = semantic_mapping_from_profiles(profiles)
        assigned = assign_eligible_households(
            frame.loc[:, reversed(frame.columns)],
            scaler=prepared.scaler,
            model=model,
            semantic_mapping=mapping,
            snapshot_date="2020-01-31",
        )
        self.assertEqual(list(assigned.household_id), list(frame.index))
        self.assertTrue(np.isfinite(assigned.distance_to_centroid).all())
        self.assertTrue((assigned.distance_to_centroid >= 0).all())


if __name__ == "__main__":
    unittest.main()
