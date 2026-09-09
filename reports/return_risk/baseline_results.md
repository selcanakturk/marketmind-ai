# Customer Return Risk — Leakage-Safe Baseline Results

## Frozen target and temporal cohorts

The prediction unit is a Complete Journey 2.0 **grocery-retail household at snapshot `T`**. Positive class `return_risk_target=1` means zero distinct baskets in the complete interval `(T,T+28 days]`; it is not contractual churn.

Training contains 10,223 repeated household-snapshot rows from April 30 through August 31, 2017. The same fitted baselines are evaluated without updating on September 30 (2,247 rows, 310 positives, 13.796%) and October 31 (2,282 rows, 315 positives, 13.804%), then summarized across 4,529 validation rows. There is no random split.

> **NOVEMBER LOCKBOX NOT ACCESSED.** The notebook snapshot constant ends on October 31 and asserts that November 30 is absent. No November target was constructed or inspected.

## Feature audit

The training-only candidate audit found no missing values. Important distribution findings include:

- `recency_days`: median 4, p95 42, skew 3.67, 16.72% zero;
- lifetime baskets: median 26, p95 106.9, skew 4.00;
- lifetime spend: median 739.64, p95 3,267.83, skew 2.58;
- 28-day baskets: median 4, p95 17, 9.33% zero;
- 28-day spend: median 107.29, p95 538.50, 9.37% zero;
- coupon-basket rate: median 2.08%, 44.98% zero, skew 2.91;
- 28-day basket/spend changes are signed and approximately centered at zero.

Training Spearman redundancy was strong for lifetime baskets–active days (0.992), lifetime spend–unique products (0.946), active days–active weeks (0.945), lifetime baskets–mean cadence (0.942), mean–standard-deviation cadence (0.928), 28–56-day baskets (0.924), 28–56-day spend (0.917), median–mean cadence (0.917), and active span–active months (0.899).

The complete audit is in `artifacts/feature_audit.csv`. Feature decisions used point-in-time validity, conceptual role, distribution quality, and training redundancy only—not validation outcomes.

## Final baseline feature set

The frozen ordered Logistic baseline contains 16 features:

1. `recency_days`
2. `basket_frequency_lifetime`
3. `monetary_lifetime`
4. `average_basket_value`
5. `baskets_last_7d`
6. `baskets_last_28d`
7. `spend_last_28d`
8. `median_days_between_baskets`
9. `std_days_between_baskets`
10. `active_span_days`
11. `unique_departments`
12. `department_spend_hhi`
13. `discount_share_of_gross`
14. `coupon_basket_rate`
15. `baskets_28d_change`
16. `spend_28d_change`

`days_since_last_basket` was identical to recency and removed. The audit also removed 14/56-day basket duplicates, 56-day spend, mean cadence, active days/weeks/months, unique products, and discounted-basket rate. Seven-day and 28-day baskets retain distinct immediate and horizon-aligned meanings. Signed changes avoid unstable zero-denominator ratios.

## Transformations and preprocessing

Fixed `log1p` is applied to nonnegative heavy-tailed magnitudes: recency, lifetime baskets/spend, average basket value, 7/28-day baskets, 28-day spend, median/std cadence, active span, and unique departments. Bounded ratios and signed changes remain unchanged. `RobustScaler` is fitted on April–August only inside the Logistic pipeline; validation is transform-only.

## Behavioral baselines

The recency baseline is a training empirical-rank score where greater recency means greater risk. The exactly-one heuristic is fixed before validation as `sigmoid(z(recency) - z(log1p(lifetime baskets)))`, using equal weights and training-only means/scales.

| Baseline | Cohort | PR-AUC | ROC-AUC | Prevalence |
|---|---|---:|---:|---:|
| Recency | September | 0.4355 | 0.7829 | 0.1380 |
| Recency | October | 0.4303 | 0.7918 | 0.1380 |
| Recency | Pooled | 0.4316 | 0.7870 | 0.1380 |
| Recency-frequency heuristic | September | **0.4864** | 0.8537 | 0.1380 |
| Recency-frequency heuristic | October | **0.4563** | 0.8394 | 0.1380 |
| Recency-frequency heuristic | Pooled | **0.4688** | 0.8459 | 0.1380 |

Both materially exceed the 0.138 prevalence/no-skill PR reference. Their bounded outputs are behavioral scores, not calibrated probabilities; their threshold-0.5, Brier, and log-loss values in the artifact are descriptive scale diagnostics only.

## Logistic Regression and class-weight comparison

Exactly two untuned variants use `solver="lbfgs"`, `max_iter=2000`, `random_state=42`, default `C`, and either `class_weight=None` or `"balanced"`. Both converged.

| Variant | Cohort | PR-AUC | ROC-AUC | Log loss | Brier |
|---|---|---:|---:|---:|---:|
| Unweighted | September | 0.4773 | 0.8591 | 0.2915 | 0.0904 |
| Unweighted | October | 0.4471 | 0.8426 | 0.3044 | 0.0952 |
| Unweighted | Pooled | **0.4586** | **0.8508** | **0.2980** | **0.0929** |
| Balanced | September | 0.4714 | 0.8588 | 0.5357 | 0.1790 |
| Balanced | October | 0.4387 | 0.8411 | 0.5530 | 0.1856 |
| Balanced | Pooled | 0.4531 | 0.8500 | 0.5444 | 0.1823 |

