# Controlled Isolation Forest challenger results

> **ANOMALY LOCKBOX REMAINS UNTOUCHED.** No `d_1914–d_1941` forecast, residual, scale, Isolation Forest score, robust score, alert, injection, ranking, or artifact was produced.

## Frozen baseline and challenger rationale

The reference remains the per-series robust residual score with statistical threshold `|score| ≥ 3` and an independent top-5/day review queue. The sole challenger asks whether a compact multivariate Isolation Forest adds useful ranking signal. It cannot replace the baseline merely through complexity, and its score is not a probability.

## Features and score semantics

The exact ordered feature vector is: robust residual score, signed residual, absolute residual, expected sales, sine weekday, cosine weekday, event-present indicator, and applicable state SNAP flag. Inputs are finite; a rare undefined robust score receives a neutral zero representation while its baseline undefined state remains separate. Store, department, state identity, prices, item metadata, future features, and causal labels are excluded.

The IF score is `-IsolationForest.score_samples(X)`, so larger values mean more isolated/more anomalous. Direction remains exclusively `spike` or `drop` from the signed robust residual; the IF score itself is directionless.

## Temporal protocol

Every scored block gets a newly fitted IF using only complete earlier OOS blocks:

| Scored block | IF training corpus | Rows |
|---|---|---:|
| DEV-1 | scale seed | 1,960 |
| DEV-2 | seed + DEV-1 | 3,920 |
| DEV-3 | seed + DEV-1 + DEV-2 | 5,880 |
| DEV-4 | seed + DEV-1 + DEV-2 + DEV-3 | 7,840 |
| Validation | seed + all four development blocks | 9,800 |

The scored block never enters its own fit. Validation was excluded from configuration selection. Training-corpus robust features are normalized using only that complete prior corpus; scored rows retain their Step 2 block-frozen robust scores.

## Predeclared configurations

All use `contamination="auto"`, `max_features=1.0`, `bootstrap=False`, `random_state=42`, and `n_jobs=1`.

| Config | Trees | Max samples |
|---|---:|---:|
| IF-1 | 200 | auto |
| IF-2 | 300 | 512 |
| IF-3 | 300 | 1,024 |

No grid expansion occurred.

## Development authentic diagnostics

| Config | Mean block median | Mean IQR | Mean p95 | Mean p98 | Mean p99 | Maximum | Mean top-5 series count | Mean top-five-series concentration |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| IF-1 | 0.4586 | 0.0706 | 0.6022 | 0.6529 | 0.6799 | 0.7440 | 24.00 | 56.43% |
| IF-2 | 0.4526 | 0.0714 | 0.5952 | 0.6454 | 0.6735 | 0.7463 | 25.25 | 56.43% |
| IF-3 | 0.4459 | 0.0697 | 0.5882 | 0.6398 | 0.6706 | 0.7471 | 27.00 | 53.39% |

IF-3 block medians remained 0.4399–0.4515 and IQRs 0.0546–0.0834. Its daily top-five lists covered 22–31 series per block, indicating reasonably stable scores but meaningful repeated concentration.

## Engineered development results

Percentages below use prior-training IF score quantiles, never injected cases, to define entry into the top 5% and top 2%.

| Config | Magnitude | Mean IF-score increase | Prior top 5% entry | Prior top 2% entry | Direction correctness |
|---|---:|---:|---:|---:|---:|
| IF-1 | 2× | 0.1104 | 50.00% | 31.04% | 97.71% |
| IF-1 | 4× | 0.1648 | 79.38% | 64.79% | 99.58% |
| IF-2 | 2× | 0.1142 | 52.08% | 32.71% | 97.71% |
| IF-2 | 4× | 0.1743 | 81.25% | 67.50% | 99.58% |
| **IF-3** | **2×** | **0.1196** | **52.29%** | **36.25%** | **97.71%** |
| **IF-3** | **4×** | **0.1863** | **83.96%** | **70.83%** | **99.58%** |

Expected sales, historical scales, and fitted IF objects were unchanged by injection. Families and non-overlapping locations exactly match Step 2.

## Development overlap with the robust baseline

Across 560 IF top-five/day rows per configuration:

| Config | Robust top-5 overlap | Overlap rate | IF top-5 also robust-threshold alerts | Spike/drop composition |
|---|---:|---:|---:|---:|
| IF-1 | 163 | 29.11% | 90 | 303 / 257 |
| IF-2 | 177 | 31.61% | 107 | 313 / 247 |
| IF-3 | 201 | 35.89% | 123 | 322 / 238 |

