# M5 Forecasting — Accuracy Dataset Audit

## Dataset Identity

This audit uses the authentic **M5 Forecasting — Accuracy** competition release from the [canonical Kaggle competition](https://www.kaggle.com/competitions/m5-forecasting-accuracy/data). The competition asks participants to forecast hierarchical Walmart retail unit sales over two 28-day horizons.

M5 is **Walmart retail data, not e-commerce transaction data**. It contains no customers, orders, baskets, browsing events, or authenticated user behavior.

Files inspected under the Git-ignored `data/raw/m5/` directory:

- `calendar.csv`
- `sell_prices.csv`
- `sales_train_validation.csv`
- `sales_train_evaluation.csv`
- `sample_submission.csv`

Kaggle identifies the data as subject to the competition rules. Public-portfolio use, attribution, and redistribution must follow those rules; raw competition files should not be committed.

## File Structure

| File | Shape | Disk | Optimized memory | Grain / candidate key |
|---|---:|---:|---:|---|
| `calendar.csv` | 1,969 × 14 | 0.10 MB | 0.22 MB | one day / `d` |
| `sales_train_evaluation.csv` | 30,490 × 1,947 | 116.10 MB | 116.62 MB | one item-store series / `id` |
| `sales_train_validation.csv` | 30,490 × 1,919 | 114.45 MB | 115.00 MB | one item-store series / `id` |
| `sample_submission.csv` | 60,980 × 29 | 4.99 MB | 10.03 MB | one series-horizon identifier / `id` |
| `sell_prices.csv` | 6,841,121 × 4 | 193.97 MB | 72.01 MB | one observed item-store-week price / composite key |

No file contains exact duplicate rows or candidate-key violations. Sales, price, and submission files have no missing values. Calendar event fields are intentionally sparse: primary event name/type are absent on 91.77% of days and secondary event fields on 99.75%.

The optimized audit uses categorical identifiers, `int16` sales, and `float32` prices without changing values. Raw file content remains untouched.

## Hierarchy

Empirically verified bottom-level cardinalities:

- 3 states
- 10 stores
- 3 categories
- 7 departments
- 3,049 items
- 30,490 unique item-store series

Every evaluation row corresponds to a unique item-store pair. These bottom series aggregate into store, state, category, department, and combined hierarchy levels; the official competition evaluates 42,840 series across 12 levels.

## Temporal Coverage

- First sales day: `d_1` — 2011-01-29
- Validation file end: `d_1913` — 2016-04-24
- Evaluation training-file end: `d_1941` — 2016-05-22
- Calendar end: `d_1969` — 2016-06-19
- Evaluation history: 1,941 daily observations
- Published future calendar beyond `d_1941`: 28 days
- Competition horizon: 28 days

The validation matrix has 1,913 daily columns. The evaluation matrix contains the same hierarchy and identical first 1,913 sales values, followed by the expected 28 additional observed days. The daily calendar is continuous through the later 28-day competition horizon.

The dataset boundary is competition-defined, rather than evidence of a retailer’s full history. Individual products enter at different dates, so a complete calendar does not imply every item-store series has a full active lifecycle.

## Sales Density

An active day has units greater than zero. Audit bands are descriptive only: “extreme” means at least 90% zero days, “sparse” at least 75%, “moderate” 25–<75%, and “dense” below 25%. They are not filtering rules.

| Level | Series | Median active days | Median active ratio | Overall zero days | ≥90% zero series | ≥75% zero series | <25% zero series |
|---|---:|---:|---:|---:|---:|---:|---:|
| Item-store | 30,490 | 518 | 26.69% | 68.00% | 16.84% | 47.24% | 5.16% |
| Department-store | 70 | 1,936 | 99.74% | 0.27% | 0% | 0% | 100% |
| Category-store | 30 | 1,936 | 99.74% | 0.22% | 0% | 0% | 100% |
| Store total | 10 | 1,938.5 | 99.87% | 0.12% | 0% | 0% | 100% |
| Category total | 3 | 1,937 | 99.79% | 0.15% | 0% | 0% | 100% |

Aggregation changes the statistical problem dramatically. Department/store and category/store series are nearly continuous, while almost half of item-store series are at least 75% zero.

## Intermittency

Bottom-level item-store findings:

- No series is entirely zero.
- Median first nonzero day: 160.
- Median active lifespan: 1,773 days.
- Median active days: 518.
- Median active-day ratio: 26.69%; median zero share: 73.31%.
- Median total demand: 868 units.
- Median longest zero run: 351 days.
- 5,133 series (16.84%) have at least 90% zero days.
- 14,402 (47.24%) have at least 75% zero days.
- 14,516 (47.61%) fall in the descriptive 25–<75% zero band.
- 1,572 (5.16%) have less than 25% zero days.

At the 90th percentile, the first nonzero sale is day 1,162 and the longest zero run is 1,169 days. The sparsity reflects assortment introductions and intermittent demand; zeros must not be removed automatically or assumed to mean stockouts.

## Seasonality

Aggregate daily demand shows clear descriptive temporal structure:

- mean Saturday demand: 41,706 units;
- mean Sunday demand: 41,304;
- mean Wednesday demand: 30,130;
- monthly/annual totals show long-term level changes across 2011–2016;
- the raw aggregate series has visible weekly and long-term variation.

There are 158 training-history days with a primary named event. Their mean total demand (33,030) differs from non-event days (34,609), but this unconditional comparison is confounded and is not a causal effect.

State SNAP-day mean sales exceed non-SNAP-day means in the raw descriptive comparison for CA, TX, and WI. Again, timing, seasonality, assortment, and other factors confound this relationship. The audit verifies usable context, not causal lift.

## Price Data

`sell_prices.csv` has 6,841,121 unique item-store-week records:

- 30,490 item-store pairs, covering every sales pair at least once;
- 282 price weeks matching 282 calendar weeks;
- no missing prices in observed records;
- 79.56% coverage of the naïve all-pair/all-week panel;
- median 260 observed price weeks per pair;
- median 2 observed price changes per pair;
- 72.95% of pairs have at least one observed price change;
- maximum observed changes for a pair: 50.

Missing rows from the full Cartesian panel should not automatically be imputed: an item may not yet be carried. Price is observational, and sales-price association is not causal.

For a future forecast, price is only a known future covariate when a planned price schedule is genuinely available at forecast issuance. Otherwise, price requires scenario assumptions, last-known treatment, or evaluation restricted to information available at each cutoff.

## Calendar Data

The calendar has unique `date` and `d` keys, 1,969 consecutive days, 282 Walmart weeks, and six represented years. It provides:

- date, weekday/wday, month, and year;
- primary and secondary event names/types;
- state-specific SNAP indicators;
- `wm_yr_wk` for price joins;
- 28 future rows after the observed evaluation-training history.

Calendar schedules can be known-in-advance covariates when the corresponding real deployment schedule is available. They differ from historical-sales features such as lags, rolling values, and expanding statistics, which must be recomputed exclusively from information available before each cutoff. No such features were created here.

## Forecasting Grain Options

### A. All item-store series

- **Methodological value:** maximum fidelity to M5 and the hierarchy; exposes intermittent demand honestly.
- **Cost:** 30,490 outputs per origin and 853,720 forecast values for each 28-day horizon. Repeated backtests multiply this cost.
- **Risk:** median series is 73.31% zero; independent per-series modeling would be cumbersome, unstable for sparse histories, and deployment-heavy.
- **Portfolio/dashboard:** rich but visually and operationally unwieldy.

### B. Selected item-store series

- **Methodological value:** preserves bottom-level forecasting/intermittency on interpretable examples.
- **Cost:** manageable locally and deployable.
- **Risk:** selection criteria can introduce cherry-picking or survivorship bias and must be frozen transparently before experimentation.
- **Portfolio/dashboard:** strongest item-level story if examples include different intermittency regimes.

### C. Department-store level

- **Scale:** 70 series; all fall in the descriptive dense band.
- **Value:** stable, operationally meaningful, computationally light, and suitable for repeated backtesting.
- **Tradeoff:** hides item-level demand and inventory-relevant granularity.

### D. Category-store level

- **Scale:** 30 very dense series.
- **Value:** simplest robust forecasting/deployment/dashboard option.
- **Tradeoff:** may be too aggregated to demonstrate challenging demand behavior.

### E. Multi-level / hierarchical demonstration

- **Value:** combines robust aggregate forecasting with selected bottom-level examples and demonstrates coherence across levels.
- **Cost:** adds reconciliation/evaluation complexity, though far less than deploying every bottom series independently.
- **Portfolio:** highest methodological breadth if tightly scoped.

The empirical evidence most strongly supports a **scoped multi-level demonstration**, with department-store or category-store as a reliable core and a predeclared, defensible item-store subset to demonstrate intermittency. This is a recommendation for the later design decision, not a frozen grain.

## Backtesting Feasibility

One possible lockbox is the final observed 28 days, `d_1914`–`d_1941`. It should remain untouched during model selection if adopted. The history before it supports many non-overlapping 28-day validation windows:

| Minimum history before a validation window | Available non-overlapping 28-day windows before lockbox |
|---:|---:|
| 365 days | 55 |
| 730 days | 42 |
| 1,095 days | 29 |

Using every possible window would be unnecessary and computationally expensive. Candidate designs include three to five recent rolling origins plus an earlier stability origin, or expanding-window origins spaced by 28/56 days. The exact windows, minimum history, and rolling versus expanding policy remain unfrozen.

The competition test labels for `d_1942`–`d_1969` are not present in the inspected sales matrices. Calendar availability is not outcome availability.

## Metric Considerations

- **MAE:** understandable absolute-unit error, but scale-dependent.
- **RMSE:** emphasizes large misses; scale-dependent and spike-sensitive.
- **WAPE:** intuitive aggregate ratio, but can hide series differences and fails when aggregate actual demand is zero.
- **MASE:** cross-series scaling against a naïve error, but denominator and seasonal-period choices need care for constant or short history.
- **RMSSE:** M5’s squared scaled formulation; supports cross-series comparison but emphasizes large errors and requires a nonzero scale.
- **WRMSSE:** competition-aligned hierarchy score weighted by recent dollar sales; valuable for hierarchical evaluation but more complex and dependent on precisely reproduced weights.

MAPE is a poor default because actual zero demand makes it undefined and near-zero demand makes it unstable. No primary metric was selected.

## Computational Feasibility

- Raw files: 429.60 MiB by file-size sum (about 469 MB filesystem usage).
- All optimized tables retained: approximately 313.88 MB before intermediates.
- Evaluation sales matrix: 59,181,090 values.
- A hypothetical long table: 59,181,090 rows; the value column alone is about 225.8 MB as `float32`, before repeated identifiers, dates, and DataFrame overhead.
- One all-series 28-day origin: 853,720 forecast values.
- Measured local loads: evaluation 3.42 seconds, validation 3.35, and prices 2.98 in this environment.

Pandas and NumPy handled file inspection, hierarchy aggregation, density, intermittency, calendar, and price audits comfortably. No Spark, Dask, Polars, or database is justified. Modeling all 30,490 series independently across many origins would be expensive; pooled, aggregate, or scoped approaches remain feasible with the existing lightweight stack.

## Anomaly Detection Feasibility

Forecast outputs could later provide `expected_t`, compared with `actual_t` at item-store, department-store, category-store, or aggregate levels. A defensible design would:

- retain seasonal/calendar context;
- normalize residual magnitude for series scale;
- distinguish intermittent zeros from unusual deviations;
- use prediction intervals only if their construction and empirical coverage are justified;
- label outputs as anomaly/deviation scores, not probabilities.

Dense aggregate levels offer the strongest initial residual-monitoring feasibility. Sparse item-store monitoring would need demand-type-specific normalization and careful false-alert analysis. No anomaly score was created.

## Inventory Limitation

M5 contains none of the following operational fields:

- current on-hand inventory;
- supplier lead time;
- inbound replenishment;
- safety stock.

Daily sales are not inventory, and zero sales do not prove stockout or zero demand. MarketMind will not claim to infer real inventory state from M5.

A future Inventory Intelligence decision-support layer may accept user-provided `current_stock`, `lead_time`, `incoming_quantity`, and service-level assumptions, then combine them transparently with demand forecasts. No inventory data or rules were fabricated.

## Known Limitations

- Walmart retail rather than e-commerce transactions.
- No customers, orders, baskets, web behavior, or recommendation identity.
- Bottom-level demand is highly intermittent and product entry dates vary.
- No operational inventory or stockout flag, so observed sales may not equal unconstrained demand.
- Future prices are not automatically known in deployment.
- Event/SNAP/price relationships are observational, not causal.
- The competition’s external test outcomes are not included in inspected sales files.
- All-series multi-origin computation and hierarchy evaluation add substantial complexity.
- Competition rules and raw-data redistribution conditions require confirmation for public GitHub publication.

## M5 Feasibility Verdict

| MarketMind module | Rating | Empirical basis |
|---|---|---|
| Demand Forecasting | **Strong** | 1,941 daily observations, 30,490 bottom series, verified hierarchy, prices/calendar, and ample rolling-window history. |
| Sales Anomaly Detection | **Strong** | Dense aggregate histories and forecast-residual framing are viable; bottom-level intermittency requires scoped treatment. |
| Inventory Decision Support | **Moderate** | Forecasts can support decisions, but all real inventory inputs must be supplied externally. |
| Customer Segmentation | **Unsupported** | No customer identity or customer transactions. |
| Customer Return Risk | **Unsupported** | No customer identity or longitudinal customer behavior. |
| Recommendation | **Unsupported** | No user-item interaction data. |

## Phase 0 Exit Criteria

| Criterion | Status | Evidence / remaining boundary |
|---|---|---|
| Dataset identity | Met | Exact Olist, Complete Journey 2.0, RetailRocket, and M5 distributions documented. |
| Temporal coverage | Met | Empirically measured for all selected/rejected candidates. |
| Table grain | Met | Keys, cardinalities, and join risks audited. |
| Target feasibility | Met for phase | Module support/rejection established; exact targets intentionally remain Phase 1 design work. |
| Major leakage risks | Met | Temporal cutoffs, censoring, future metadata/prices, and post-outcome fields documented. |
| Computational feasibility | Met | Local memory/disk and large-table constraints measured for all major candidates. |
| Module-dataset mapping | Met, pending sign-off | Proposed architecture is empirically supported but not yet frozen. |
| Known limitations | Met | Domain mismatch, identity, sparsity, censoring, inventory, and metadata limitations recorded. |
| Public portfolio/license concerns | Identified, not legally resolved | M5 competition rules and RetailRocket/Olist license obligations need final publication review. |

### Unresolved before modeling

- Approve/freeze the final module-dataset architecture.
- Choose and predeclare M5 forecasting grain/subset rules without cherry-picking.
- Freeze temporal development windows and one untouched lockbox.
- Select primary/secondary forecasting metrics and hierarchy weights.
- Decide how future price availability will be represented.
- Define Complete Journey return-risk snapshots and horizon without calling inactivity contractual churn.
- Define RetailRocket warm/cold-start evaluation coverage and ranking protocol.
- Resolve public portfolio attribution/redistribution requirements; do not commit raw data.
- Define minimum resource/deployment budgets for each module.

The empirical feasibility work requested for Phase 0 is complete. Phase 1 should not begin until these design choices receive explicit review and sign-off.
