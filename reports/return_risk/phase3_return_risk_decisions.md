# Phase 3 Return Risk Decisions

Status: Step 2 leakage-safe baselines complete; no final classifier or production model is frozen.

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
| Baselines | recency rule, one recency/frequency heuristic, and unweighted/balanced Logistic evaluated in Step 2 |

## Step 2 baseline decisions

| Decision | Current outcome |
|---|---|
| Baseline features | 16 ordered features: recency; lifetime baskets/spend/average basket; 7/28-day baskets and 28-day spend; median/std cadence; active span; unique departments and department HHI; discount share and coupon-basket rate; 28-day basket/spend change |
| Transform | fixed `log1p` for nonnegative magnitude features; ratios and signed changes unchanged |
| Scaling | `RobustScaler`, fitted on April–August only |
| Behavioral baselines | training-rank recency; exactly one equal-weight `z(recency)-z(log-frequency)` heuristic |
| Logistic variants | default-C `lbfgs`, max_iter 2000, random state 42; unweighted and balanced only |
| Pooled recency | PR-AUC 0.4316; ROC-AUC 0.7870 |
| Pooled heuristic | PR-AUC 0.4688; ROC-AUC 0.8459 |
| Pooled unweighted Logistic | PR-AUC 0.4586; ROC-AUC 0.8508; Brier 0.0929 |
| Pooled balanced Logistic | PR-AUC 0.4531; ROC-AUC 0.8500; Brier 0.1823 |
| Temporal finding | all learned/combined scores weaken in October; October remains included |
| Logistic reference | unweighted preferred over balanced, but not frozen as final classifier |
| Calibration | diagnostic only; no calibrator; balanced scores substantially overstate prevalence |
| Threshold | unresolved; 0.5 and top-capacity analyses are descriptive only |
| Household dependence | snapshot metrics plus deterministic 300-replicate household-clustered bootstrap |
| Lockbox | November outcome not accessed |

## Non-negotiable leakage rules

Features and eligibility end at `T`; the target starts strictly after `T`. Distinct baskets—not transaction lines—define return. Censored horizons are unknown and rejected. No random split, future basket/spend, overlapping target activity, full-year/future segment assignment, future-fitted preprocessing, pre-split balancing, duplicate household-snapshot row, threshold/calibration on lockbox, or repeated lockbox use is allowed.

## Open modeling decisions

Nonlinear candidate specification, narrow tuning scope, model-selection rule, intervention capacity/costs, operating threshold, calibration method, monitoring, and production artifact contract remain open. Final model family is unresolved. None may be resolved using the lockbox.