Disagreement is complementarity, not error. IF tends to prioritize absolute-scale/context isolation in addition to per-series robust deviation.

## Configuration selection

**IF-3 was selected using development only and frozen before validation.** It led both engineered ranking criteria at both magnitudes, covered the most series, had the lowest concentration, and overlapped the strong robust ranking most often. Its maximum observed serialized footprint, 11.84 MB, remained lightweight enough that IF-1's simplicity advantage did not outweigh IF-3's consistent evidence.

## Validation results

The frozen IF-3 fit used 9,800 prior rows and scored all 1,960 validation rows. Score median was 0.4422, IQR 0.0584, p95 0.5655, p98 0.6161, p99 0.6510, and maximum 0.7283.

Its 140 daily top-five rows covered 26 series, with the five most represented series contributing 55% and one series contributing at most 26 rows. Composition was 58 spike-direction and 82 drop-direction rows.

Only 36 of 140 IF and robust daily top-five rows overlapped (25.71%). Fourteen IF top-five rows were among the 25 frozen robust-threshold alerts, so IF surfaced 56% of those strong robust deviations while also producing a substantially different review ranking.

## Validation engineered confirmation

| Magnitude | Mean IF-score increase | Prior top 5% entry | Prior top 2% entry | Direction correctness |
|---|---:|---:|---:|---:|
| 2× | 0.1544 | 65.00% | 44.17% | 100% |
| 4× | 0.2109 | 88.33% | 83.33% | 100% |

The robust baseline's frozen threshold sensitivity on the same validation protocol was 74.17% and 97.50%, respectively. The definitions differ—IF quantile ranking versus a robust statistical boundary—but IF does not demonstrate superior sensitivity.

## Top authentic IF examples

| Date | Series | Actual | Expected | Residual | Robust score | IF score | Direction | Robust threshold |
|---|---|---:|---:|---:|---:|---:|---|---|
| 2016-04-09 | WI_2/FOODS_2 | 2,063 | 1,414.19 | 648.81 | 5.293 | 0.728 | spike | yes |
| 2016-04-01 | WI_2/HOUSEHOLD_1 | 1,869 | 1,185.57 | 683.43 | 4.852 | 0.722 | spike | yes |
| 2016-04-08 | WI_2/FOODS_3 | 3,093 | 2,537.79 | 555.21 | 2.691 | 0.711 | spike | no |
| 2016-04-24 | CA_3/FOODS_3 | 3,385 | 3,856.37 | -471.37 | -1.304 | 0.698 | drop | no |
| 2016-03-28 | CA_3/FOODS_3 | 2,433 | 2,909.49 | -476.49 | -1.320 | 0.692 | drop | no |

These are observed deviations and rankings, not causal diagnoses or verified anomalies.

## Complexity and limitations

Across four development fits, IF-1/2/3 required approximately 0.58/0.89/1.02 seconds; scoring required 0.087/0.130/0.148 seconds. Largest serialized models were 2.86/7.27/11.84 MB. The largest development feature matrix was about 0.48 MiB. Validation IF-3 fit took 0.319 seconds, scoring 0.037 seconds, feature memory about 0.60 MiB, and serialized size 11.23 MB.

M5 has no authentic anomaly labels, so overlap is not accuracy and complementary alerts are not proven useful. Raw residual and expected-sales inputs can favor high-volume series despite robust-score inclusion. Isolation Forest supplies no causal explanation, calibrated probability, or conventional feature importance. No SHAP analysis was performed.

## Final challenger decision

### **C — ISOLATION FOREST IS USEFUL ONLY AS A SECONDARY DIAGNOSTIC**

IF-3 is deterministic, lightweight, responsive to engineered changes, and surfaces complementary multivariate rankings. However, it is less interpretable than the signed robust score, has weaker validation engineered sensitivity under its ranking thresholds, concentrates repeatedly in some high-volume series, and lacks authentic labels that could validate its disagreements. The robust residual baseline remains primary. No ensemble or hybrid is authorized, and another detector family is not justified before genuinely new evidence or a specific operational need.

The robust statistical threshold remains **3**, the review capacity remains **top 5/day**, and the anomaly lockbox remains completely untouched.
