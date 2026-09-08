# Leakage-Safe Baseline Results

> **NO LOCKBOX RESULTS:** This experiment reads only `sales_train_validation.csv` and evaluates `d_1466`–`d_1913`. It does not read or evaluate target values for `d_1914`–`d_1941`.

## Experiment setup

Daily item sales were summed into the frozen department × store grain using `d_1`–`d_1913`. The resulting matrix has exactly 70 series (7 departments × 10 stores). Every baseline produces 28 daily forecasts at each of the six frozen expanding-window origins. No learned model, tuned parameter, price value, calendar feature, or engineered forecasting feature is involved.

The reproducible analysis is in [`notebooks/01_forecasting_baselines.ipynb`](../../notebooks/01_forecasting_baselines.ipynb). Reusable metric implementations are in [`src/marketmind/forecasting/metrics.py`](../../src/marketmind/forecasting/metrics.py).

## Temporal validation

| Fold | Training | Validation | Validation days |
|---:|---|---|---:|
| 1 | `d_1`–`d_1465` | `d_1466`–`d_1493` | 28 |
| 2 | `d_1`–`d_1549` | `d_1550`–`d_1577` | 28 |
| 3 | `d_1`–`d_1633` | `d_1634`–`d_1661` | 28 |
| 4 | `d_1`–`d_1717` | `d_1718`–`d_1745` | 28 |
| 5 | `d_1`–`d_1801` | `d_1802`–`d_1829` | 28 |
| 6 | `d_1`–`d_1885` | `d_1886`–`d_1913` | 28 |

## Baseline definitions

- **Last value:** repeat the final observed training value for all 28 steps.
- **Seasonal naïve (7):** repeat the final seven observed training values four times. Validation actuals are never recursively consumed.
- **Historical mean (28):** repeat the mean of the final 28 observed training values for all steps.

The optional seven-day mean was not added: the three frozen baselines already provide distinct level, weekly-pattern, and recent-level references without expanding the comparison set.

## Metric definitions

- **RMSSE:** root mean squared validation error divided by the mean squared one-step change calculated only from that series and fold's training slice. The primary statistic is the unweighted mean over series and folds.
- **MAE:** mean absolute error in daily units.
- **WAPE:** summed absolute error divided by summed actual demand. Pooled WAPE is reported because macro per-series ratios can be unstable at low volume.
- **Forecast bias:** `sum(forecast - actual) / sum(actual)`. Positive means overforecasting; negative means underforecasting.

Non-positive WAPE/bias denominators and non-positive or invalid RMSSE scales return undefined (`NaN`), never zero.

## Leakage protections

- Only the validation training file, ending at `d_1913`, is loaded.
- Each baseline is constructed exclusively from observations through its fold cutoff.
- Seasonal naïve tiles a frozen seven-value training template.
- Each RMSSE scale is recomputed from the current fold's training slice.
- The nine item-store demonstrations are selected from development-period descriptive statistics before their forecast performance is evaluated.
- No random split, full-development preprocessing, validation-derived statistic, future price, or lockbox outcome is used.

## Core 70-series results

Metrics below cover 420 series-fold observations per baseline.

| Baseline | Macro RMSSE | Median RMSSE | RMSSE Q25 | RMSSE Q75 | Macro MAE | Pooled WAPE | Pooled bias |
|---|---:|---:|---:|---:|---:|---:|---:|
| Historical mean (28) | **1.06690** | 0.98535 | 0.83592 | 1.19618 | 99.42 | 17.83% | -1.81% |
| Seasonal naïve (7) | 1.06967 | **0.96583** | **0.76451** | 1.26216 | **91.48** | **16.41%** | **-1.10%** |
| Last value | 1.53223 | 1.38292 | 1.04778 | 1.80705 | 162.15 | 29.09% | +16.15% |

Under the frozen primary metric, historical mean is the benchmark. Its macro RMSSE advantage over seasonal naïve is only 0.00277 (about 0.26%), so it is not broadly dominant. Seasonal naïve is stronger on macro MAE, pooled WAPE, pooled bias magnitude, median RMSSE, and lower-quartile RMSSE. Last value is clearly weaker and substantially overforecasts overall.

## Fold stability

| Fold | Historical mean RMSSE | Seasonal naïve RMSSE | Last-value RMSSE | Primary-metric winner |
|---:|---:|---:|---:|---|
| 1 | **1.13487** | 1.21504 | 1.80515 | Historical mean |
| 2 | **0.91486** | 0.92854 | 1.32980 | Historical mean |
| 3 | 0.94506 | **0.86270** | 1.32819 | Seasonal naïve |
| 4 | 1.17895 | **1.12144** | 1.69331 | Seasonal naïve |
| 5 | 1.16838 | **1.16165** | 1.42925 | Seasonal naïve |
| 6 | **1.05930** | 1.12866 | 1.60767 | Historical mean |

Fold leadership splits evenly: historical mean wins Folds 1, 2, and 6; seasonal naïve wins Folds 3, 4, and 5. Fold 4 is hardest for historical mean, while Fold 1 is hardest for seasonal and last-value naïve. The relative ordering of the two credible baselines is therefore not stable. Last value ranks last in every fold.

## Series-level findings

Using six-fold mean RMSSE for the primary benchmark:

