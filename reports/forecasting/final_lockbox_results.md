# Final Forecasting Lockbox Results

> **THIS IS THE FIRST AND FINAL PLANNED EVALUATION ON `d_1914`–`d_1941`.**

> **`d_1914`–`d_1941` IS NOW CONSUMED.** These observations must never again be treated as model-selection validation data or used to revise features, preprocessing, parameters, sampling, strategy, baselines, or model family.

## Frozen candidate

The candidate was frozen in Step 5 before any lockbox target was evaluated:

- `sklearn.ensemble.HistGradientBoostingRegressor`;
- one global horizon-conditioned Full Direct model;
- department × store × day grain, all 70 series;
- raw unit-sales target and 28 daily horizons;
- Full historical, identity, horizon, and known target-date calendar feature scope;
- no prices;
- weekly training origins aligned backward from `training_end − 28`, minimum origin 56;
- fold-local-equivalent ordinal category encoding and zero clipping if needed.

Frozen parameters:

```text
loss="squared_error"
learning_rate=0.05
max_iter=160
max_leaf_nodes=63
max_depth=None
min_samples_leaf=100
l2_regularization=1.0
early_stopping=False
random_state=42
```

No element changed after the Step 5 freeze.

## Pre-lockbox development evidence

| Metric | Six-fold development result |
|---|---:|
| Macro RMSSE | 0.74604 |
| Macro MAE | 57.35 |
| Pooled WAPE | 10.29% |
| Pooled bias | -0.37% |

The operational HGBR candidate was selected despite ExtraTrees Direct's lower development RMSSE because the latter produced an approximately 1.05 GB artifact versus 1.28 MB for HGBR-4.

## Lockbox protocol

The notebook first loaded only `sales_train_validation.csv`, constructed training features and targets through `d_1913`, fitted preprocessing and the frozen model, and generated all 1,960 predictions. It asserted the 70 × 28 forecast shape and finite values before opening `sales_train_evaluation.csv` for the 28 lockbox columns.

Known calendar information for `d_1914`–`d_1941` was allowed under the frozen covariate policy. Lockbox sales, realized prices, and any target-derived lockbox statistic were absent from training, preprocessing, and forecast generation. RMSSE scales use only `d_1`–`d_1913`.

## Final training setup

| Item | Value |
|---|---:|
| Development observations | `d_1`–`d_1913` |
| Weekly training origins | 262 |
| Supervised rows | 513,520 |
| Approximate table + target memory | 159.48 MB |
| Build time | 4.17 s |
| Fit time | 5.82 s |
| Forecasts generated | 1,960 |

Timings are local measurements, not portable performance guarantees.

## Lockbox metrics

| Model | Macro RMSSE | Median RMSSE | Q25 | Q75 | Macro MAE | Pooled WAPE | Pooled bias |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Frozen HGBR-4 Direct** | **0.80073** | **0.71686** | 0.53949 | 0.96673 | **60.13** | **9.57%** | -4.76% |
| Seasonal naïve (7) | 1.02737 | 0.88501 | 0.69238 | 1.36668 | 83.01 | 13.21% | -7.36% |
| Historical mean (28) | 1.15338 | 1.08107 | 0.92518 | 1.29134 | 105.07 | 16.72% | -3.91% |
| Last value | 1.49252 | 1.33460 | 1.11907 | 1.72773 | 151.74 | 24.15% | +13.19% |

## Baseline comparison

The frozen model improves lockbox RMSSE by:

- **0.22665 absolute / 22.06% relative** versus seasonal naïve;
- **0.35265 / 30.58%** versus historical mean;
- **0.69179 / 46.35%** versus last value.

It also reduces pooled WAPE by 3.64, 7.15, and 14.58 percentage points, respectively. Baseline results are interpretation only and did not alter the model.

## Generalization gap

| Metric | Development | Lockbox | Gap |
|---|---:|---:|---:|
| Macro RMSSE | 0.74604 | 0.80073 | +0.05469 (+7.33%) |
| Macro MAE | 57.35 | 60.13 | +2.78 (+4.85%) |
| Pooled WAPE | 10.29% | 9.57% | -0.72 pp |
| Pooled bias | -0.37% | -4.76% | -4.39 pp |

