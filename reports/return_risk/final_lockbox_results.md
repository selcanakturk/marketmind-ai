# Customer Return Risk — Final November Lockbox Results

> **THIS IS THE FIRST AND FINAL PLANNED EVALUATION ON THE NOVEMBER 30 COHORT.**
>
> **THE NOVEMBER 30 RETURN-RISK LOCKBOX IS NOW CONSUMED.**

## Frozen system and development evidence

The system was frozen before outcome access:

- entity: eligible Complete Journey grocery-retail household at November 30, 2017 23:59:59;
- positive class: `return_risk_target=1`, zero distinct baskets in `(T,T+28 days]`; not churn;
- eligibility: 90 history days, 5 distinct baskets, and 30 active-span days;
- features: exact frozen 16-feature order using information through `T`;
- model: unweighted Extra Trees ET-2—300 estimators, depth 12, minimum leaf 10, sqrt features, random state 42;
- output: uncalibrated return-risk ranking score;
- policy: deterministic top 10%, with top 5% and 20% descriptive scenarios;
- calibration and fixed threshold: none.

Development validation was PR-AUC 0.4827, ROC-AUC 0.8576, Brier 0.0916, and log loss 0.2944. These values and all choices were fixed before the lockbox was opened.

## Lockbox protocol and score-before-outcome ordering

ET-2 was trained on the predeclared April–August cohorts only—10,223 household-snapshot rows. September and October were not added. November features were built using transactions at or before November 30 only.

The evaluation then executed this irreversible order:

1. build the 2,322 eligible November feature rows;
2. generate unchanged ET-2 scores;
3. deterministically rank by descending score and household-key tie break;
4. freeze top-5%, top-10%, and top-20% flags;
5. save `november_lockbox_scores_preoutcome.csv` without a target column;
6. only then construct and join the December outcome;
7. save the final evaluation artifact.

The target interval is exactly `(2017-11-30 23:59:59, 2017-12-28 23:59:59]`. Complete observation through December 28 was verified; distinct baskets determine outcomes, and no censored row is labeled no-return.

## Lockbox cohort and metrics

- Eligible households: **2,322**
- No-return positives: **341**
- Return negatives: **1,981**
- Positive prevalence: **14.6856%**

| Model/score | PR-AUC | ROC-AUC | Brier | Log loss |
|---|---:|---:|---:|---:|
| **ET-2** | **0.4999** | **0.8691** | 0.0953 | 0.2995 |
| Recency baseline | 0.4591 | 0.8136 | not probability-calibrated | not probability-calibrated |
| Recency-frequency heuristic | 0.4994 | 0.8612 | not probability-calibrated | not probability-calibrated |

Brier and log loss describe raw, uncalibrated ET-2 outputs. They do not change score semantics.

ET-2 exceeds recency by 0.04083 PR-AUC and 0.05549 ROC-AUC. Versus the heuristic, it is nearly tied but slightly higher: +0.000523 PR-AUC and +0.007873 ROC-AUC. This confirms competitiveness rather than a large primary-metric advantage.

## Frozen capacity policy

| Policy | Flagged | Positives captured | Precision | Recall | Lift |
|---|---:|---:|---:|---:|---:|
| Top 5% | 117 | 66 | 0.5641 | 0.1935 | 3.84× |
| **Top 10%** | **233** | **129** | **0.5536** | **0.3783** | **3.77×** |
| Top 20% | 465 | 216 | 0.4645 | 0.6334 | 3.16× |

The frozen top-10% policy was applied unchanged. Positive prevalence among flagged households is the reported precision, 55.36%. No new capacity or score threshold was selected.

## Generalization gap

| Metric | Development | Lockbox | Absolute gap | Relative gap |
|---|---:|---:|---:|---:|
| PR-AUC | 0.4827 | 0.4999 | +0.0173 | +3.58% |
| ROC-AUC | 0.8576 | 0.8691 | +0.0115 | +1.34% |
| Brier | 0.0916 | 0.0953 | +0.0037 | +3.99% |
| Log loss | 0.2944 | 0.2995 | +0.0051 | +1.74% |

Ranking improves while raw score losses worsen modestly, partly alongside prevalence increasing from roughly 13.8% to 14.69%. This is a generalization gap, not automatic evidence of overfitting or improvement in the population.

## Ranking generalization assessment

ET-2 PR-AUC is 3.40 times the 0.1469 no-skill prevalence reference, ROC-AUC remains 0.8691, and the frozen top 10% concentrates positives at 3.77 times base prevalence. ET-2 remains slightly ahead of the heuristic in both PR-AUC and ROC-AUC, although their PR-AUC difference is negligible. The score distribution has no pathology.

Under the predeclared qualitative rubric, this is **STRONG GENERALIZATION**: ranking is clearly useful, competitive with the frozen heuristic, operational concentration remains strong, and no score failure appears. “Strong” describes this held-out cohort only and does not authorize retuning or causal/business-impact claims.

## Segment post-hoc analysis

The frozen segmentation artifact assigned households using behavior available through November 30. Segment was never used by ET-2.

| Segment | Households | Positives | Prevalence | Median score | Top-10 flags | Share of all flags |
|---|---:|---:|---:|---:|---:|---:|
| High-Engagement Broad | 1,186 | 56 | 4.72% | 0.0213 | 3 | 1.29% |
| Promotion Basket Builders | 291 | 29 | 9.97% | 0.0488 | 11 | 4.72% |
| Lower-Engagement Focused | 845 | 256 | 30.30% | 0.2250 | 219 | 93.99% |

The concentration in Lower-Engagement Focused households persists and should be monitored operationally. These are descriptive behavioral groups, not protected classes or causal explanations.

## Score sanity

| Check | Result |
|---|---:|
| Eligible scores | 2,322 |
| Minimum / maximum | 0.00242 / 0.63763 |
| p05 / p25 / median / p75 / p95 | 0.00533 / 0.01684 / 0.06131 / 0.18998 / 0.41866 |
| NaN / infinite scores | 0 / 0 |
| Duplicate household IDs | 0 |

All scores lie in `[0,1]`, but remain uncalibrated ranking scores.

## Evaluation artifact

`reports/return_risk/artifacts/november_lockbox_scores.csv` contains only household ID, snapshot, frozen score/rank/flags, observed target, and post-hoc segment code. It contains no raw transactions. The separately persisted pre-outcome artifact proves the target-free scoring stage.

## Known limitations

This is one grocery-household month-end cohort in a short panel. Its higher positive prevalence and holiday-period behavior may not represent later deployment periods. Segment assignments use the frozen September segmentation artifact applied forward. Metrics are observational and do not measure intervention impact. The lockbox provides one final estimate, not permission for repeated testing.

## Lockbox consumption statement

**THE NOVEMBER 30 RETURN-RISK LOCKBOX IS NOW CONSUMED.** It must never again be treated as fresh validation for feature engineering, model selection, tuning, calibration, threshold or capacity selection, preprocessing changes, or policy redesign. Any weaknesses or hypotheses arising here belong to future data collection and independently designed evaluation—not optimization against November.
