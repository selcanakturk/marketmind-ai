import tempfile
import unittest
import json
from pathlib import Path

import numpy as np
import pandas as pd

from marketmind.recommendations.bundle import load_bundle, save_bundle
from marketmind.recommendations.config import DEFAULT_K, FROZEN_CONFIGURATION, LOCKBOX_STATUS, NEIGHBOR_COUNT
from marketmind.recommendations.predict import OUTPUT_COLUMNS, recommend_visitor
from marketmind.recommendations.train import train_production_bundle, validate_events


def _events():
    return pd.DataFrame({
        "timestamp": [1, 2, 3, 1, 2, 1, 2, 3],
        "visitorid": [1, 1, 1, 2, 2, 3, 3, 3],
        "itemid": [10, 10, 20, 10, 30, 20, 30, 40],
        "event": ["view", "transaction", "view", "view", "addtocart", "view", "view", "transaction"],
    })


class RecommendationProductionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = train_production_bundle(_events())

    def test_raw_contract_transactionid_optional_and_invalid_values_rejected(self):
        self.assertEqual(len(validate_events(_events())), 8)
        with self.assertRaisesRegex(ValueError, "missing columns"):
            validate_events(_events().drop(columns="event"))
        bad = _events().copy()
        bad.loc[0, "timestamp"] = np.nan
        with self.assertRaisesRegex(ValueError, "timestamp"):
            validate_events(bad)
        bad = _events().copy()
        bad.loc[0, "event"] = "click"
        with self.assertRaisesRegex(ValueError, "event"):
            validate_events(bad)

    def test_bundle_is_compact_valid_and_round_trips(self):
        bundle = self.bundle
        self.assertFalse(hasattr(bundle, "interaction_matrix"))
        self.assertLessEqual(np.diff(bundle.neighbor_indptr).max(), 50)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.joblib"
            save_bundle(bundle, path)
            loaded = load_bundle(path)
            self.assertTrue(np.array_equal(loaded.item_ids, bundle.item_ids))
            self.assertTrue(np.array_equal(loaded.neighbor_indices, bundle.neighbor_indices))
            before = recommend_visitor(_events(), 1, 3, bundle, k=4)
            after = recommend_visitor(_events(), 1, 3, loaded, k=4)
            pd.testing.assert_frame_equal(before, after)

    def test_frozen_configuration_and_lockbox_marker(self):
        self.assertEqual(NEIGHBOR_COUNT, 50)
        self.assertEqual(DEFAULT_K, 20)
        self.assertEqual(FROZEN_CONFIGURATION["self_similarity"], "retained")
        self.assertEqual(FROZEN_CONFIGURATION["seen_items"], "allowed")
        self.assertEqual(FROZEN_CONFIGURATION["event_weighting"], "none; all event types equal")
        self.assertEqual(LOCKBOX_STATUS, "consumed")
        self.assertEqual(self.bundle.lockbox_status, "consumed")

    def test_reviewable_artifact_metadata_and_summary_are_operational_only(self):
        model_dir = Path(__file__).parents[1] / "models" / "recommendations"
        metadata = json.loads((model_dir / "metadata.json").read_text())
        summary = json.loads((model_dir / "training_summary.json").read_text())
        self.assertEqual(metadata["lockbox_status"], "consumed")
        self.assertEqual(metadata["neighbor_count"], 50)
        self.assertTrue(metadata["self_similarity"])
        self.assertTrue(metadata["allow_seen_items"])
        forbidden = ("ndcg", "recall", "hitrate", "hit_rate", "mrr", "precision", "quality")
        self.assertFalse(any(term in key.lower() for key in summary for term in forbidden))

    def test_self_similarity_seen_items_ties_schema_and_determinism(self):
        first = recommend_visitor(_events(), 1, 3, self.bundle, k=4)
        second = recommend_visitor(_events().sample(frac=1, random_state=4), 1, 3, self.bundle, k=4)
        pd.testing.assert_frame_equal(first, second)
        self.assertEqual(tuple(first.columns), OUTPUT_COLUMNS)
        self.assertEqual(first.iloc[0].itemid, 10)  # retained self edge
        self.assertTrue(first.iloc[0].was_previously_seen)  # seen remains eligible
        self.assertEqual(len(first.itemid), first.itemid.nunique())
        self.assertLess(first.itemid.tolist().index(20), first.itemid.tolist().index(30))

    def test_repeated_history_does_not_multiply_scores_and_future_is_ignored(self):
        base = recommend_visitor(_events(), 1, 3, self.bundle, k=4)
        augmented = pd.concat([_events(), pd.DataFrame({
            "timestamp": [2, 4], "visitorid": [1, 1], "itemid": [20, 999], "event": ["view", "view"]
        })], ignore_index=True)
        changed = recommend_visitor(augmented, 1, 3, self.bundle, k=4)
        pd.testing.assert_frame_equal(base, changed)
        self.assertNotIn(999, changed.itemid.tolist())

    def test_unknown_visitor_and_unknown_history_fall_back_to_current_popularity(self):
        unknown = recommend_visitor(_events(), 999, 3, self.bundle, k=3)
        self.assertEqual(unknown.itemid.tolist(), [10, 20, 30])
        self.assertTrue((unknown.score_source == "popularity_fill").all())
        self.assertTrue((unknown.fallback_reason == "no_history").all())
        augmented = pd.concat([_events(), pd.DataFrame({
            "timestamp": [3], "visitorid": [8], "itemid": [999], "event": ["view"]
        })], ignore_index=True)
        partial = recommend_visitor(augmented, 8, 3, self.bundle, k=5)
        self.assertTrue((partial.fallback_reason == "no_collaborative_history").all())
        self.assertIn(999, partial.itemid.tolist())  # a new item may enter only by popularity

    def test_partially_known_history_uses_known_graph_and_popularity_fill(self):
        augmented = pd.concat([_events(), pd.DataFrame({
            "timestamp": [3], "visitorid": [1], "itemid": [999], "event": ["view"]
        })], ignore_index=True)
        result = recommend_visitor(augmented, 1, 3, self.bundle, k=5)
        self.assertEqual(result.known_history_item_count.iloc[0], 2)
        self.assertEqual(result.score_source.iloc[0], "collaborative")
        self.assertIn(999, result.loc[result.score_source == "popularity_fill", "itemid"].tolist())

    def test_invalid_k_and_pretraining_snapshot_rejected(self):
        with self.assertRaisesRegex(ValueError, "k must"):
            recommend_visitor(_events(), 1, 3, self.bundle, k=0)
        with self.assertRaisesRegex(ValueError, "training cutoff"):
            recommend_visitor(_events(), 1, 2, self.bundle)


if __name__ == "__main__":
    unittest.main()
