# Customer Return Risk — Controlled Nonlinear Challenger

## Objective and frozen design

This experiment asks whether one lightweight nonlinear family improves positive-class ranking beyond the frozen recency-frequency heuristic. The target remains `return_risk_target=1` for zero distinct baskets in `(T,T+28 days]`; this is grocery-household return risk, not contractual churn.

The exact 16 Step 2 features and eligibility rules are unchanged. April–August 2017 supplies 10,223 training rows. Each candidate is fit once and evaluated unchanged on September (2,247 rows; 13.796% positive), October (2,282; 13.804%), and their 4,529-row pool. Raw engineered values enter HGB without scaling. All 16 features have zero training and validation missingness.

> **NOVEMBER LOCKBOX NOT ACCESSED.** The analysis constant contains only April–October and explicitly excludes the November 30 lockbox. No lockbox outcome was constructed, scored, or inspected.

## Model family and predeclared candidates

`sklearn.ensemble.HistGradientBoostingClassifier` is the only nonlinear family tested. It supports nonlinear tabular effects and interactions without a new external dependency. All candidates are unweighted with `early_stopping=False` and `random_state=42`; there is no sampling, feature extension, or tuning beyond the five frozen configurations.

| Candidate | Learning rate | Iterations | Max leaves | Min leaf rows | L2 |
|---|---:|---:|---:|---:|---:|
| HGB-1 | 0.05 | 150 | 15 | 50 | 1.0 |
| HGB-2 | 0.05 | 200 | 31 | 50 | 1.0 |
| HGB-3 | 0.03 | 250 | 31 | 50 | 1.0 |
| HGB-4 | 0.05 | 200 | 31 | 100 | 1.0 |
| HGB-5 | 0.05 | 200 | 15 | 50 | 5.0 |

The predeclared policy requires pooled PR-AUC above 0.4688, no severe September–October instability, and calibration not catastrophically worse than unweighted Logistic. When candidates are within 1% relative PR-AUC, the simpler/smaller configuration is preferred unless temporal stability clearly favors another.

## Temporal validation results

| Candidate | Cohort | PR-AUC | ROC-AUC | Brier | Log loss |
|---|---|---:|---:|---:|---:|
| HGB-1 | September | **0.4844** | **0.8663** | **0.0890** | **0.2859** |
| HGB-1 | October | **0.4531** | **0.8487** | **0.0936** | **0.3004** |
| HGB-1 | Pooled | **0.4672** | **0.8574** | **0.0913** | **0.2932** |
| HGB-2 | September | 0.4561 | 0.8585 | 0.0924 | 0.2963 |
| HGB-2 | October | 0.4278 | 0.8441 | 0.0958 | 0.3093 |
| HGB-2 | Pooled | 0.4412 | 0.8512 | 0.0941 | 0.3029 |
| HGB-3 | September | 0.4596 | 0.8609 | 0.0915 | 0.2924 |
| HGB-3 | October | 0.4389 | 0.8456 | 0.0949 | 0.3054 |
| HGB-3 | Pooled | 0.4479 | 0.8531 | 0.0932 | 0.2989 |
| HGB-4 | September | 0.4638 | 0.8604 | 0.0917 | 0.2957 |
| HGB-4 | October | 0.4302 | 0.8452 | 0.0960 | 0.3097 |
| HGB-4 | Pooled | 0.4460 | 0.8527 | 0.0939 | 0.3028 |
| HGB-5 | September | 0.4718 | 0.8631 | 0.0901 | 0.2885 |
| HGB-5 | October | 0.4457 | 0.8467 | 0.0944 | 0.3019 |
| HGB-5 | Pooled | 0.4578 | 0.8549 | 0.0923 | 0.2953 |

HGB-1 is both the raw PR-AUC leader and the simplest candidate. HGB-5 is 2.02% relatively below it; therefore the within-1% simplicity rule does not alter selection. Larger 31-leaf candidates are consistently worse.

## Baseline comparison

| Method | Pooled PR-AUC | Pooled ROC-AUC | Brier | Log loss |
|---|---:|---:|---:|---:|
| Recency | 0.4316 | 0.7870 | — | — |
| Recency-frequency heuristic | **0.4688** | 0.8459 | — | — |
| Unweighted Logistic | 0.4586 | 0.8508 | 0.0929 | 0.2980 |
| Balanced Logistic | 0.4531 | 0.8500 | 0.1823 | 0.5444 |
| HGB-1 | 0.4672 | **0.8574** | **0.0913** | **0.2932** |

Versus the primary heuristic benchmark, HGB-1 changes PR-AUC by **−0.001585 absolute** and **−0.338% relative**. Versus unweighted Logistic it improves PR-AUC by 0.00858, ROC-AUC by 0.00660, Brier by 0.00153, and log loss by 0.00478. It improves the learned reference, but does not clear the required simple-behavior benchmark.

## Household-clustered uncertainty

The deterministic 300-replicate household-clustered bootstrap gives HGB-1 pooled intervals:

