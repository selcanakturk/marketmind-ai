import unittest

import pandas as pd

from marketmind.recommendations.item_cf import fit_item_cf, recommend
from marketmind.recommendations.lockbox import FROZEN_NEIGHBORS, lockbox_instance_keys, reveal_targets_after_ranking


def _events():
    rows = [
        (1000, 1, "view", 10, None), (2000, 1, "view", 20, None),
        (4000, 1, "view", 30, None),  # at T: history, not target
        (5000, 1, "view", 99, None),  # lockbox target/new model item
        (1000, 2, "view", 10, None), (2000, 2, "view", 40, None),
        (6000, 2, "view", 10, None),
    ]
    return pd.DataFrame(rows, columns=["timestamp", "visitorid", "event", "itemid", "transactionid"])


class RecommendationLockboxTests(unittest.TestCase):
    def test_frozen_neighborhood_and_prelockbox_similarity(self):
        self.assertEqual(FROZEN_NEIGHBORS, 50)
        events = _events()
        model = fit_item_cf(events.loc[events.timestamp < 4000], 50)
        self.assertNotIn(30, model.item_to_index)
        self.assertNotIn(99, model.item_to_index)

    def test_keys_use_history_through_t_without_target_revelation(self):
        keys = lockbox_instance_keys(_events(), pd.Timestamp(4000, unit="ms", tz="UTC"), pd.Timestamp(7000, unit="ms", tz="UTC"))
        self.assertEqual(keys.visitorid.tolist(), [1, 2])
        self.assertFalse(any("target" in column for column in keys))

    def test_preoutcome_contract_and_post_freeze_target_join(self):
        keys = lockbox_instance_keys(_events(), pd.Timestamp(4000, unit="ms", tz="UTC"), pd.Timestamp(7000, unit="ms", tz="UTC"))
        ranking = keys.copy()
        for rank in range(1, 21):
            ranking[f"rank_{rank}_itemid"] = rank
        joined = reveal_targets_after_ranking(_events(), pd.Timestamp(4000, unit="ms", tz="UTC"), pd.Timestamp(7000, unit="ms", tz="UTC"), ranking)
        self.assertTrue(joined.target_timestamp.gt(joined.recommendation_timestamp).all())
        with self.assertRaises(ValueError):
            reveal_targets_after_ranking(_events(), pd.Timestamp(4000, unit="ms", tz="UTC"), pd.Timestamp(7000, unit="ms", tz="UTC"), ranking.assign(target_itemid=99))

    def test_new_item_has_no_cf_representation_but_can_fill_after_availability(self):
        events = _events(); model = fit_item_cf(events.loc[events.timestamp < 4000], 50)
        ranking, _ = recommend(model, [10, 20], [99, 40, 20, 10], neighbors=50, k=4, candidate_items=[10, 20, 40, 99])
        self.assertIn(99, ranking)
        self.assertNotIn(99, model.item_to_index)
        before, _ = recommend(model, [10, 20], [40, 20, 10], neighbors=50, k=3, candidate_items=[10, 20, 40])
        self.assertNotIn(99, before)

    def test_seen_and_self_similarity_remain_enabled_and_deterministic(self):
        events = _events(); model = fit_item_cf(events.loc[events.timestamp < 4000], 50)
        first, _ = recommend(model, [10, 20], [40, 20, 10], neighbors=50, k=3)
        second, _ = recommend(model, [20, 10], [40, 20, 10], neighbors=50, k=3)
        self.assertEqual(first, second)
        self.assertTrue(set(first) & {10, 20})


if __name__ == "__main__": unittest.main()
