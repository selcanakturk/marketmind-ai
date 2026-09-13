# Robust residual anomaly baseline results

> **ANOMALY LOCKBOX REMAINS UNTOUCHED.** No forecast, residual, score, injection, alert, ranking, or outcome from `d_1914–d_1941` was created or inspected.

## Frozen methodology and OOS construction

The baseline operates on 70 department-store daily series. For every 28-day block, a new global Full Direct `HistGradientBoostingRegressor` used the unchanged Phase 1 features, weekly origin sampling, parameters, and nonnegative clipping. Training ended strictly before the scored block. The production model trained through `d_1941` was not loaded.

| Block | Train through | Score dates | Training rows | Total fit/forecast pipeline runtime |
|---|---:|---|---:|---:|
| Scale seed | `d_1465` | `d_1466–1493` | 388,080 | 12.97 s |
| DEV-1 | `d_1549` | `d_1550–1577` | 411,600 | 14.05 s |
| DEV-2 | `d_1633` | `d_1634–1661` | 435,120 | 14.47 s |
| DEV-3 | `d_1717` | `d_1718–1745` | 458,640 | 14.92 s |
| DEV-4 | `d_1801` | `d_1802–1829` | 482,160 | 15.21 s |
| Validation | `d_1885` | `d_1886–1913` | 505,680 | 15.74 s |

Every output has 1,960 deterministically ordered rows and exact identity/date alignment. Expected sales never use actuals in their score block.

## Residual scale evolution

For each series, `residual = actual − expected`. At block start, the score is:

`(residual − median(prior OOS residuals)) / (1.4826 × MAD(prior OOS residuals))`.

DEV-1 uses only 28 scale-seed residuals per series; DEV-2 uses seed + DEV-1; the archive expands only after complete-block scoring. Validation uses seed plus all four development blocks. All 9,800 development/validation scores were defined; undefined rate was 0%. No epsilon or within-block update was used.

## Development score and forecast-residual diagnostics

| Block | Score median | IQR | p1 | p5 | p95 | p99 | Max | MAE | Mean residual | Median residual |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| DEV-1 | 0.015 | 1.543 | -2.828 | -1.847 | 2.159 | 3.552 | 6.589 | 48.81 | 3.19 | -0.41 |
| DEV-2 | -0.202 | 1.365 | -2.767 | -1.909 | 1.822 | 2.798 | 8.160 | 50.51 | -8.70 | -7.56 |
| DEV-3 | -0.096 | 1.727 | -3.233 | -2.025 | 2.857 | 5.793 | 10.749 | 58.45 | -18.04 | -5.05 |
| DEV-4 | 0.275 | 1.726 | -2.405 | -1.612 | 2.639 | 4.070 | 6.159 | 70.41 | 38.72 | 7.85 |

The shifts are forecast-residual context, not renewed forecasting model selection.

## Development threshold comparison

| Block | `|score|≥3` alerts/rate | Spike/drop | `|score|≥4` alerts/rate | Spike/drop |
|---|---:|---:|---:|---:|
| DEV-1 | 46 / 2.35% | 32 / 14 | 15 / 0.77% | 13 / 2 |
| DEV-2 | 33 / 1.68% | 18 / 15 | 9 / 0.46% | 9 / 0 |
| DEV-3 | 119 / 6.07% | 95 / 24 | 62 / 3.16% | 54 / 8 |
| DEV-4 | 72 / 3.67% | 69 / 3 | 23 / 1.17% | 23 / 0 |
| **Total** | **270 / 3.44%** | **214 / 56** | **109 / 1.39%** | **99 / 10** |

Threshold 3 reached 57 series; its top five series contributed 33.70% of alerts. Threshold 4 reached 28 series and concentrated 53.21% in its top five. Threshold 3 had 24 zero-alert dates across 112 dates and at most 12 alerts on one date; threshold 4 had 58 zero-alert dates and at most 7 alerts.

Capacity policies produced exactly 140 top-5 records per block (560 total, 7.14%) and 280 top-10 records per block (1,120 total, 14.29%). Top 5 reached 41–48 series per block; top 10 reached 54–64. These are review queues, not assertions of true anomaly status.

## Consecutive alerts

At threshold 3, 127 alert rows participated in 48 consecutive series runs; the longest was 10 days during DEV-3. Threshold 4 had 58 participating rows in 23 runs, with a six-day maximum. Daily observations remain separate.

## Engineered development tests

