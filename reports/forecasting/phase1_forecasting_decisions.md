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

## Open

The model algorithm, target transformation, direct/recursive/multi-output strategy, final features, categorical encoding, hyperparameter budget, price-unavailability treatment, challenger architectures, prediction intervals, hierarchy reconciliation/WRMSSE, and downstream anomaly or inventory rules remain experimental decisions.

See [`docs/forecasting_methodology.md`](../../docs/forecasting_methodology.md) for definitions, metric formulas, dates, leakage protections, and downstream boundaries.
