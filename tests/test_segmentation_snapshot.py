import unittest

import pandas as pd

from marketmind.segmentation.snapshot import build_household_snapshot


def _transactions() -> pd.DataFrame:
    rows = []
    for household, dates in {
        "eligible": ["2020-01-01", "2020-02-01", "2020-03-01"],
        "too_new": ["2020-03-01", "2020-03-15", "2020-03-31"],
        "too_few": ["2020-01-01", "2020-03-31"],
    }.items():
        for i, date in enumerate(dates):
            rows.append(
                {
                    "household_id": household,
                    "store_id": "s1",
                    "basket_id": f"{household}-{i}",
                    "product_id": "p1" if i < 2 else "p2",
                    "sales_value": 10.0,
                    "retail_disc": 2.0 if i == 0 else 0.0,
                    "coupon_disc": 1.0 if i == 0 else 0.0,
                    "coupon_match_disc": 0.0,
                    "transaction_timestamp": pd.Timestamp(date),
                }
            )
    return pd.DataFrame(rows)


class SegmentationSnapshotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.products = pd.DataFrame(
            {
                "product_id": ["p1", "p2"],
                "department": ["grocery", "produce"],
                "brand": ["Private", "National"],
            }
        )

    def test_sequential_eligibility_and_point_in_time_filter(self):
        transactions = _transactions()
        future = transactions.iloc[[0]].assign(
            household_id="future_only",
            basket_id="future",
            transaction_timestamp=pd.Timestamp("2020-04-01"),
        )
        transactions = pd.concat([transactions, future], ignore_index=True)
        result = build_household_snapshot(
            transactions,
            self.products,
            snapshot_at="2020-03-31 23:59:59",
            min_observed_history_days=60,
            min_baskets=3,
            min_active_span_days=30,
        )

        self.assertEqual(list(result.features.index), ["eligible"])
        self.assertEqual(result.eligibility.observed_households, 3)
        self.assertEqual(result.eligibility.excluded_insufficient_history, 1)
        self.assertEqual(result.eligibility.excluded_insufficient_baskets, 1)
        self.assertEqual(result.eligibility.eligible_households, 1)

    def test_feature_semantics_are_unscaled_and_auditable(self):
        result = build_household_snapshot(
            _transactions().query("household_id == 'eligible'"),
            self.products,
            snapshot_at="2020-03-31 23:59:59",
            min_observed_history_days=0,
            min_baskets=1,
            min_active_span_days=0,
        )
        row = result.features.loc["eligible"]

        self.assertEqual(row["basket_frequency"], 3)
        self.assertEqual(row["monetary_value"], 30)
        self.assertEqual(row["avg_basket_value"], 10)
        self.assertEqual(row["recency_days"], 30)
        self.assertAlmostEqual(row["discount_share_of_gross"], 3 / 33)
        self.assertAlmostEqual(row["discounted_basket_rate"], 1 / 3)
        self.assertAlmostEqual(row["coupon_basket_rate"], 1 / 3)
        self.assertAlmostEqual(row["private_label_spend_share"], 2 / 3)

    def test_duplicate_lines_do_not_inflate_distinct_basket_frequency(self):
        transactions = _transactions().query("household_id == 'eligible'")
        transactions = pd.concat(
            [transactions, transactions.iloc[[0]]], ignore_index=True
        )
        result = build_household_snapshot(
            transactions,
            self.products,
            snapshot_at="2020-03-31 23:59:59",
            min_observed_history_days=0,
            min_baskets=1,
            min_active_span_days=0,
        )

        self.assertEqual(result.features.loc["eligible", "basket_frequency"], 3)


if __name__ == "__main__":
    unittest.main()
