import unittest

import pandas as pd

from marketmind.recommendations.evaluation import hit_rate_at_k, mrr_at_k, ndcg_at_k, precision_at_k, recall_at_k
from marketmind.recommendations.popularity import point_in_time_topk, popularity_ranking
from marketmind.recommendations.splits import candidate_items, next_item_instances, validate_events


def _events():
    rows = [
        (1000, 1, "view", 10, None), (2000, 1, "view", 11, None),
        (3000, 1, "view", 10, None), (3500, 2, "view", 20, None),
        (5000, 1, "addtocart", 10, None), (6000, 2, "view", 99, None),
    ]
    return pd.DataFrame(rows, columns=["timestamp", "visitorid", "event", "itemid", "transactionid"])


class RecommendationMethodologyTests(unittest.TestCase):
    def test_timestamp_conversion_is_utc(self):
        result = validate_events(_events())
        self.assertEqual(str(result.event_at.dtype), "datetime64[ms, UTC]")

    def test_history_is_strictly_before_target_and_seen_items_are_retained(self):
        result = next_item_instances(_events(), pd.Timestamp(4000, unit="ms", tz="UTC"), pd.Timestamp(7000, unit="ms", tz="UTC"))
        self.assertEqual(result.visitorid.tolist(), [1])
        self.assertGreater(result.target_timestamp.iloc[0], pd.Timestamp(4000, unit="ms", tz="UTC"))
        self.assertTrue(result.target_previously_seen.iloc[0])

    def test_future_item_does_not_enter_candidate_universe_and_is_cold(self):
        cutoff = pd.Timestamp(4000, unit="ms", tz="UTC")
        self.assertNotIn(99, candidate_items(_events(), cutoff))
        result = next_item_instances(_events(), cutoff, pd.Timestamp(7000, unit="ms", tz="UTC"), min_prior_interactions=1)
        cold = result.loc[result.visitorid.eq(2)].iloc[0]
        self.assertFalse(cold.candidate_item_known)

    def test_tiny_single_target_metrics(self):
        ranked = [8, 4, 2]
        self.assertEqual(recall_at_k(ranked, 4, 2), 1.0)
        self.assertEqual(hit_rate_at_k(ranked, 4, 1), 0.0)
        self.assertAlmostEqual(ndcg_at_k(ranked, 4, 3), 1 / 1.584962500721156)
        self.assertEqual(mrr_at_k(ranked, 4, 3), 0.5)
        self.assertEqual(precision_at_k(ranked, 4, 2), 0.5)
        self.assertEqual(recall_at_k(ranked, 99, 3), 0.0)  # cold target remains a miss

    def test_ordering_is_deterministic_under_input_shuffle(self):
        first = next_item_instances(_events(), pd.Timestamp(4000, unit="ms", tz="UTC"), pd.Timestamp(7000, unit="ms", tz="UTC"), min_prior_interactions=1)
        second = next_item_instances(_events().sample(frac=1, random_state=2), pd.Timestamp(4000, unit="ms", tz="UTC"), pd.Timestamp(7000, unit="ms", tz="UTC"), min_prior_interactions=1)
        pd.testing.assert_frame_equal(first, second)

    def test_point_in_time_popularity_updates_availability_counts_and_ties(self):
        early = popularity_ranking(_events(), pd.Timestamp(2500, unit="ms", tz="UTC"), 20)
        later = popularity_ranking(_events(), pd.Timestamp(6000, unit="ms", tz="UTC"), 20)
        self.assertEqual(early, [10, 11])  # tied counts resolve by numeric ID
        self.assertNotIn(99, early)
        self.assertEqual(later[0], 10)  # counts increment as events arrive
        self.assertIn(99, later)
        self.assertEqual(len(later), len(set(later)))

    def test_repeated_topk_execution_is_deterministic(self):
        instances = next_item_instances(_events(), pd.Timestamp(4000, unit="ms", tz="UTC"), pd.Timestamp(7000, unit="ms", tz="UTC"), min_prior_interactions=1)
        first = point_in_time_topk(_events(), instances)
        second = point_in_time_topk(_events().sample(frac=1, random_state=4), instances)
        pd.testing.assert_frame_equal(first, second)

    def test_later_lockbox_rows_cannot_change_validation_ranking(self):
        cutoff = pd.Timestamp(4000, unit="ms", tz="UTC")
        full = popularity_ranking(_events(), cutoff, 20)
        without_later = popularity_ranking(_events().loc[lambda x: x.timestamp <= 4000], cutoff, 20)
        self.assertEqual(full, without_later)


if __name__ == "__main__":
    unittest.main()
