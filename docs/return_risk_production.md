# Customer Return Risk production contract

The engine scores the risk that an eligible household records **zero distinct baskets in `(T, T+28 days]`**. This is a ranking signal, not contractual churn. Its raw Extra Trees output is uncalibrated and must not be presented as a probability or confidence.

## Frozen model and training policy

The artifact contains ET-2: 300 trees, depth 12, minimum leaf 10, `sqrt` features, no class weighting, and random state 42. It uses the exact 16-feature schema in `return_risk.config`. Final production retraining uses all fully labeled month-end cohorts from April through November 2017 (17,074 household-snapshot rows), with feature history ending at each snapshot and outcomes observed only through 2017-12-28. This is production retraining, with no search, calibration fitting, threshold selection, or new outcome-based evaluation.

November was permanently consumed as the one-time research lockbox. Its historical results remain metadata evidence and are never fresh validation after inclusion in final training.

## Inference and policy

A household is eligible at explicit snapshot `T` with at least 90 observed-history days, five distinct baskets, and a 30-day active span. Transactions after `T` are ignored. Every household observed by `T` is returned; ineligible rows have a reason and null score/rank/percentile.

Output fields are `household_id`, `snapshot_date`, `eligibility_status`, `eligibility_reason`, `risk_score`, `risk_rank`, `risk_percentile`, `selected_capacity`, and `flagged`. Higher values mean higher relative risk. The default selects `ceil(N × 10%)` eligible households. Five and twenty percent are secondary scenarios; any capacity in `(0,1]` is accepted. Household ID breaks score ties. There is no fixed threshold.

```bash
python -m marketmind.return_risk.train --raw-dir data/raw/complete_journey --output-dir models/return_risk
```

Programmatic inference uses `score_from_artifact(...)` in `marketmind.return_risk.predict` and requires a snapshot. Monitor schema, eligibility volume/rate, score distribution and drift, flagged count, point-in-time segment coverage, and independently matured outcomes. Retraining requires new complete labels, temporal evaluation, and a new version; November must never be reused as a lockbox.
