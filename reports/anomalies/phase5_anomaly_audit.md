# Phase 5 Step 1 anomaly feasibility audit

## Scope and lockbox guard

This is a structural/descriptive audit, not anomaly detection. Sales distributions below use only `d_1–d_1913`. For the frozen anomaly lockbox `d_1914–d_1941`, only schema/date availability and the count `70 × 28 = 1,960` were checked. No lockbox sales values, residuals, anomaly scores, alerts, rankings, or performance were inspected.

## Authentic inputs

| File | Exact shape | Schema | Missingness |
|---|---:|---|---|
| `sales_train_evaluation.csv` | 30,490 × 1,947 | `id,item_id,dept_id,cat_id,store_id,state_id,d_1…d_1941` | 0 cells |
| `calendar.csv` | 1,969 × 14 | `date,wm_yr_wk,weekday,wday,month,year,d,event_name_1,event_type_1,event_name_2,event_type_2,snap_CA,snap_TX,snap_WI` | base/date/SNAP fields complete; event-1 name/type 1,807 missing each and event-2 name/type 1,964 missing each, representing non-event days |
| `sell_prices.csv` | 6,841,121 × 4 | `store_id,item_id,wm_yr_wk,sell_price` | 0 cells; weeks 11101–11621 |

Observed sales run from `d_1` (2011-01-29) through `d_1941` (2016-05-22). The calendar continues to `d_1969` (2016-06-19), but those later calendar rows are not observed sales. The hierarchy contains 3 states, 10 stores, 3 categories, 7 departments, 3,049 items, and 30,490 item-store rows. All 70 department-store combinations exist.

## Department-store density

Aggregation across `d_1–d_1913` produced exactly 133,910 observations (`70 × 1,913`), with no duplicate series-day keys, missing grid rows, negative sales, or missing sales values.

| Daily sales across all 70 series | Value |
|---|---:|
| Minimum / 1st percentile | 0 / 6 |
| 25th percentile / median / 75th percentile | 135 / 286 / 549 |
| Mean / standard deviation | 490.594 / 602.598 |
| 95th / 99th percentile | 1,836 / 2,876 |
| Maximum | 5,118 |
| IQR | 414 |
| Zero-sales share | 0.2711% |

Every series has 1,913 observations. The following summarizes the 70 per-series descriptive profiles rather than pooling unlike scales:

| Per-series statistic | Minimum | Median across series | Maximum |
|---|---:|---:|---:|
| Median daily sales | 10 | 287 | 2,871 |
| Daily-sales IQR | 10 | 119.5 | 895 |
| Zero-sales share | 0.0000% | 0.2614% | 1.0978% |
| Coefficient of variation | 0.2081 | 0.3151 | 0.7887 |
| 95th percentile sales | 26 | 448.4 | 4,080.8 |
| 99th percentile sales | 40 | 535.92 | 4,481.68 |
| Maximum sales | 76 | 767 | 5,118 |

The largest raw values are plausible high-volume department totals, not labeled anomalies. Scale varies greatly—median series sales span 10 to 2,871 and maximums span 76 to 5,118—so a common raw-unit threshold would be indefensible. The grain is exceptionally dense and operationally interpretable; there is no empirical reason to move to intermittent item-store monitoring.

## Residual-scale feasibility

Raw residuals preserve unit direction but are incomparable across series. Raw percentage errors are unstable for the lower-volume departments. Per-series historical standard deviations and CVs show heterogeneity, while low zero rates support robust residual scaling. The primary candidate is therefore a signed residual standardized by each series' expanding archive of earlier out-of-sample residuals using median and `1.4826 × MAD`. Scale must be recomputed point-in-time. Zero-MAD cases remain undefined and counted. RMSSE-like naïve-change scaling and absolute residuals remain diagnostics.

## Calendar and price context

Within development, event-1 is populated on 154 days, covering 30 names: 52 Religious, 51 National, 35 Cultural, and 16 Sporting observations. Four days have a second event. Each state has 630 SNAP days. These known-ahead fields can legitimately shape the frozen forecasting expectation and can be shown descriptively beside alerts; they do not provide causal explanations.

Prices are complete in the price table but weekly, assortment-dependent, and excluded from the established production forecast because future price availability was not guaranteed. Nothing in this audit demonstrates that price is necessary for the first anomaly detector. Keeping it out preserves a clean expectation contract; observed-price diagnostics remain future work.

## Temporal-block feasibility

Five 28-day development blocks provide 9,800 series-days. The first 1,960 seed the earlier-only residual archive; the next 7,840 support baseline and policy development. A separate 28-day anomaly validation block provides 1,960 observations. The untouched anomaly lockbox is `d_1914–d_1941`, also structurally 1,960 rows. Every block has at least 1,465 prior days for point-in-time expectation fitting, and blocks do not overlap.

## Synthetic and alert-volume feasibility

Dense nonnegative sales support controlled one-day and two-to-three-day spike/drop injections scaled to each series' prior robust variation. Drops can be floored at zero without impossible sales. These are engineered sensitivity tests, never authentic labels.

With 70 series per day, top-5 and top-10 policies imply fixed review volumes of 7.14% and 14.29% of daily observations. Fixed robust-score thresholds of 3 and 4 allow quiet days but variable volume. Step 2 should measure volume, temporal stability, direction balance, series/date concentration, consecutive records, and reviewability before selecting a policy.

## Feasibility conclusion

**FEASIBLE.** Department × store × day is dense, complete, compatible with forecasting, and large enough for chronological residual research. The next step can implement the interpretable robust residual baseline under the frozen partitions without training an anomaly detector in this step.
