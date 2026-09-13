# Customer Return Risk — Calibration and Operational Policy

## Frozen model and calibration protocol

The model family and configuration remain Extra Trees ET-2: 300 estimators, depth 12, minimum leaf size 10, `max_features="sqrt"`, no class weight, `n_jobs=-1`, and random state 42. The target remains `return_risk_target=1` for zero distinct baskets in `(T,T+28 days]`; this is not contractual churn.

Calibration preserves temporal ordering:

- base ET-2 fit: April–July 2017, 8,004 household-snapshot rows;
- calibration fit: August 31 only, 2,219 rows;
- final development assessment: September and October, 4,529 rows;
- calibrators: none, sigmoid/Platt, and isotonic only.

September/October were previously used for family selection; their reuse is acknowledged. They are assessment-only here and do not fit either calibrator. The full 16-feature contract is unchanged.

> **NOVEMBER LOCKBOX REMAINS UNTOUCHED.** No November label, score, calibrator input, threshold analysis, segment analysis, or policy metric was constructed.

## Calibration results

| Approach | Cohort | PR-AUC | ROC-AUC | Brier | Log loss | ECE-10 |
|---|---|---:|---:|---:|---:|---:|
| Uncalibrated | September | **0.5010** | **0.8644** | 0.0917 | **0.2932** | 0.0320 |
| Uncalibrated | October | **0.4713** | **0.8502** | 0.0944 | **0.3023** | 0.0274 |
| Uncalibrated | Pooled | **0.4850** | **0.8572** | 0.0930 | **0.2977** | 0.0287 |
| Sigmoid | September | 0.5010 | 0.8644 | 0.0903 | 0.2995 | 0.0433 |
| Sigmoid | October | 0.4713 | 0.8502 | 0.0935 | 0.3094 | 0.0365 |
| Sigmoid | Pooled | 0.4850 | 0.8572 | 0.0919 | 0.3045 | 0.0384 |
| Isotonic | September | 0.4737 | 0.8629 | **0.0892** | 0.3529 | **0.0105** |
| Isotonic | October | 0.4414 | 0.8476 | **0.0926** | 0.3385 | **0.0149** |
| Isotonic | Pooled | 0.4568 | 0.8552 | **0.0909** | 0.3456 | **0.0119** |

These uncalibrated metrics differ slightly from Step 4 because the base estimator intentionally excludes August so that August can serve as a temporally later calibration cohort.

### Calibration decision

**No calibrator is selected.** Sigmoid preserves ranking and improves pooled Brier by 0.00113, but worsens log loss by 0.00673 and ECE by 0.00974, with the same direction in both months. Isotonic improves Brier/ECE but lowers pooled PR-AUC by 0.02818 and worsens log loss by 0.04787; its stepwise ties and single-cohort fit damage ranking and suggest August overfit.

The required combination of material loss improvement, preserved ranking, and stable temporal behavior is not met. Calibration is not forced for cosmetic probability output.

## Temporal calibration stability

Uncalibrated and sigmoid rankings are identical because sigmoid is monotonic. PR-AUC declines from 0.5010 in September to 0.4713 in October, and ROC-AUC from 0.8644 to 0.8502. Uncalibrated Brier/log loss worsen from 0.0917/0.2932 to 0.0944/0.3023. Sigmoid exhibits the same ranking shift and worse log loss/ECE in both months. Isotonic has the largest PR-AUC decline and unstable loss tradeoff.

The selected uncalibrated score remains useful for ranking, but the monthly changes reinforce capacity-based operations and monitoring rather than a universal probability cutoff.

## Threshold analysis

The pooled deterministic grid from 0.05 to 0.50 is diagnostic only. At score 0.20, precision is 0.4167, recall 0.6480, F1 0.5072, and 21.46% of rows are flagged—the largest displayed F1. At 0.30, precision increases to 0.5170 while recall falls to 0.4144 and 11.06% are flagged. At 0.50, only 0.95% are flagged and recall collapses to 0.0464.

No threshold is frozen. Accuracy was not used, F1 was not treated as the sole objective, and raw score 0.5 has no calibrated semantic meaning.

## Capacity analysis

Selected uncalibrated ET-2:

