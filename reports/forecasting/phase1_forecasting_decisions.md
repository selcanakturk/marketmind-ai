# Phase 1 Forecasting Decision Record

## Frozen

| Decision | Policy |
|---|---|
| Business target | At a cutoff, forecast daily observed unit sales for every store-department combination for the next 28 days. This is not unconstrained latent demand. |
| Primary grain | Department × store × day: 7 departments × 10 stores = 70 verified series. |
| Secondary scope | Nine pre-model item-store demonstrations: three each with zero share <25%, 25%–<75%, and ≥75%; require ≥730 active-history-span days and ≥100 total units; within each regime rank distance to its eligible-series median zero share, break ties by stable ID, and take three. This pre-performance clarification replaces the earlier lexicographic-first rule. |
| Horizon | 28 daily steps; later summaries may aggregate to 7 and 28 days. |
| Development | `d_1`–`d_1913` (2011-01-29–2016-04-24). |
| Final lockbox | `d_1914`–`d_1941` (2016-04-25–2016-05-22); no selection, tuning, or repeated evaluation. |
| Primary metric | Per-series RMSSE with its scale recomputed from that fold's training observations only, macro-averaged across 70 series and then six folds; invalid scales remain undefined and are reported. |
| Secondary metrics | MAE, WAPE, and signed forecast bias, with per-series, macro, and pooled summaries where defined. MAPE is not primary; WRMSSE requires a genuine future hierarchical evaluation. |
| Covariates | Calendar/scheduled context only if known at issuance; target-derived values are historical-only; future prices only as genuinely planned values or labeled scenarios. |
| Baselines | Last value, leakage-safe repeated final-seven-day seasonal naïve, and final-28-day mean. Step 2 evaluates them only on the six development folds; the lockbox remains untouched. |

## Baseline experiment status

Step 2 is complete on the development folds only. The primary benchmark is the **28-day historical mean (macro RMSSE 1.06690)**, narrowly ahead of seasonal naïve (1.06967); seasonal naïve has better macro MAE and pooled WAPE, and each wins three of six folds on RMSSE. Last value is weakest in every fold. All three remain required comparators for learned models. See [`baseline_results.md`](baseline_results.md); there are **no lockbox results**.

## Frozen expanding-window folds

| Fold | Training | Validation | Training days |
|---:|---|---|---:|
| 1 | `d_1`–`d_1465` | `d_1466`–`d_1493` | 1,465 |
| 2 | `d_1`–`d_1549` | `d_1550`–`d_1577` | 1,549 |
| 3 | `d_1`–`d_1633` | `d_1634`–`d_1661` | 1,633 |
| 4 | `d_1`–`d_1717` | `d_1718`–`d_1745` | 1,717 |
| 5 | `d_1`–`d_1801` | `d_1802`–`d_1829` | 1,801 |
| 6 | `d_1`–`d_1885` | `d_1886`–`d_1913` | 1,885 |

The authentic M5 headers and calendar were checked directly: all boundaries exist, all validation blocks contain 28 days, and none enters the lockbox.

## Recommended first learned architecture

After baselines, test one lightweight global model across all 70 series first. It can share statistical strength, retain store/department categorical identity, and remain a single maintainable deployment artifact.

## First learned experiment status

Step 3 tested the recommendation with one fixed, untuned, horizon-conditioned direct `HistGradientBoostingRegressor`. Actual features were origin-anchored lags 1/7/14/28/56; rolling mean and population standard deviation over 7/28/56 days; forecast horizon; store/department/state; and target-date weekday, day, month, year, trend, primary event name/type, and applicable SNAP indicator. Fold-local ordinal encoding was used; prices were excluded.

Across development folds, macro RMSSE was **0.77916**, a 0.28774 absolute and 26.97% relative improvement over historical mean. The model beat historical mean and seasonal naïve in all six folds, with six of 70 series regressing versus historical mean. The result satisfies the predeclared promising criterion but does **not** freeze the final model family or feature set. See [`first_global_model_results.md`](first_global_model_results.md). There are **no lockbox results**.

## Step 4 ablation and strategy status

Four fixed-parameter direct feature sets and one one-step recursive challenger were evaluated on the same folds. Removing rolling summaries worsened macro RMSSE by 0.05720 (7.34%); removing rich target-date calendar fields worsened it by 0.10384 (13.33%); the minimal feature set worsened it by 0.19662 (25.23%). Each ablation lost to Full Direct in all six folds and regressed most series. The **Full feature scope is the current selected feature scope** for the next controlled comparison, but individual features and the final pipeline are not frozen.

Recursive Global achieved macro RMSSE 0.76957 versus 0.77916 for Full Direct, won four of six folds, and improved 44 of 70 series, but its advantage was only 1.23%, it regressed 26 series, and 28-step inference was sequential. **Full Direct and Recursive remain strategy finalists; neither strategy is frozen.** The result does not justify selecting Direct as superior or opening the lockbox. See [`ablation_strategy_results.md`](ablation_strategy_results.md).

## Open

The model algorithm, target transformation, direct/recursive/multi-output strategy, final features, categorical encoding, hyperparameter budget, price-unavailability treatment, challenger architectures, prediction intervals, hierarchy reconciliation/WRMSSE, and downstream anomaly or inventory rules remain experimental decisions.

See [`docs/forecasting_methodology.md`](../../docs/forecasting_methodology.md) for definitions, metric formulas, dates, leakage protections, and downstream boundaries.