At diagnostic threshold 0.5, unweighted Logistic has precision 0.5429, recall 0.2432, F1 0.3359, and confusion matrix `[[3776,128],[473,152]]`. Balanced Logistic shifts many more scores above 0.5: precision 0.3230, recall 0.8512, F1 0.4683, and `[[2789,1115],[93,532]]`. This is a class-weight effect, not a selected operating policy.

The unweighted variant ranks slightly better and has substantially better loss/calibration diagnostics. Balanced weighting does not improve PR-AUC and grossly raises the score level, so the unweighted baseline is the preferred Logistic reference. No final classifier is frozen.

## September versus October

Prevalence is essentially unchanged, but performance weakens in October:

- heuristic PR-AUC falls 0.4864 → 0.4563 and ROC-AUC 0.8537 → 0.8394;
- unweighted Logistic PR-AUC falls 0.4773 → 0.4471 and ROC-AUC 0.8591 → 0.8426;
- balanced Logistic PR-AUC falls 0.4714 → 0.4387 and ROC-AUC 0.8588 → 0.8411.

Unweighted score distributions are stable (mean 0.1345 vs 0.1350; median 0.0535 vs 0.0549), so the metric decline is not explained by a large marginal score shift. October remains part of validation and demonstrates forward instability that a later nonlinear experiment must address rather than hide.

## Calibration diagnostics

Unweighted Logistic’s pooled mean score is near prevalence and its upper quantile bin averages 0.5456 versus 0.4923 observed; middle bins show smaller under/over-estimation. Its Brier score is 0.0929. Household-bootstrap 95% intervals are PR-AUC `[0.4104,0.5038]` and ROC-AUC `[0.8320,0.8664]`.

Balanced Logistic is not calibrated to prevalence: validation mean scores are about 0.386 despite 0.138 prevalence, and its highest bin averages 0.9173 versus 0.4680 observed. Its Brier score doubles to 0.1823. No calibrator was fit, and neither output is described as a calibrated probability.

## Capacity analysis

For unweighted Logistic on pooled validation:

| Highest-risk capacity | Selected | Positives captured | Precision | Recall |
|---:|---:|---:|---:|---:|
| 5% | 227 | 129 | 0.5683 | 0.2064 |
| 10% | 453 | 223 | 0.4923 | 0.3568 |
| 20% | 906 | 381 | 0.4205 | 0.6096 |

These are intervention-capacity diagnostics, not business impact and not frozen thresholds.

## Error and feature patterns

Validation non-returners versus returners have median recency 25 versus 4 days, lifetime baskets 15 versus 43, 28-day baskets 1 versus 4, 28-day spend 5.00 versus 111.96, median cadence 9.21 versus 4.44 days, and cadence standard deviation 15.75 versus 6.13 days. These are descriptive associations.

At the unweighted 0.5 diagnostic cutoff, false negatives remain partially active: median recency 15 days and one recent basket, compared with true positives at 61 days and zero recent baskets. False positives resemble long-inactive sparse households but nevertheless return. This explains why a high 0.5 cutoff misses many harder positive cases and why threshold selection must remain capacity/cost based.

## Repeated-household dependence

Pooled rows are not treated as IID. A deterministic 300-replicate clustered bootstrap resamples households while retaining their repeated snapshots. Snapshot-specific metrics are reported separately. A future inferential analysis may expand uncertainty work, but household dependence is not silently ignored.

## Leakage protections and known limitations

- All features use `transaction_timestamp <= T`; recent windows are `(T-w,T]`.
- Previous activity is `(T-56,T-28]` and cannot overlap the target.
- Targets use distinct baskets in `(T,T+28]`; positive remains no return.
- Training alone determines feature audit, transforms, scaler statistics, and heuristic standardization.
- September and October are transform-only validation with the same fitted model.
- No segmentation feature, SMOTE, other resampling, random split, tuning, nonlinear model, or calibration fit was used.
- No November outcome, threshold selection, or model selection used the lockbox.

The dataset is a short grocery-household panel, repeated rows are dependent, and behavior may vary seasonally. Observational feature associations are not causal. Threshold value cannot be judged without intervention capacity and costs.

## Decision for next experiment

Logistic Regression adds a small ROC-AUC improvement over the heuristic (0.8508 versus 0.8459) but **does not beat it on primary pooled PR-AUC** (0.4586 versus 0.4688). It therefore provides limited incremental value rather than a clear baseline win. The recency-frequency heuristic remains the benchmark; unweighted Logistic is the learned reference because it dominates the balanced variant on PR-AUC and calibration diagnostics.

After review, a single narrowly specified nonlinear model may be tested under the same frozen cohorts/features or a separately predeclared compact extension. Hyperparameter scope, selection rule, threshold policy, and calibration strategy remain unresolved. November must stay sealed.
