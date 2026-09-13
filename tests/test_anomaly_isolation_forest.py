import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from marketmind.anomalies.isolation_forest import (
    CONFIGURATIONS, FEATURE_COLUMNS, anomaly_score, build_features, fit_isolation_forest,
)
from marketmind.anomalies.isolation_forest_experiment import _synthetic_features, prior_corpus, run_validation


def _calendar():
    dates = pd.date_range("2020-01-01", periods=60)
    return pd.DataFrame({"date": dates, "event_name_1": ["Event"] + [np.nan] * 59,
                         "snap_CA": [1] + [0] * 59, "snap_TX": 0, "snap_WI": 0})


def _scored(n=40):
    residual = np.linspace(-5, 5, n)
    return pd.DataFrame({"block": "development_2", "d": [f"d_{i}" for i in range(1, n + 1)],
        "date": pd.date_range("2020-01-01", periods=n), "store_id": "CA_1", "dept_id": "FOODS_1",
        "state_id": "CA", "actual_sales": 100 + residual, "expected_sales": 100.0,
        "residual": residual, "anomaly_score": residual / 2})


class IsolationForestChallengerTests(unittest.TestCase):
    def test_exact_feature_order_finite_event_and_state_snap(self):
        features = build_features(_scored(), _calendar())
        self.assertEqual(tuple(features.columns), FEATURE_COLUMNS)
        self.assertTrue(np.isfinite(features.to_numpy()).all())
        self.assertEqual(features.event_present.iloc[0], 1)
        self.assertEqual(features.snap.iloc[0], 1)
        self.assertEqual(features.event_present.iloc[1], 0)

    def test_only_three_predeclared_configs(self):
        self.assertEqual(tuple(CONFIGURATIONS), ("IF-1", "IF-2", "IF-3"))
        self.assertTrue(all(config["random_state"] == 42 for config in CONFIGURATIONS.values()))

    def test_model_is_deterministic_and_higher_score_is_more_anomalous(self):
        features = build_features(_scored(), _calendar())
        first, _, _ = fit_isolation_forest(features, "IF-1")
        second, _, _ = fit_isolation_forest(features, "IF-1")
        np.testing.assert_allclose(anomaly_score(first, features), anomaly_score(second, features))
        outlier = features.iloc[[0]].copy(); outlier.loc[:, "residual"] = 10000; outlier.loc[:, "absolute_residual"] = 10000
        self.assertGreater(anomaly_score(first, outlier)[0], np.median(anomaly_score(first, features)))

    def test_prior_corpus_excludes_current_future_validation_and_lockbox(self):
        parts = []
        names = ["development_1_scale_seed", "development_2", "development_3", "development_4", "development_5", "validation"]
        for i, name in enumerate(names):
            part = _scored(2); part["block"] = name; part["d"] = [f"d_{10*i+1}", f"d_{10*i+2}"]; parts.append(part)
        residuals = pd.concat(parts, ignore_index=True)
        prior = prior_corpus(residuals, "development_4")
        self.assertEqual(set(prior.block), set(names[:3]))
        self.assertNotIn("development_4", set(prior.block)); self.assertNotIn("validation", set(prior.block))
        with self.assertRaisesRegex(ValueError, "lockbox"):
            prior_corpus(residuals, "anomaly_lockbox")

    def test_undefined_robust_score_has_finite_neutral_representation(self):
        frame = _scored(); frame.loc[0, "anomaly_score"] = np.nan
        self.assertEqual(build_features(frame, _calendar()).robust_residual_score.iloc[0], 0)

    def test_selection_freeze_required_and_must_precede_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError, "frozen"):
                run_validation(Path(directory), Path("unused"))
        selection = json.loads((Path(__file__).parents[1] / "reports/anomalies/artifacts/if_selected_config.json").read_text())
        self.assertEqual(selection["selected_config"], "IF-3")
        self.assertEqual(selection["validation_status_at_freeze"], "not scored by Isolation Forest")

    def test_direction_is_not_part_of_if_score_or_features(self):
        self.assertNotIn("direction", FEATURE_COLUMNS)
        self.assertNotIn("store_id", FEATURE_COLUMNS)
        self.assertNotIn("dept_id", FEATURE_COLUMNS)

    def test_synthetic_features_recompute_residual_without_refitting(self):
        features = build_features(_scored(), _calendar())
        model, _, _ = fit_isolation_forest(features, "IF-1")
        estimator_ids = tuple(id(tree) for tree in model.estimators_)
        case = pd.DataFrame({
            "date": [pd.Timestamp("2020-01-01")], "store_id": ["CA_1"], "dept_id": ["FOODS_1"],
            "injected_actual_sales": [130.0], "expected_sales": [100.0],
            "score_after": [3.0], "prior_residual_median": [0.0], "prior_robust_scale": [10.0],
        })
        injected = _synthetic_features(case, _calendar())
        self.assertEqual(injected.residual.iloc[0], 30.0)
        self.assertEqual(injected.robust_residual_score.iloc[0], 3.0)
        anomaly_score(model, injected)
        self.assertEqual(estimator_ids, tuple(id(tree) for tree in model.estimators_))


if __name__ == "__main__":
    unittest.main()
