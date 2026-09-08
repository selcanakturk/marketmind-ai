# Demand Forecasting Methodology

## Status and scope

This document is the source of truth for MarketMind AI demand-forecasting experiments. It freezes the problem, evaluation boundary, and comparison policy before model development. It does not authorize lockbox evaluation, feature production, model training, anomaly detection, or inventory logic.

## Frozen decisions

### Business problem and target

At a forecast origin at the end of day \(T\), MarketMind will estimate daily unit sales for every store-department combination for days \(T+1\) through \(T+28\):

\[
\hat y_{s,d,T+h}, \qquad h=1,\ldots,28
\]

where \(s\) is a store, \(d\) is a department, and the target \(y\) is the sum of M5 item-level units sold for that store, department, and day. The business question is: **How many units are expected to be sold for each store-department combination on each of the next 28 days?** Seven-day and 28-day sums may later be presented as business summaries of the same daily forecast.

The output is intended to support planning, later forecast-residual monitoring, and inventory scenarios that receive real operational inputs. It is a **sales forecast**, or cautiously an **observed-demand forecast**. Sales are not unconstrained demand: M5 has no inventory availability, stockout flag, or lost-sales measure. The forecast therefore does not estimate latent demand, inventory state, causal event or price effects, or guaranteed business outcomes.

### Primary grain

The primary grain is **department × store × day**. Authentic M5 data contains 7 departments, 10 stores, and all 70 department-store combinations, producing 70 daily series.

This choice is methodological rather than performance-driven:

- All 30,490 item-store series preserve maximum detail, but Phase 0 found a median zero share of 73.31%; 47.24% are at least 75% zero. They would make independent training, evaluation, deployment, and dashboard use unnecessarily heavy for the core system.
- Category-store has only 30 series and store-total only 10. Both are dense and inexpensive, but remove department-level operational detail.
- The 70 department-store series are operationally legible and computationally light while retaining useful within-store structure. They are dense: Phase 0 measured a 0.27% overall zero-day rate, a median of 1,936 active days over the full 1,941-day history, and all 70 below 25% zeros.

No empirical model result may be used to revisit this grain unless a genuine methodological flaw is found and documented.

### Secondary intermittent-demand demonstration

A secondary, explicitly non-core demonstration may later use **nine item-store series: three from each of three regimes**. Selection must occur before modeling and use only `sales_train_validation.csv` (`d_1`–`d_1913`). For each item-store series define:

- active day: daily units greater than zero;
- active-day ratio: active days divided by 1,913;
- zero share: one minus the active-day ratio;
- history length: inclusive days from first through last positive-sale day;
- total sales: units summed over `d_1`–`d_1913`.

First require history length of at least 730 days and total sales of at least 100 units. Then assign mutually exclusive regimes:

| Regime | Pre-model rule |
|---|---|
| Dense | zero share < 25% (active-day ratio > 75%) |
| Moderately intermittent | 25% ≤ zero share < 75% (25% < active-day ratio ≤ 75%) |
| Highly intermittent | zero share ≥ 75% (active-day ratio ≤ 25%) |

Within each regime, calculate the median zero share among eligible series, rank series by absolute distance from that regime median, break ties by ascending stable `id`, and take the first three. This replaces the earlier first-three-lexicographic-ID rule before baseline performance was evaluated: proximity to the regime median is more representative while remaining deterministic and model-independent. These thresholds follow the descriptive bands established in Phase 0; minimum history and volume avoid demonstrations dominated by extremely short assortment exposure or trivial totals. On the authentic development data, the eligible counts are 1,560 dense, 14,310 moderately intermittent, and 10,959 highly intermittent, so the rule is feasible. It is deliberately indifferent to validation or lockbox accuracy. The selected nine must be recorded before their forecasts are evaluated and must never replace the 70-series core evaluation.

### Forecast horizon and output

The forecast horizon is **28 daily steps**. This is the native M5 horizon, a meaningful retail planning window, usable later for anomaly monitoring and inventory scenarios, and manageable for repeated backtests. A dashboard may aggregate the daily values into 7-day and 28-day summaries. There will not initially be separate 7-day or 30-day models, and 28-day forecasts will not be called 30-day forecasts.

### Development history and final lockbox

- **Development:** `d_1`–`d_1913`, 2011-01-29 through 2016-04-24.
- **Untouched final lockbox:** `d_1914`–`d_1941`, 2016-04-25 through 2016-05-22.

The lockbox may be evaluated exactly once only after the feature pipeline, model family and configuration, baseline comparison, metric implementation, and any decision thresholds are frozen. It must not influence feature, model, hyperparameter, threshold, baseline, series, or grain selection. Calendar rows after `d_1941` are scheduled context, not observed future sales; `d_1942`–`d_1969` sales labels are absent from the inspected matrices.

### Expanding-window backtesting

