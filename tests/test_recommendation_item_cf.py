import unittest

import numpy as np
import pandas as pd

from marketmind.recommendations.evaluation import recall_at_k
from marketmind.recommendations.item_cf import build_binary_interactions, fit_item_cf, recommend


def _training():
    return pd.DataFrame({
        "visitorid": [1, 1, 1, 2, 2, 3, 3, 3],
        "itemid": [10, 10, 20, 10, 30, 20, 30, 40],
        "timestamp": [1, 2, 3, 1, 2, 1, 2, 3],
    })


class RecommendationItemCFTests(unittest.TestCase):
    def test_binary_matrix_collapses_repeated_events(self):
        matrix, visitors, items = build_binary_interactions(_training())
        self.assertEqual(matrix.shape, (3, 4))
        self.assertEqual(matrix.nnz, 7)
        self.assertTrue(np.array_equal(matrix.data, np.ones(7)))

    def test_known_cosine_and_training_only_fit(self):
        model = fit_item_cf(_training(), 200)
        item_index = model.item_to_index
        source = item_index[10]
        indices, values = model.neighbors[source]
        similarities = dict(zip(model.item_ids[indices], values))
        self.assertAlmostEqual(float(similarities[20]), 0.5)
        self.assertAlmostEqual(float(similarities[30]), 0.5)
        changed = pd.concat([_training(), pd.DataFrame({"visitorid": [9], "itemid": [99], "timestamp": [999]})])
        unchanged = fit_item_cf(changed.loc[changed.timestamp < 999], 200)
        self.assertNotIn(99, unchanged.item_to_index)
        self.assertEqual(model.neighbors[source][0].tolist(), unchanged.neighbors[source][0].tolist())

    def test_seen_items_allowed_ties_fallback_and_no_duplicates(self):
        model = fit_item_cf(_training(), 200)
        ranking, diagnostics = recommend(model, [10], [40, 30, 20, 10], neighbors=50, k=4)
        self.assertEqual(ranking[0], 10)  # self-similarity; seen items remain valid
        self.assertLess(ranking.index(20), ranking.index(30))  # equal similarity, item ID tie
        self.assertEqual(len(ranking), len(set(ranking)))
        fallback, status = recommend(model, [999], [40, 30, 20, 10], neighbors=50, k=4)
        self.assertEqual(fallback, [40, 30, 20, 10])
        self.assertEqual(status["complete_popularity_fallback"], 1.0)

    def test_future_input_cannot_change_earlier_model_or_ranking(self):
        all_events = pd.concat([_training(), pd.DataFrame({"visitorid": [1], "itemid": [99], "timestamp": [100]})])
        first = fit_item_cf(all_events.loc[all_events.timestamp <= 3], 200)
        second = fit_item_cf(_training(), 200)
        a, _ = recommend(first, [10], [10, 20, 30, 40], neighbors=50, k=4)
        b, _ = recommend(second, [10], [10, 20, 30, 40], neighbors=50, k=4)
        self.assertEqual(a, b)
        self.assertNotIn(99, a)

    def test_cold_target_is_miss_and_execution_deterministic(self):
        model = fit_item_cf(_training(), 200)
        first, _ = recommend(model, [10, 20], [10, 20, 30, 40], neighbors=100, k=4)
        second, _ = recommend(model, [20, 10, 10], [10, 20, 30, 40], neighbors=100, k=4)
        self.assertEqual(first, second)
        self.assertEqual(recall_at_k(first, 999, 4), 0.0)


if __name__ == "__main__":
    unittest.main()