- PR-AUC 95% interval: `[0.4219, 0.5092]`;
- ROC-AUC 95% interval: `[0.8413, 0.8711]`.

Repeated snapshots are retained together during resampling; household-snapshot rows are not treated as IID. The interval overlaps the heuristic point estimate and does not reverse the predeclared observed-score gate.

## Calibration diagnostics

HGB-1 has pooled Brier 0.0913 and log loss 0.2932, slightly better than unweighted Logistic. Mean scores are 0.1420 in September and 0.1415 in October versus prevalence near 0.138. Medians are 0.0535 and 0.0512; 10th/90th percentiles are approximately 0.0018/0.4558 and 0.0018/0.4532. The score distribution is highly stable.

September’s highest quantile averages 0.5621 with 0.5556 observed; October’s averages 0.5577 with 0.4934 observed. Lower/middle bins also move unevenly. HGB-1 is not catastrophically worse than Logistic, but October shows some upper-tail overestimation alongside ranking degradation. No calibrator was fitted and raw HGB outputs remain **uncalibrated probability estimates/risk scores**, not calibrated probabilities.

## Capacity and threshold diagnostics

| Model | Capacity | Precision | Recall |
|---|---:|---:|---:|
| HGB-1 | 5% | 0.5639 | 0.2048 |
| HGB-1 | 10% | 0.5210 | 0.3776 |
| HGB-1 | 20% | 0.4294 | 0.6224 |
| Unweighted Logistic | 5% | 0.5683 | 0.2064 |
| Unweighted Logistic | 10% | 0.4923 | 0.3568 |
| Unweighted Logistic | 20% | 0.4205 | 0.6096 |
| Heuristic | 5% | **0.5947** | **0.2160** |
| Heuristic | 10% | **0.5408** | **0.3920** |
| Heuristic | 20% | 0.4183 | 0.6064 |

HGB-1 improves on Logistic at 10% and 20% capacity but trails the heuristic at 5% and 10%. At 20% it captures ten more positives than the heuristic. These are capacity simulations, not business-impact estimates.

Diagnostic HGB-1 thresholds from 0.10 through 0.50 produce precision 0.306→0.532 and recall 0.888→0.291. The best displayed F1 occurs near 0.30, but this is exploratory and **no threshold is selected or frozen**.

## Temporal stability

HGB-1 PR-AUC falls 0.0313 from September to October and ROC-AUC falls 0.0176, while prevalence and marginal scores are essentially unchanged. Calibration’s upper bin also changes from close alignment to overestimation. October deterioration therefore reflects mainly ranking degradation plus a modest calibration shift—not a broad score-distribution shift. October remains fully reported.

## Error analysis

At the diagnostic 0.5 threshold, HGB-1 produces 182 true positives, 160 false positives, 3,744 true negatives, and 443 false negatives. True positives have median recency 75 days, 8 lifetime baskets, zero 28-day baskets, and zero recent spend. False positives are similarly inactive—median recency 65, 9 lifetime baskets, zero recent activity—but subsequently return. False negatives are harder cases: median recency 13 days, 17 lifetime baskets, one recent basket, and recent spend 20.30.

The unresolved errors occur among households with partially conflicting activity/cadence signals. These descriptions are associative, contain no raw household identifiers, and do not establish causes.

## Compute and artifact-size estimates

| Candidate | Fit seconds | Predict seconds, 4,529 rows | Serialized KiB |
|---|---:|---:|---:|
| HGB-1 | 0.517 | 0.0077 | 290.6 |
| HGB-2 | 0.906 | 0.0101 | 728.8 |
| HGB-3 | 1.195 | 0.0151 | 904.6 |
| HGB-4 | 0.854 | 0.0115 | 728.8 |
| HGB-5 | 0.477 | 0.0124 | 378.8 |

All are lightweight. HGB-1’s metric advantage, not merely its footprint, makes it the strongest candidate. Sizes are in-memory research serialization estimates; no production artifact was written.

## Selection decision

HGB-1 satisfies the temporal-stability and calibration safeguards but fails the first mandatory condition: pooled PR-AUC does not exceed 0.4688. **HGB therefore does not meaningfully beat the heuristic under the predeclared policy.** HGB-1 is the best nonlinear research candidate, but the classifier family is **not frozen** and threshold/calibration work must not begin as though model selection were complete.

Feature extension is not currently justified merely to recover a 0.34% relative shortfall. The error profiles do not reveal an obviously absent point-in-time feature family: recency, cadence, frequency, recent activity, and change are already represented. Any extension would need a predeclared business/measurement rationale rather than metric chasing.

## Known limitations and next decision

Complete Journey is a short grocery-household panel with repeated observations and limited seasonal replication. Model comparisons are development estimates, raw scores are not calibrated, and feature associations are not causal. The five configurations are intentionally narrow and provide no exhaustive HGB optimization claim.

The next review should decide whether to retain the simpler heuristic as the operational benchmark, authorize one methodologically motivated feature study, or stop nonlinear development. No final classifier, threshold, calibration method, or production artifact is approved. The November lockbox remains sealed.