Injections changed actual sales only, used 2×/4× each series' prior robust sales variation, preserved expected sales and residual scales, and floored drops at zero. Ten deterministic series per block produced 480 injected rows per magnitude.

| Magnitude | Selected-threshold detection | Direction correct | Mean |score| before → after |
|---|---:|---:|---:|
| 2× | 61.25% | 97.71% | 1.117 → 3.820 |
| 4× | 94.79% | 99.58% | 1.117 → 7.221 |

Across individual families, 2× detection ranged from 52.50% to 67.50%. At 4× it ranged from 92.50% to 97.50%. Family windows are non-overlapping and evaluated on independent copies. These are engineered sensitivity rates, not real-world recall.

## DEVELOPMENT-SELECTED decisions

The statistical threshold was frozen at **`|score| ≥ 3`** before validation scoring. It maintained an interpretable robust boundary, materially improved 2× and 4× engineered sensitivity, covered more series, and was less concentrated than threshold 4 while producing a manageable 3.44% development alert rate.

Operational review capacity was separately frozen at **top 5 defined absolute scores per day**. It surfaces a consistent, manageable queue and halves top-10 workload. A top-5 review candidate need not cross the statistical threshold.

The decision and exact blockwise scale policy were serialized to `development_policy_freeze.json`; validation scoring refused to run without that freeze.

## Validation evidence

Validation contained 1,960 defined scores: median -0.094, IQR 1.349, p1 -2.376, p5 -1.698, p95 1.856, p99 2.935, and maximum absolute score 5.810. Forecast residual MAE was 55.89 units, mean residual -7.35, and median residual -5.47.

The frozen threshold flagged 25 rows (1.28%): 19 spikes and 6 drops across 16 series. The top five series contributed 52%; the largest series count was 5. There were 11 zero-alert days and a maximum of 4 alerts on one date. Eight rows formed four two-day consecutive runs. Threshold 4, retained only for context, flagged 8 rows (0.41%), 5 spikes and 3 drops across 7 series.

Top-5/day produced 140 validation review candidates across 52 series; top-10/day produced 280 across 63. Neither changed the frozen policy.

## Validation engineered confirmation

The exact frozen injection protocol yielded 74.17% detection and 100% direction correctness at 2×, with mean absolute score moving from 0.834 to 4.974. At 4×, detection was 97.50% and direction correctness was 100%, with mean absolute score 8.972. No parameter changed afterward.

## Authentic alert examples

| Scope/date | Series | Actual | Expected | Residual | Score | Direction | Context |
|---|---|---:|---:|---:|---:|---|---|
| DEV 2015-10-30 | WI_2/HOBBIES_2 | 104 | 31.01 | 72.99 | 10.749 | spike | no event; SNAP 0 |
| DEV 2015-10-22 | TX_3/HOBBIES_2 | 158 | 48.88 | 109.12 | 10.037 | spike | no event; SNAP 0 |
| DEV 2015-10-31 | WI_2/HOBBIES_2 | 96 | 33.91 | 62.09 | 9.298 | spike | Halloween/Cultural; SNAP 0 |
| Validation 2016-04-03 | CA_2/HOUSEHOLD_1 | 1,414 | 1,053.37 | 360.63 | 5.810 | spike | no event; SNAP 1 |
| Validation 2016-04-09 | WI_2/FOODS_2 | 2,063 | 1,414.19 | 648.81 | 5.293 | spike | no event; SNAP 1 |
| Validation 2016-04-22 | TX_1/HOUSEHOLD_2 | 133 | 221.12 | -88.12 | -4.201 | drop | no event; SNAP 0 |

These statements describe deviations only. They do not attribute causes.

## Event and SNAP context

Among 270 development alerts, 24 fell on primary-event dates and 76 had the applicable state SNAP flag. No secondary-event alert occurred. Among 25 validation alerts, none fell on recorded event dates and 16 had SNAP active. These are descriptive overlaps, not causal effects.

## Limitations and next step

M5 has no authentic anomaly labels; alert counts cannot be called false positives, and synthetic detection cannot estimate real-world precision/recall. Scores inherit forecast limitations and are not probabilities. Fixed thresholds vary by period, while top-N queues force review candidates on quiet days. Residual archives contain sparse 28-day blocks rather than every historical day.

The interpretable baseline is established. One controlled Isolation Forest challenger is justified only to test whether multivariate residual/context structure improves stability or engineered sensitivity without unacceptable opacity. It must use the same development/validation protocol and cannot access the anomaly lockbox.
