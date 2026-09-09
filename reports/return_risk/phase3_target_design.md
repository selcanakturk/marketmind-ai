# Phase 3 Customer Return Risk — Target and Cohort Design

## Problem definition and dataset context

The eventual task is: given information known for an eligible grocery-retail household at snapshot time `T`, estimate its risk of making no basket purchase in a fixed future horizon. Complete Journey 2.0 contains 2,469 households, 155,848 distinct baskets, and 1,469,307 basket-product lines. It is a one-year grocery panel, not contractual churn data or an individual e-commerce customer table.

Authentic transaction timestamps run from 2017-01-01 11:53:26 to 2018-01-01 04:01:20. Because 2018-01-01 contains only 86 early-hours baskets and is an incomplete boundary day, this design conservatively freezes complete observation at **2017-12-31 23:59:59**. There are 541 baskets on December 31, supporting use of that complete day.

## Target semantics

The prediction entity is `(household_id, snapshot_at)`. The selected target window is `(T, T + 28 days]`. `return_risk_target=1` means zero distinct baskets in the fully observed window; `return_risk_target=0` means at least one. A basket at `T` is historical, while one exactly at `T+28 days` is a return. “No return” is not “churn,” and an eventual uncalibrated model output is a risk score rather than a probability.

## Horizon audit

The audit used the same seven development month-ends for all four horizons, so horizon comparisons are not confounded by different cohort dates. Every displayed outcome is fully observable. `history days` is elapsed calendar days from the source start date to the snapshot date; household-specific eligibility still measures from each household's first observed basket.

| Snapshot | History days | Observed | Eligible / complete | H | Return | No return | No-return % |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2017-04-30 | 119 | 2,327 | 1,777 | 14 | 1,496 | 281 | 15.81% |
| 2017-04-30 | 119 | 2,327 | 1,777 | 28 | 1,652 | 125 | 7.03% |
| 2017-04-30 | 119 | 2,327 | 1,777 | 42 | 1,699 | 78 | 4.39% |
| 2017-04-30 | 119 | 2,327 | 1,777 | 56 | 1,724 | 53 | 2.98% |
| 2017-05-31 | 150 | 2,372 | 1,970 | 14 | 1,565 | 405 | 20.56% |
| 2017-05-31 | 150 | 2,372 | 1,970 | 28 | 1,778 | 192 | 9.75% |
| 2017-05-31 | 150 | 2,372 | 1,970 | 42 | 1,863 | 107 | 5.43% |
| 2017-05-31 | 150 | 2,372 | 1,970 | 56 | 1,895 | 75 | 3.81% |
| 2017-06-30 | 180 | 2,393 | 2,085 | 14 | 1,654 | 431 | 20.67% |
| 2017-06-30 | 180 | 2,393 | 2,085 | 28 | 1,866 | 219 | 10.50% |
| 2017-06-30 | 180 | 2,393 | 2,085 | 42 | 1,957 | 128 | 6.14% |
| 2017-06-30 | 180 | 2,393 | 2,085 | 56 | 1,992 | 93 | 4.46% |
| 2017-07-31 | 211 | 2,414 | 2,172 | 14 | 1,693 | 479 | 22.05% |
| 2017-07-31 | 211 | 2,414 | 2,172 | 28 | 1,903 | 269 | 12.38% |
| 2017-07-31 | 211 | 2,414 | 2,172 | 42 | 2,008 | 164 | 7.55% |
| 2017-07-31 | 211 | 2,414 | 2,172 | 56 | 2,056 | 116 | 5.34% |
| 2017-08-31 | 242 | 2,430 | 2,219 | 14 | 1,658 | 561 | 25.28% |
| 2017-08-31 | 242 | 2,430 | 2,219 | 28 | 1,908 | 311 | 14.02% |
| 2017-08-31 | 242 | 2,430 | 2,219 | 42 | 2,007 | 212 | 9.55% |
| 2017-08-31 | 242 | 2,430 | 2,219 | 56 | 2,069 | 150 | 6.76% |
| 2017-09-30 | 272 | 2,446 | 2,247 | 14 | 1,686 | 561 | 24.97% |
| 2017-09-30 | 272 | 2,446 | 2,247 | 28 | 1,937 | 310 | 13.80% |
| 2017-09-30 | 272 | 2,446 | 2,247 | 42 | 2,040 | 207 | 9.21% |
| 2017-09-30 | 272 | 2,446 | 2,247 | 56 | 2,101 | 146 | 6.50% |
| 2017-10-31 | 303 | 2,452 | 2,282 | 14 | 1,693 | 589 | 25.81% |
| 2017-10-31 | 303 | 2,452 | 2,282 | 28 | 1,967 | 315 | 13.80% |
| 2017-10-31 | 303 | 2,452 | 2,282 | 42 | 2,068 | 214 | 9.38% |
| 2017-10-31 | 303 | 2,452 | 2,282 | 56 | 2,130 | 152 | 6.66% |

Aggregate comparison counts repeated household-snapshot rows, not unique people:

| Horizon | Cohort rows | Return | No return | No-return % | Interpretation / feasibility |
|---:|---:|---:|---:|---:|---|
| 14 days | 14,752 | 11,445 | 3,307 | 22.42% | operationally fast, but likely treats one missed short grocery cycle as risk |
| **28 days** | **14,752** | **13,011** | **1,741** | **11.80%** | monthly business cadence, meaningful inactivity, supports a November lockbox |
| 42 days | 14,752 | 13,642 | 1,110 | 7.52% | less timely and more imbalanced; latest month-end shifts earlier |
| 56 days | 14,752 | 13,967 | 785 | 5.32% | two-month delay, strongest imbalance, least temporal room |

