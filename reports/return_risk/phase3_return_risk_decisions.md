# Phase 3 Return Risk Decisions

Status: Step 4 final family resolution complete; Extra Trees / ET-2 is frozen as the learned ranking approach, but no calibrated model, threshold, or production artifact exists.

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

## Step 3 nonlinear challenger decisions

| Decision | Outcome |
|---|---|
| Family | `HistGradientBoostingClassifier` only; raw frozen features, unweighted |
| Candidates | exactly HGB-1 through HGB-5 as specified in `models.py`; no expansion |
| Best candidate | HGB-1: LR 0.05, 150 iterations, 15 leaves, min leaf 50, L2 1.0 |
| HGB-1 September | PR-AUC 0.4844; ROC-AUC 0.8663; Brier 0.0890; log loss 0.2859 |
| HGB-1 October | PR-AUC 0.4531; ROC-AUC 0.8487; Brier 0.0936; log loss 0.3004 |
| HGB-1 pooled | PR-AUC 0.4672; ROC-AUC 0.8574; Brier 0.0913; log loss 0.2932 |
| Heuristic gate | not beaten: −0.001585 absolute / −0.338% relative PR-AUC |
| Logistic comparison | HGB-1 improves pooled PR-AUC by 0.00858 and ROC-AUC by 0.00660 |
| Bootstrap | HGB-1 PR-AUC `[0.4219,0.5092]`; ROC-AUC `[0.8413,0.8711]` |
| Model-family status | not frozen because the mandatory heuristic PR-AUC gate failed |
| Feature extension | not currently justified solely to chase the narrow shortfall |
| Calibration | diagnostics only; HGB raw output remains uncalibrated |
| Threshold | unresolved and not frozen |
| Lockbox | November outcomes remain sealed |

## Step 4 final family resolution

| Decision | Frozen outcome |
|---|---|
| Final challenger | exactly ET-1, ET-2, ET-3 using raw frozen features; no weights or resampling |
| Best Extra Trees | ET-2: 300 trees, depth 12, leaf 10, sqrt features, unweighted, random state 42 |
| ET-2 September | PR-AUC 0.4989; ROC-AUC 0.8647; Brier 0.0901; log loss 0.2894 |
| ET-2 October | PR-AUC 0.4695; ROC-AUC 0.8506; Brier 0.0932; log loss 0.2993 |
| ET-2 pooled | PR-AUC 0.4827; ROC-AUC 0.8576; Brier 0.0916; log loss 0.2944 |
| Heuristic comparison | +0.013871 absolute / +2.959% relative PR-AUC; gate passed |
| HGB comparison | +0.015456 absolute / +3.31% relative PR-AUC |
| Selected family/config | Extra Trees / ET-2; model-family search closed |
| Simple fallback | frozen recency-frequency heuristic remains benchmark and fallback |
| Output | uncalibrated return-risk score / estimate for ranking, not calibrated probability |
| Threshold/calibration | both remain open; 0.5 diagnostics are not decisions |
| Lockbox | November outcomes remain sealed |

## Open modeling decisions

Development-only calibration strategy, intervention capacity/costs, operating threshold, monitoring, and production contracts remain unresolved. No further family/feature search is authorized absent a methodological defect. None may be resolved using the lockbox.
