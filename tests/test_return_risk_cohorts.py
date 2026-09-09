import unittest

import pandas as pd

from marketmind.return_risk.cohorts import (
    EligibilityRule,
    RightCensoringError,
    build_labeled_cohort,
    future_outcomes,
    history_through_snapshot,
    household_eligibility,
)


def _transactions() -> pd.DataFrame:
    rows = [
        ("a", "a1", "2020-01-01"),
        ("a", "a2", "2020-01-11"),
        ("a", "a3", "2020-01-31"),
        ("a", "a4", "2020-02-10"),  # exactly T: history, not outcome
        ("a", "a5", "2020-02-11"),
        ("a", "a5", "2020-02-11"),  # second line, same basket
        ("a", "a6", "2020-02-24"),  # exactly T + 14 days
        ("a", "a7", "2020-02-25"),  # after the outcome window
        ("b", "b1", "2020-01-01"),
        ("b", "b2", "2020-01-11"),
        ("b", "b3", "2020-01-21"),
        ("b", "b4", "2020-01-31"),
        ("b", "b5", "2020-02-10"),
    ]
    return pd.DataFrame(rows, columns=["household_id", "basket_id", "transaction_timestamp"])


class ReturnRiskCohortTests(unittest.TestCase):
    def test_history_ends_at_snapshot_and_excludes_future(self):
        history = history_through_snapshot(_transactions(), "2020-02-10")
        self.assertEqual(history.transaction_timestamp.max(), pd.Timestamp("2020-02-10"))
        self.assertNotIn("a5", set(history.basket_id))

    def test_future_interval_is_open_left_and_closed_right(self):
        outcomes = future_outcomes(
            _transactions(), ["a", "b"], "2020-02-10", 14, "2020-02-24"
        )
        self.assertEqual(outcomes.loc["a", "future_baskets"], 2)
        self.assertEqual(outcomes.loc["a", "return_flag"], 1)
        self.assertEqual(outcomes.loc["b", "return_risk_target"], 1)

    def test_distinct_baskets_not_transaction_lines_are_counted(self):
        outcome = future_outcomes(
            _transactions(), ["a"], "2020-02-10", 1, "2020-02-11"
        )
        self.assertEqual(outcome.loc["a", "future_baskets"], 1)

    def test_censored_cohort_is_rejected(self):
        with self.assertRaises(RightCensoringError):
            future_outcomes(
                _transactions(), ["a"], "2020-02-10", 14, "2020-02-23"
            )

    def test_eligibility_is_deterministic_and_uses_distinct_baskets(self):
        rule = EligibilityRule(40, 5, 30)
        first = household_eligibility(_transactions(), "2020-02-10", rule)
        second = household_eligibility(_transactions(), "2020-02-10", rule)
        pd.testing.assert_frame_equal(first, second)
        self.assertFalse(first.loc["a", "eligible"])
        self.assertTrue(first.loc["b", "eligible"])
        self.assertEqual(first.loc["a", "basket_count"], 4)

    def test_labeled_cohort_contains_only_eligible_households(self):
        cohort = build_labeled_cohort(
            _transactions(),
            "2020-02-10",
            14,
            "2020-02-24",
            EligibilityRule(40, 5, 30),
        )
        self.assertEqual(set(cohort.index), {"b"})


if __name__ == "__main__":
    unittest.main()