Historical inter-purchase gaps have median 2.21, p90 11.54, p95 18.07, and p99 45.95 days. Those data make 14 days plausible but not decisive. The **28-day horizon is frozen** because it clears the p95 cadence, maps to an approximately monthly intervention cycle, retains 1,741 positive development rows without manufacturing balance, and permits a later November lockbox. Forty-two and 56 days delay intervention and sacrifice late-cohort validation while pushing target 1 below 8% and 6%; 14 days is more likely to flag routine variation.

The upward no-return prevalence over calendar time may reflect seasonality, panel behavior, eligibility composition, or data-generating changes. It is not evidence of worsening loyalty and reinforces snapshot-level temporal reporting.

## Eligibility analysis

The frozen standard rule is at least 90 observed-history days, 5 distinct baskets, and 30 active-span days. A predeclared lighter alternative—60 days, 3 baskets, and 14 active-span days—was audited at 28 days.

| Rule | Development rows | Unique eligible households | No return | No-return % |
|---|---:|---:|---:|---:|
| Standard 90/5/30 | 14,752 | 2,282 | 1,741 | 11.80% |
| Lighter 60/3/14 | 15,746 | 2,368 | 2,192 | 13.92% |

The standard rule retains 93.07% of households observed by October (2,282/2,452) and gives more reliable cadence/history inputs while remaining compatible with segmentation operations. Relative to the lighter rule it removes 994 repeated rows (6.31%). The higher no-return rate under the lighter rule confirms a scope tradeoff: the standard estimand underrepresents newly observed, infrequent, and short-span households, which may be higher risk. This is disclosed rather than “fixed” through a model-performance choice. A future separate new-household policy may be needed; it is not mixed into this first model.

## Repeated snapshots, temporal validation, and lockbox

Repeated month-end household snapshots are recommended. They provide realistic periodic issuance and temporal diversity, but correlated observations forbid a random row split. Training uses April–August (10,223 rows; 1,116 target-1 rows), validation uses September–October (4,529 rows; 625 target-1 rows), and the untouched lockbox is November 30. Outcomes end exactly 28 days after each snapshot as listed in the methodology.

Household overlap is acceptable for the main estimand: predicting a genuinely later state of the operational population. It means evaluation is temporal generalization, not new-household generalization. Metrics must be cohort-specific and pooled, and later confidence intervals should cluster by household. A household-disjoint sensitivity analysis remains optional.

At the November lockbox snapshot, 2,463 households are observed and 2,322 satisfy eligibility. Its outcome ends 2017-12-28 23:59:59 and is fully observable. **No lockbox return counts, no-return counts, or prevalence were computed or inspected.** The lockbox cannot influence horizon, features, model, hyperparameters, threshold, or calibration.

## Feature families and segmentation interaction

Candidate snapshot-safe families are RFM, basket value/frequency, cadence, engagement span, product/category breadth and concentration, promotion/coupon associations, and recent-versus-long-term trends. Candidate recent windows are 7/14/28/56 days for baskets and 28/56 days for spend, all ending at `T`. This audit creates no final feature matrix.

Production segmentation is initially excluded from predictive inputs and reserved for point-in-time-safe post-model analysis. September assignments cannot describe April–August households. Any later segment-feature experiment needs an as-of-`T` artifact and separate justification.

## Metric, threshold, imbalance, and baseline plan

PR-AUC is the primary candidate metric because target 1 is 11.80% in development; ROC-AUC is secondary. Report prevalence/no-skill reference, per-snapshot and pooled discrimination, precision, recall, F1, precision at intervention capacity, and validation-selected recall. Brier score and calibration curves are required before probability language.

No threshold exists. It must later reflect intervention capacity and asymmetric costs, not accuracy. SMOTE is not automatic because synthetic temporal snapshots can distort structure; class weights and validation-only threshold selection are safer candidates.

Future baselines are a simple recency rule, a simple recency/frequency heuristic, and Logistic Regression. No baseline was trained in this step.

## Leakage protections

The implementation enforces the open-left/closed-right target, distinct-basket outcomes, point-in-time eligibility/history, and hard rejection of censored horizons. Governance prohibits future purchases/spend in features, overlapping rolling windows, full-year or future segment labels, random splitting, future-fitted preprocessing, balancing before the temporal split, duplicate `(household, snapshot)` rows, lockbox selection, and censored-negative labels.

## Frozen decisions

- Grocery household at month-end is the entity; repeated snapshots are allowed.
- Positive class is `return_risk_target=1`: zero baskets in `(T,T+28 days]`.
- Horizon is 28 days; observation ends at 2017-12-31 23:59:59.
- Eligibility is 90 history days / 5 distinct baskets / 30 active-span days.
- April–August train; September–October validation; November 30 untouched lockbox.
- Segment is excluded initially; PR-AUC is the primary candidate metric.

## Open decisions and known limitations

Open items are final feature definitions/pruning, preprocessing, class weighting, model specifications, uncertainty intervals, intervention capacity/costs, threshold, calibration, and production monitoring. Complete Journey covers about one year, has household rather than individual identity, is grocery-specific, cannot establish contractual attrition, and provides limited seasonal replication. Panel-entry and dataset-end effects can resemble behavior change. The selected eligibility scope excludes cold-start households. Repeated snapshots are correlated, and no model can establish causality from promotion variables.

Phase 3 is ready for leakage-safe baseline modeling after review of this frozen design; the lockbox remains unconsumed.