| Cohort | Capacity | Flagged | Precision | Recall | Lift vs prevalence |
|---|---:|---:|---:|---:|---:|
| September | 5% | 113 | 0.6106 | 0.2226 | 4.43× |
| September | 10% | 225 | 0.5511 | 0.4000 | 3.99× |
| September | 15% | 338 | 0.4852 | 0.5290 | 3.52× |
| September | 20% | 450 | 0.4467 | 0.6484 | 3.24× |
| October | 5% | 115 | 0.6000 | 0.2190 | 4.35× |
| October | 10% | 229 | 0.5109 | 0.3714 | 3.70× |
| October | 15% | 343 | 0.4636 | 0.5048 | 3.36× |
| October | 20% | 457 | 0.4114 | 0.5968 | 2.98× |
| Pooled | 5% | 227 | 0.6035 | 0.2192 | 4.37× |
| Pooled | **10%** | **453** | **0.5298** | **0.3840** | **3.84×** |
| Pooled | 15% | 680 | 0.4750 | 0.5168 | 3.44× |
| Pooled | 20% | 906 | 0.4294 | 0.6224 | 3.11× |

Capacity is stable in workload by construction, and performance degrades gradually rather than collapsing in October.

## Business policy scenarios

- **Conservative outreach:** top 5% of eligible households; roughly 60% validation precision and 22% recall.
- **Balanced monitoring — default:** top 10%; 53.0% pooled precision, 38.4% recall, and 3.84× lift, with September/October precision of 55.1%/51.1%.
- **Broad retention campaign:** top 20%; 42.9% pooled precision and 62.2% recall.

These are generic workload scenarios, not monetary or causal impact estimates.

## Threshold versus capacity decision

**Top-capacity ranking is the primary operational policy.** It fixes workload and does not pretend an uncalibrated score has stable probability meaning. A score threshold would allow volume to vary with drift and cannot offer stable semantics without defensible calibration.

The frozen default is: **at each scoring run, rank all eligible households by uncalibrated ET-2 return-risk score and flag the top 10%; resolve exact ties deterministically by stable household key.** Top 5% and top 20% remain predefined conservative/broad alternatives for capacity planning. No score threshold is operationally frozen.

## Segmentation post-hoc analysis

The September segmentation artifact is applied at September using history through September and at October using history through October. Assignment keys must match each risk snapshot. Segment never enters ET-2.

| Segment | Rows | No-return prevalence | PR-AUC | Mean / median score | Top-10 flags | Share of flags |
|---|---:|---:|---:|---:|---:|---:|
| High-Engagement Broad | 2,228 | 4.13% | 0.2058 | 0.0357 / 0.0166 | 6 | 1.32% |
| Promotion Basket Builders | 577 | 10.40% | 0.4251 | 0.0935 / 0.0460 | 37 | 8.17% |
| Lower-Engagement Focused | 1,724 | 27.44% | 0.5306 | 0.2147 / 0.1949 | 410 | 90.51% |

All segments contain both classes and support descriptive PR-AUC. Within-segment top-10 flag rates are 0.27%, 6.41%, and 23.78%, respectively.

## Operational coverage analysis

The Lower-Engagement Focused group dominates high-risk flags in both months: 204 of 227 September flags and 206 of 226 October flags. High-Engagement Broad households are nearly never selected—three per month—while their observed no-return prevalence rises from 3.25% to 4.95%. Promotion Basket Builders receive 20 and 17 flags.

This concentration is consistent with descriptive behavioral risk differences, but it must be monitored. It is an operational coverage check, not protected-attribute fairness analysis. Segment-specific scores, flags, or prevalence do not establish causality or justify different treatment without business review.

## Household-clustered uncertainty

Three hundred deterministic household-cluster resamples for the selected score/policy give:

- PR-AUC 95% interval `[0.4345,0.5294]`;
- ROC-AUC 95% interval `[0.8400,0.8713]`;
- top-10% precision 95% interval `[0.4735,0.5811]`.

Repeated snapshots remain grouped; capacity selection is recalculated inside each replicate.

## Frozen operational policy and output semantics

- Model: ET-2, unchanged.
- Calibration: none.
- Output: **uncalibrated return-risk score**, used for relative ranking.
- Default intervention policy: deterministic top 10% of eligible households per scoring run.
- Secondary capacity scenarios: top 5% conservative and top 20% broad.
- Fixed score threshold: none.
- Segmentation: post-hoc monitoring only, never predictive input.

The score must not be called a probability, confidence, probability of churn, or calibrated risk probability.

## Known limitations and lockbox status

The source is a short grocery-household panel with repeated observations and limited seasonality. August calibration is a single cohort. September/October assessment reuses cohorts involved in family selection, so metrics are development evidence rather than an independent final estimate. Segment coverage reflects behavioral clusters, not protected classes. Capacity performance may drift when prevalence or collection changes.

The model plus operational policy are ready to freeze before one-time lockbox evaluation. Productionization has not begun. **November remains sealed.**
