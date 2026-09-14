# Phase 6 inventory feasibility audit

## Upstream and raw-schema audit

The authentic `sales_train_evaluation.csv` contains item/store hierarchy (`id`, `item_id`, `dept_id`, `cat_id`, `store_id`, `state_id`) and 1,941 daily unit-sales columns. `calendar.csv` maps dates and M5 day IDs to retail week, weekday/month/year, up to two event names/types, and CA/TX/WI SNAP flags. `sell_prices.csv` provides `store_id`, `item_id`, `wm_yr_wk`, and weekly `sell_price`.

These support demand history, hierarchy, known calendar context, and descriptive price. They do not contain on-hand inventory, inventory position, purchase orders, backorders, lead/review times, MOQ, case packs, capacities, service targets, supplier reliability, or ordering/holding/shortage economics.

The frozen Phase 1 contract produces `store_id`, `dept_id`, `state_id`, `forecast_date`, horizon 1–28, and nonnegative `predicted_sales` for exactly 70 department-store series and 28 consecutive days after the history cutoff. It requires at least 56 consecutive history days and known future calendar. Predictions below zero are explicitly clipped upstream.

## Feasibility findings

Keeping department-store planning grain is feasible and contract-compatible. It supports aggregate replenishment envelopes but not SKU purchase orders. Periodic review with `protection = deterministic lead time + review period` fits the daily forecast. Configurations above 28 days must be rejected because neither extrapolation nor a frozen extended forecast exists.

The anomaly bundle's exact OOS residual state is technically reusable at the identical grain as forecast-error uncertainty evidence. It contains 13,720 residuals across 70 series and 196 observed research dates through `d_1941`. This does not make the point forecast probabilistic, and anomaly scores/thresholds/IF must not enter ordering logic.

Normal-scale, empirical horizon-quantile, and user buffer-day safety stock are the bounded Step 2 candidates. Normal scaling requires explicit independence/distribution caveats; empirical quantiles require legitimate chronological aggregation and enough comparable windows; buffer days require explicit business ownership. Service level is a planning target parameter, not a guarantee.

## Scenario and operational boundaries

Every series needs its own explicit inventory state, lead time, review period, and service target. Optional MOQ/case-pack/max constraints are series-specific. Inputs and forecasts must share identity and snapshot origin. Quantities use units, never currency/orders/transactions. Price and EOQ are excluded.

Feasibility is **confirmed for a transparent scenario engine**, conditional on external operational inputs and the 28-day protection bound. Historical inventory KPI evaluation is infeasible from M5 and is prohibited.

