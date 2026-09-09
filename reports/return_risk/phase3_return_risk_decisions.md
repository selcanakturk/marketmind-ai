# Phase 3 Return Risk Decisions

Status: target and cohort design frozen; no model exists.

| Decision | Frozen outcome |
|---|---|
| Entity | Complete Journey grocery-retail `household_id` at a month-end snapshot `T` |
| Positive class | `return_risk_target=1`: zero distinct baskets in complete `(T,T+28d]`; not churn |
| Return | `return_flag=1`: at least one distinct basket in `(T,T+28d]` |
| Horizon | 28 days, selected from cadence, business meaning, prevalence, and temporal feasibility—not model performance |
| Observation end | 2017-12-31 23:59:59; incomplete 2018-01-01 excluded |
| Eligibility | at least 90 history days, 5 distinct baskets, and 30 active-span days, recomputed at `T` |
| Training | 2017-04-30, 05-31, 06-30, 07-31, 08-31 23:59:59; outcomes end 05-28, 06-28, 07-28, 08-28, 09-28 |
| Validation | 2017-09-30 and 10-31 23:59:59; outcomes end 10-28 and 11-28 |
| Lockbox | 2017-11-30 23:59:59 → 2017-12-28 23:59:59; 2,322 eligible; outcomes untouched |
| Repeated households | allowed across time; no random rows; cohort metrics plus household-clustered uncertainty |
| Segment feature | excluded initially; point-in-time-safe post-model analysis only |
| Metrics | PR-AUC primary candidate; ROC-AUC secondary; precision/recall/F1/capacity metrics; later Brier/calibration |
| Baselines | recency rule, recency/frequency heuristic, Logistic Regression; none trained yet |

## Non-negotiable leakage rules

Features and eligibility end at `T`; the target starts strictly after `T`. Distinct baskets—not transaction lines—define return. Censored horizons are unknown and rejected. No random split, future basket/spend, overlapping target activity, full-year/future segment assignment, future-fitted preprocessing, pre-split balancing, duplicate household-snapshot row, threshold/calibration on lockbox, or repeated lockbox use is allowed.

## Open modeling decisions

Final features and transforms, missing-value policy, model candidates/tuning, class weighting, uncertainty method, intervention capacity/costs, operating threshold, calibration method, monitoring, and production artifact contract remain open. None may be resolved using the lockbox.