- Best historical-mean series include `TX_2/HOBBIES_1` (0.7580), `TX_2/FOODS_2` (0.7727), `TX_1/FOODS_3` (0.7786), and `TX_2/FOODS_3` (0.7841).
- The hardest include `CA_2/FOODS_2` (2.2090), `WI_2/FOODS_2` (1.6370), `WI_1/FOODS_2` (1.4873), and `WI_2/HOUSEHOLD_1` (1.4454). None were removed.
- Seasonal naïve most strongly improves on last value for `CA_2/FOODS_2` (RMSSE reduction 2.4150), `CA_2/HOUSEHOLD_1` (1.4637), `CA_2/FOODS_3` (1.4098), and `CA_1/HOUSEHOLD_1` (1.4068).
- Historical mean beats both alternatives for 38 of 70 series. Its largest advantage over the better alternative appears for `WI_2/FOODS_2` (0.6272), `TX_1/HOBBIES_2` (0.4540), and `CA_1/HOBBIES_2` (0.4076).

Historical-mean average RMSSE by department is lowest for `HOBBIES_1` (0.8554) and highest for `FOODS_2` (1.2271) and `HOUSEHOLD_1` (1.2227). By store it is lowest for `TX_2` (0.8786) and highest for `CA_2` (1.2431) and `WI_2` (1.2108). State means are TX 0.9784, CA 1.0964, and WI 1.1160. These are descriptive error patterns, not causal conclusions.

## Intermittent-demand demonstration

The updated deterministic median-proximity rule selected these series before forecast evaluation:

| Regime | Eligible-regime median zero share | Selected ID | Zero share | History span | Total units |
|---|---:|---|---:|---:|---:|
| Dense | 16.60% | `FOODS_3_116_CA_3_validation` | 16.57% | 1,913 | 12,466 |
| Dense | 16.60% | `FOODS_3_295_WI_1_validation` | 16.57% | 1,913 | 18,231 |
| Dense | 16.60% | `FOODS_3_394_CA_3_validation` | 16.57% | 1,912 | 4,745 |
| Moderate | 56.93% | `FOODS_1_118_WI_1_validation` | 56.93% | 1,377 | 1,784 |
| Moderate | 56.93% | `FOODS_1_127_TX_3_validation` | 56.93% | 1,913 | 1,596 |
| Moderate | 56.93% | `FOODS_1_185_WI_3_validation` | 56.93% | 1,904 | 1,600 |
| High | 85.21% | `FOODS_1_125_TX_3_validation` | 85.21% | 899 | 468 |
| High | 85.21% | `FOODS_1_189_TX_2_validation` | 85.21% | 1,514 | 378 |
| High | 85.21% | `FOODS_2_111_TX_3_validation` | 85.21% | 1,200 | 446 |

Descriptive nine-series results:

| Regime | Baseline | Macro RMSSE | Macro MAE | Pooled WAPE | Pooled bias |
|---|---|---:|---:|---:|---:|
| Dense | Historical mean | **0.7544** | **3.8071** | **75.04%** | +6.77% |
| Dense | Last value | 0.8930 | 3.9464 | 77.79% | -27.73% |
| Dense | Seasonal naïve | 0.9500 | 4.2679 | 84.12% | -5.05% |
| Moderate | Historical mean | **0.7133** | **0.9515** | **100.12%** | +5.64% |
| Moderate | Last value | 0.9267 | 1.2004 | 126.31% | -6.47% |
| Moderate | Seasonal naïve | 0.9543 | 1.1647 | 122.55% | +5.22% |
| High | Historical mean | **0.8578** | 0.5340 | 144.70% | +17.74% |
| High | Last value | 0.9664 | **0.5238** | **141.94%** | -24.73% |
| High | Seasonal naïve | 1.0784 | 0.5516 | 149.46% | +26.88% |

The tiny item sample is illustrative, not inferential. Unit MAE falls with volume, but WAPE rises above 100% in moderate/high regimes because actual totals are small and zeros are frequent. The simple weekly pattern is not automatically helpful at item level. Historical mean leads item-demo RMSSE in all three regimes, while last value has slightly lower unit MAE/WAPE in the highly intermittent group. These outcomes do not influence core benchmark selection.

## Metric edge cases

- Core evaluation: 0 of 1,260 baseline/series/fold rows had invalid RMSSE; no core series-fold had zero actual total.
- Item demonstration: no invalid RMSSE scale occurred. Two of 54 item-series/fold validation windows had zero actual total, making WAPE and relative bias undefined for all three baselines on those windows. They remain `NaN`; they were not converted to zero. Pooled regime metrics remain defined because each regime has positive aggregate actual demand.
- The metric tests explicitly cover perfect, over-, under-, zero-total, zero-scale, shape-mismatch, and normal nonzero cases.

## Baseline benchmark

The frozen primary-metric benchmark for future learned models is **28-day historical mean, macro RMSSE 1.06690** across the six development folds. Future comparisons must retain all three baselines because seasonal naïve is statistically adjacent on RMSSE and better on several secondary metrics. Claims of learned-model improvement should address fold stability and per-series behavior, not only a pooled score.

## Known limitations and remaining questions

- Six spaced origins characterize recent development history but do not cover every retail condition.
- Aggregate sales still reflect observed sales, not unconstrained demand or inventory availability.
- RMSSE emphasizes large errors; WAPE emphasizes high-volume series; both views must remain visible.
- Nine intermittent series cannot establish general bottom-level performance.
- Before learned models: choose the algorithm family, direct/recursive/multi-output strategy, leakage-safe feature set and categorical encoding, price-unavailability policy, and constrained tuning budget—all using development folds only.
- Prediction intervals, hierarchy reconciliation/WRMSSE, anomaly thresholds, and inventory logic remain out of scope.
