# Customer Return Risk Methodology

This is the source of truth for MarketMind AI Customer Return Risk Phase 3 Step 1. It defines the temporal target and cohort contract only. No classifier, predictive feature matrix, threshold, calibrated probability, or production service exists.

Complete Journey 2.0 is a **grocery-retail household panel**, not contractual subscription data and not an individual e-commerce customer table. The outcome is therefore observed return behavior within a fixed window, never automatic “churn.”

## Frozen decisions

### Prediction unit and target

One future supervised row represents one `household_id` at one calendar month-end snapshot `T`. A household, basket, and basket-product transaction line are distinct grains; purchase frequency and outcomes count distinct `basket_id` values.

The target window is **`(T, T + 28 days]`**:

- `return_flag = 1`: at least one distinct basket is observed in the window;
- `return_flag = 0`: zero distinct baskets are observed in the complete window;
- **`return_risk_target = 1`: zero distinct baskets are observed in the complete window**;
- `return_risk_target = 0`: at least one distinct basket is observed.

Target 1 means **no observed purchase within 28 days**, not churn. A future classifier output is a risk score until calibration and probabilistic semantics are evaluated.

### Observation boundary and eligibility

The complete-data boundary is **2017-12-31 23:59:59**. The 86 baskets recorded during the partial 2018-01-01 boundary are excluded from coverage claims so that observation does not depend on an incomplete day.

At every snapshot, eligibility is recomputed using only data at or before `T`:

1. at least 90 calendar days from first observed basket to `T`;
2. at least 5 distinct baskets by `T`;
3. at least 30 calendar days between first and last observed basket by `T`.

There is no future-activity, spend, demographic, or segment condition. Ineligible households are outside this initial estimand; they are not classified as returners or non-returners.

### Cohorts and temporal evaluation

Monthly repeated snapshots are frozen because they add temporal diversity and mirror periodic scoring. Their correlation must be respected; row independence must not be assumed.

| Role | Snapshot(s) | Complete 28-day outcome window(s) |
|---|---|---|
| Training | 2017-04-30, 05-31, 06-30, 07-31, 08-31 at 23:59:59 | through 05-28, 06-28, 07-28, 08-28, 09-28 at 23:59:59 |
| Validation | 2017-09-30 and 2017-10-31 at 23:59:59 | through 10-28 and 11-28 at 23:59:59 |
| Final lockbox | 2017-11-30 23:59:59 | through 2017-12-28 23:59:59 |

The same household may appear in more than one role because the deployment question is genuinely later issuance to the active population, not generalization only to unseen households. Temporal ordering—not household-disjoint randomization—is primary. Metrics must be reported by snapshot as well as pooled; uncertainty methods must account for household clustering. A household-disjoint sensitivity analysis may later test memorization, but cannot replace the temporal evaluation.

The final lockbox has 2,463 households observed and 2,322 eligible. Its complete horizon is verified, but its return/no-return outcomes were not inspected in target design. It may be evaluated once only after features, preprocessing, model family, tuning, threshold, and calibration decisions are frozen.

### Right-censoring

A target is legal only when `T + 28 days <= 2017-12-31 23:59:59`. The label interval is open on the left and closed on the right: a basket at `T` belongs to history; a basket exactly at `T + H` is a return. An incomplete horizon is **unknown due to dataset end**, not a no-return label, and cohort construction must fail rather than silently label it.

### Candidate feature availability

Only information timestamped at or before `T` may later be considered. Compact candidate families are:

- RFM: days since last basket, distinct historical baskets, and historical net sales;
- basket behavior: average/median basket value and recent basket frequency;
- cadence: mean/median gaps, gap variability, and days since last basket;
- engagement: active days/weeks/months and active span;
- product behavior: distinct products/departments and category concentration;
- promotion behavior: discount share and coupon-use rates, described as associations only;
- trends: recent versus earlier basket/spend changes and recent-to-long-term activity ratios.

Predeclared recent windows are 7, 14, 28, and 56 days for baskets, and 28 and 56 days for spend. The 28-day window aligns with the target cadence; 7/14 capture immediate disengagement and 56 supplies a longer comparison. Windows end at `T`; none overlaps the target. Redundant variants will be narrowed before the first model rather than assembled into a large matrix now.

### Segmentation interaction

Segment assignment is excluded from the first predictive feature set. It may be used for post-model error, score, and intervention analysis if assignment is generated point-in-time. The September production/reference assignment must never be joined to earlier snapshots. A later predictive-feature experiment would require a documented as-of-`T` segmentation artifact and must be justified separately.

### Evaluation and baseline policy

Given the 11.80% development no-return prevalence at 28 days, **PR-AUC is the primary candidate discrimination metric** and ROC-AUC is secondary. Both must be paired with snapshot-level prevalence and a prevalence/no-skill PR reference. Operational reporting should include precision, recall, F1, precision at intervention capacity, and recall at a validation-selected threshold. Later probability claims require Brier score and calibration curves on validation data.

No threshold is chosen now. A future threshold must reflect intervention capacity, precision/recall, false-positive cost, and false-negative cost—not accuracy alone. Do not automatically use SMOTE; temporal snapshots make synthetic interpolation questionable. Class weights and threshold selection may be evaluated after temporal splitting.

Future baselines, in order, are: (A) a simple recency rule, (B) a predeclared recency/frequency heuristic, and (C) Logistic Regression. Learned candidates must add value beyond useful behavioral rules.

### Leakage checklist

- Features and eligibility end at `T`; purchases at `T` are history, never outcome.
- No future basket count, spend, target-window activity, or future-updated metadata enters features.
- Rolling windows end at `T` and never overlap `(T, T+H]`.
- No full-year or September segment assignment is backfilled into earlier snapshots.
- No random train/test split or duplicate household-snapshot row is allowed.
- Preprocessing is fitted on training snapshots only; later cohorts are transform-only.
- Class balancing occurs only after temporal roles are fixed and never across cohorts.
- Horizon, features, model family, hyperparameters, threshold, and calibration cannot use lockbox outcomes.
- Censored rows are unknown and cannot be converted to target 1.
- Repeated rows are keyed by `(household_id, snapshot_at)` and grouped uncertainty is required.

## Open decisions

- exact final historical feature definitions, transformations, redundancy pruning, and missing-value policy;
- whether class weighting is beneficial;
- Logistic Regression and any later tree-model specifications and tuning protocol;
- validation selection metric confirmation and uncertainty intervals;
- intervention capacity, costs, and operating threshold;
- whether calibration is adequate for probability language and which calibrator is appropriate;
- whether a household-disjoint sensitivity test or point-in-time segment-feature ablation adds useful evidence;
- monitoring, retraining, artifact versioning, and production inference contracts.

These decisions may not be resolved using the lockbox.