All model selection will use the following six expanding-window folds within `d_1`–`d_1913`. Each validation block has 28 days. Origins are 84 days apart, so the folds sample roughly quarterly conditions across the most recent 448-day span while avoiding the cost and dependence of every possible origin. The first fit still has 1,465 days (just over four years) of history.

| Fold | Training period | Training end date | Validation period | Validation dates | Training-history length |
|---:|---|---|---|---|---:|
| 1 | `d_1`–`d_1465` | 2015-02-01 | `d_1466`–`d_1493` | 2015-02-02–2015-03-01 | 1,465 days |
| 2 | `d_1`–`d_1549` | 2015-04-26 | `d_1550`–`d_1577` | 2015-04-27–2015-05-24 | 1,549 days |
| 3 | `d_1`–`d_1633` | 2015-07-19 | `d_1634`–`d_1661` | 2015-07-20–2015-08-16 | 1,633 days |
| 4 | `d_1`–`d_1717` | 2015-10-11 | `d_1718`–`d_1745` | 2015-10-12–2015-11-08 | 1,717 days |
| 5 | `d_1`–`d_1801` | 2016-01-03 | `d_1802`–`d_1829` | 2016-01-04–2016-01-31 | 1,801 days |
| 6 | `d_1`–`d_1885` | 2016-03-27 | `d_1886`–`d_1913` | 2016-03-28–2016-04-24 | 1,885 days |

For every fold, preprocessing and target-derived statistics must be fitted or computed using only that fold's training period. The folds are frozen for model comparison unless a documented methodological defect is discovered.

### Metric policy

For series \(i\), forecast errors are \(e_{i,h}=y_{i,T+h}-\hat y_{i,T+h}\). Let \(n_i\) be its training length and \(H=28\).

**Primary metric — RMSSE**

\[
\operatorname{RMSSE}_i=
\sqrt{\frac{H^{-1}\sum_{h=1}^{H}e_{i,h}^2}
{(n_i-1)^{-1}\sum_{t=2}^{n_i}(y_{i,t}-y_{i,t-1})^2}}
\]

RMSSE normalizes squared forecast error by the in-sample one-step naïve-change scale computed separately from **only that fold's training observations**. A full-development denominator must never be reused for earlier folds. It is related to M5 evaluation, compares heterogeneous department-store scales, and penalizes large misses. It is appropriate for the dense primary grain. A zero, non-finite, or otherwise invalid denominator makes a series-fold undefined (`NaN`) and must be counted and reported rather than replaced with zero.

The primary comparison statistic is the unweighted mean of per-series RMSSE across all 70 series and then the unweighted mean across the six folds. Fold distributions and per-series results must accompany it so weak series are visible.

**Secondary metrics**

- \(\operatorname{MAE}=H^{-1}\sum_h|e_h|\): typical absolute error in units. Report per series, macro averages, and pooled/global MAE. It is interpretable but scale-dependent.
- \(\operatorname{WAPE}=\sum|e|/\sum y\): total absolute error relative to total actual units. Report each series-fold when its actual sum is positive, plus pooled fold/global values. It is operationally intuitive but high-volume series dominate pooled WAPE and a zero actual denominator is undefined.
- **Forecast bias:** use the signed convention \(\sum(\hat y-y)/\sum y\), alongside mean signed error in units. Positive means overforecasting and negative means underforecasting. Report per series, macro where defined, and pooled values; opposing errors can cancel.

MAPE is not primary because zero actuals make it undefined and near-zero actuals make it unstable. WRMSSE is not adopted merely because this is M5. It remains optional only if a genuine hierarchical evaluation with correctly reconstructed, decision-relevant weights is later implemented.

### Baseline plan for the next step

The next experimental step must implement these baselines before any ML model:

1. **Last-value naïve:** forecast the latest observed value at the cutoff for all 28 steps.
2. **Seasonal naïve (7 days):** repeat the final seven observed training values (`T-6` through `T`) four times. It must not use `y_(T+h-7)` when that value is an actual from inside validation.
3. **Recent-mean:** forecast the arithmetic mean of the final 28 observed days at the cutoff for all 28 steps.

Each baseline must follow the same folds, grain, horizon, and metrics. A learned model must show repeatable value relative to these simple references; complexity alone is not evidence of improvement.

**Step 2 status update:** The three baselines were evaluated on the six development folds without reading lockbox targets. The 28-day historical mean is the primary-metric benchmark with macro RMSSE 1.06690, narrowly ahead of seasonal naïve at 1.06967; seasonal naïve is better on MAE and pooled WAPE. Fold RMSSE leadership splits 3–3, so future models must retain all three comparisons and demonstrate stability rather than beat only one aggregate number. Full results are recorded in `reports/forecasting/baseline_results.md`.

### Covariate availability policy

Covariates are classified by what is genuinely available at forecast issuance:

- **Known in advance:** forecast date, weekday, month, year, documented calendar event names/types, applicable state SNAP schedules, and Walmart week identifier, provided the corresponding schedule is actually available at issuance.
- **Historical only:** lagged sales, rolling or expanding sales statistics, historical residuals, and every other target-derived value. These stop at the forecast cutoff and are recomputed fold by fold.
- **Price:** historical prices may be used only where temporally available. Horizon prices may be used only when explicitly supplied as known planned prices or labeled scenario inputs. Future realized prices must never be silently treated as known. How to handle unavailable future price is an open experiment, not an invitation to leak it.

Calendar availability does not make target-derived features future-known, and publication of a calendar row does not establish publication of a sales label.

### Leakage checklist

Before accepting any experiment, verify that:

- no future target value enters training, features, preprocessing, selection, or scaling;
- rolling windows are trailing, never centered, and are shifted appropriately at issuance;
- realized horizon prices are excluded unless genuinely planned or explicitly scenario-labeled;
- aggregate statistics and encodings are fitted only on data available at each cutoff;
- temporal folds are chronological; random train/test splitting is not used;
- preprocessing is fitted separately within each training fold, never on validation or lockbox data;
- series selection uses the frozen descriptive rule, not final evaluation performance;
- `d_1914`–`d_1941` is not read by experimental or selection code before final evaluation;
- the lockbox is not repeatedly inspected or used to revise decisions;
- known-ahead calendar fields are kept distinct from target-derived historical features;
- metric scaling denominators use only the relevant fold's training history;
- multi-step recursive inputs, if later used, cannot substitute future actual sales for prior predictions.

### Downstream boundaries

Future anomaly work may follow: expected sales forecast → observed actual sales → residual/deviation → scale and context normalization → anomaly signal. A forecast error alone is not automatically a business anomaly, and an anomaly score is not a probability of anomaly.

Future inventory decision support may combine forecasts with explicit inputs such as `current_stock`, `supplier_lead_time`, `incoming_quantity`, and safety-stock or service assumptions. M5 contains none of those operational states; they will not be inferred or fabricated.

## Open / future experimental decisions

### Modeling architecture

| Strategy | Strengths | Limitations |
|---|---|---|
| One model per series | Direct and locally interpretable | Fragments data; 70 artifacts/configurations increase training and maintenance cost |
| One global model | Shares information across all series; one deployable pipeline; entity categories can express store/department differences | Requires careful entity encoding and error analysis; may underfit unusual series |
| Grouped models | Compromise by department, category, state, or demand behavior | Group definition and multiple artifacts add selection and maintenance decisions |
| Simple statistical baselines | Transparent, fast, and essential reference points | Limited ability to combine rich context or learn cross-series patterns |

After the mandatory baselines, the first learned architecture to test should be a **single lightweight global model across the 70 series**, with store and department identity represented categorically and identical temporal validation for every series. It offers cross-series learning, data efficiency, and a compact production artifact. The algorithm, target transformation, multi-step strategy, categorical encoding, feature set, and tuning procedure remain open and must be chosen only within development folds. Per-series or grouped approaches remain valid challengers.

### Uncertainty

Point forecasts come first. Prediction intervals or other uncertainty estimates may be added only with statistically defensible construction and empirical coverage evaluation. They must not be mislabeled as confidence, certainty, or event probability.

### Other open decisions

- Exact learned model family and hyperparameter search budget.
- Direct, recursive, or multi-output 28-step strategy.
- Final leakage-safe lag, rolling, event, SNAP, and price feature definitions.
- Missing/unavailable future-price treatment and whether price scenarios are exposed.
- Whether grouped or per-series challengers justify their additional complexity.
- Whether defensible interval methodology achieves useful empirical coverage.
- Whether true hierarchical reconciliation and WRMSSE are worth implementing.
- Later anomaly normalization and review thresholds.
- Later inventory-policy assumptions and user-input contract.

## Empirical validation record

The frozen structural choices were rechecked programmatically against the authentic files in `data/raw/m5/`, not inferred only from Phase 0 prose:

- `sales_train_validation.csv`: 30,490 rows and exactly 1,913 target columns, `d_1`–`d_1913`.
- `sales_train_evaluation.csv`: target columns `d_1`–`d_1941`, confirming the 28 observed lockbox labels exist.
- Seven distinct `dept_id` values, ten distinct `store_id` values, and 70 observed department-store pairs, equal to the complete 7 × 10 Cartesian count.
- `calendar.csv`: `d_1` = 2011-01-29, `d_1913` = 2016-04-24, `d_1914` = 2016-04-25, `d_1941` = 2016-05-22, and calendar-only continuation through `d_1969` = 2016-06-19.
- Every frozen backtest validation boundary exists in the development timeline; Fold 6 ends exactly at `d_1913`, before the lockbox.

No conflict was found. This validation inspected structure and descriptive eligibility only; it did not evaluate a forecast or the lockbox.