The higher RMSSE and MAE constitute a moderate generalization gap, not automatic evidence of overfitting. Aggregate normalized absolute error improves, while underforecast bias becomes more pronounced.

## Series-level results

The frozen model beats historical mean for **65 of 70 series**, seasonal naïve for **62 of 70**, and last value for **61 of 70**. Gains are therefore broad rather than concentrated in a small subset.

Best series by RMSSE:

- `CA_1/HOUSEHOLD_1`: 0.3112
- `WI_1/FOODS_3`: 0.3395
- `CA_1/FOODS_2`: 0.3686
- `TX_2/HOUSEHOLD_2`: 0.3696
- `CA_3/FOODS_3`: 0.3830

Worst series:

- `WI_2/FOODS_1`: 1.8203
- `CA_3/HOBBIES_2`: 1.7766
- `WI_3/FOODS_1`: 1.7174
- `TX_3/FOODS_1`: 1.5267
- `TX_1/FOODS_1`: 1.4677

Previously highlighted difficult series score:

- `CA_4/HOBBIES_2`: 0.8969
- `CA_2/FOODS_2`: 1.2461
- `TX_1/HOBBIES_2`: 1.3518

They remain included and do not trigger model revision.

## Department, store, and state results

Department macro RMSSE:

| Department | RMSSE |
|---|---:|
| FOODS_3 | 0.4945 |
| HOUSEHOLD_1 | 0.6095 |
| HOBBIES_1 | 0.6588 |
| FOODS_2 | 0.6990 |
| HOUSEHOLD_2 | 0.7014 |
| HOBBIES_2 | 1.1394 |
| FOODS_1 | 1.3024 |

`FOODS_1` and `HOBBIES_2` are the clearest department-level weaknesses. By store, `CA_1` is strongest at 0.5363 and `WI_2` weakest at 1.0335. State averages are CA 0.7810, TX 0.8068, and WI 0.8209. These are descriptive findings, not causal conclusions.

## Horizon analysis

| Horizons | MAE | WAPE | Bias |
|---|---:|---:|---:|
| 1–7 | 50.55 | 8.55% | -2.34% |
| 8–14 | 57.89 | 9.11% | -3.45% |
| 15–21 | 66.70 | 10.00% | -6.58% |
| 22–28 | 65.37 | 10.55% | -6.45% |

Errors rise with horizon in broad blocks, though not monotonically day by day. Horizon 2 is easiest at MAE 39.81. Horizon 21 is hardest at 104.86, followed by horizon 28 at 88.97. Increasing underforecast bias after day 14 is the main horizon-level limitation; it is documented rather than tuned away.

## Prediction sanity checks

| Check | Result |
|---|---:|
| Total predictions | 1,960 |
| Raw minimum | 13.0377 |
| Raw maximum | 3,600.9411 |
| Negative raw predictions | 0 |
| Changed by clipping | 0 |
| Clipping rate | 0% |
| NaNs | 0 |
| Infinities | 0 |

No unexpected output required repair.

## Generalization assessment

**Strong overall generalization, with documented horizon and subgroup weaknesses.** The frozen model clearly beats every simple baseline, improves 62–65 of 70 series versus the two major baselines, retains a reasonable 7.33% RMSSE generalization gap, and has finite, plausible nonnegative output. The -4.76% aggregate bias and approximately -6.5% bias in horizons 15–28 temper the assessment but do not erase the broad improvement.

This assessment does not authorize retraining against lockbox findings. Any investigation of `FOODS_1`, `HOBBIES_2`, late-horizon underforecasting, or the untested ExtraTrees candidate requires genuinely new evaluation data or must be described only as future-work hypotheses.

## Known limitations

- The lockbox is one 28-day retail period and cannot characterize every deployment regime.
- Sales are observed sales rather than unconstrained latent demand.
- The model excludes price and inventory state by design.
- Some departments and series remain materially harder.
- Later horizons show stronger underforecast bias.
- ExtraTrees had better development RMSSE but was not evaluated on the lockbox under the frozen-candidate protocol.
- No uncertainty intervals are available.

## Lockbox consumption statement

**`d_1914`–`d_1941` IS NOW CONSUMED.** This was the first and final planned performance evaluation on those targets. The interval may be retained for immutable reporting and reproducibility, but it must never again be used for model selection, feature engineering, parameter tuning, threshold selection, or claims of fresh validation.
