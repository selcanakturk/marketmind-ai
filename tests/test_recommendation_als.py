import unittest

import numpy as np
import pandas as pd

from marketmind.recommendations.als import ALS_CONFIGS, fit_als, recommend_als
from marketmind.recommendations.evaluation import recall_at_k


def _events():
    return pd.DataFrame({
        "visitorid": [1, 1, 1, 2, 2, 3, 3, 4, 4],
        "itemid": [10, 10, 20, 10, 30, 20, 40, 30, 40],
        "timestamp": [1, 2, 3, 1, 2, 1, 2, 1, 2],
    })


class RecommendationALSTests(unittest.TestCase):
    def test_binary_matrix_and_deterministic_mappings(self):
        model = fit_als(_events(), "ALS-1")
        self.assertEqual(model.interaction_matrix.nnz, 8)
        self.assertEqual(model.visitor_ids.tolist(), [1, 2, 3, 4])
        self.assertEqual(model.item_ids.tolist(), [10, 20, 30, 40])
        self.assertTrue(np.isfinite(model.estimator.user_factors).all())
        self.assertTrue(np.isfinite(model.estimator.item_factors).all())

    def test_only_three_predeclared_configs(self):
        self.assertEqual(tuple(ALS_CONFIGS), ("ALS-1", "ALS-2", "ALS-3"))

    def test_unknown_visitor_falls_back_and_unknown_items_are_fill_only(self):
        model = fit_als(_events(), "ALS-1")
        ranking, diagnostic = recommend_als(model, 999, [10, 20, 30, 40, 99], [99, 40, 30, 20, 10], k=5)
        self.assertEqual(ranking, [99, 40, 30, 20, 10])
        self.assertEqual(diagnostic["complete_popularity_fallback"], 1.0)

    def test_seen_items_allowed_no_duplicates_and_candidate_safety(self):
        model = fit_als(_events(), "ALS-1")
        ranking, _ = recommend_als(model, 1, [10, 20, 30, 40], [40, 30, 20, 10], k=4)
        self.assertIn(10, ranking)
        self.assertEqual(len(ranking), len(set(ranking)))
        self.assertNotIn(99, ranking)

    def test_validation_event_excluded_and_reproducible_seed(self):
        future = pd.concat([_events(), pd.DataFrame({"visitorid": [1], "itemid": [99], "timestamp": [100]})])
        first = fit_als(future.loc[future.timestamp < 100], "ALS-1")
        second = fit_als(_events(), "ALS-1")
        a, _ = recommend_als(first, 1, [10, 20, 30, 40], [10, 20, 30, 40], k=4)
        b, _ = recommend_als(second, 1, [10, 20, 30, 40], [10, 20, 30, 40], k=4)
        self.assertEqual(a, b)
        self.assertNotIn(99, a)

    def test_cold_target_remains_miss_and_topk_length_valid(self):
        model = fit_als(_events(), "ALS-1")
        ranking, _ = recommend_als(model, 1, [10, 20, 30, 40], [10, 20, 30, 40], k=4)
        self.assertEqual(len(ranking), 4)
        self.assertEqual(recall_at_k(ranking, 99, 4), 0.0)


if __name__ == "__main__":
    unittest.main()
