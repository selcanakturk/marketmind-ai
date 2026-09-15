# Inventory decision-support production engine

## Purpose, ownership, and grain

The engine recommends additional units to cover a configured protection period. It is decision support, not autonomous procurement, historical optimization, supplier scheduling, SKU allocation, causal diagnosis, or guaranteed stockout prevention. Grain remains store × department with daily forecast inputs; 70 M5 series are known.

MarketMind generates the 28-day demand forecast, per-series OOS residual uncertainty state, and optional informational anomaly context. The business must explicitly supply snapshot date, on-hand, on-order, backorders, deterministic lead time, review period, and planning service target. MOQ, case pack, maximum order, and explicit buffer-days override are optional. No business quantity is inferred from M5.

## Forecast and input contract

The unchanged Phase 1 HGBR-4 engine supplies exactly 28 finite, nonnegative daily predictions for snapshot+1 through snapshot+28. Every requested series must match exactly; missing, duplicate, gapped, wrongly dated, mismatched, negative, or non-finite forecasts fail. Historical averages are not a fallback.

Inventory components must be finite and nonnegative. Lead time is integer ≥0, review period integer ≥1, their sum is 1–28, and service target is [0.50, 0.999]. Multiple series may carry independent parameters; the API does not broadcast them.

## Position, demand, and uncertainty

`inventory_position = on_hand + on_order − backorders`; position may be negative. Lead-time demand sums days 1…lead time (zero at lead time zero). Protection demand sums days 1…lead+review. Expected daily demand is protection demand divided by protection days.

The compact uncertainty artifact has 70 rows with store, department, residual count, residual median/MAD, daily robust scale, and source dates. It comes from exactly 13,720 legitimate point-in-time OOS forecast residuals, 196 per series across 196 dates from 2015-02-02 through 2016-05-22. Runtime does not need full histories, anomaly scores, threshold, IF, or the forecast model.

Default `robust_normal` safety stock is `max(0, norm.ppf(service_level_target) × daily_robust_scale × sqrt(protection_period_days))`, where scale is `1.4826 × OOS residual MAD`. Service target is a planning factor—not achieved service or a probability guarantee. Zero MAD produces zero plus an explicit warning; no epsilon is added.

Historical errors had positive serial dependence and √H scaling understated cumulative robust variability, reaching a median observed/predicted ratio of 2.24 at H=28. This frozen limitation appears in every robust-normal decision and metadata but never modifies the calculation.

Explicit `user_buffer_days` mode instead sums forecast demand over the requested integer 0–28 days. It is a user-specified demand buffer; service target does not determine it. Supplying buffer days while using default mode is rejected. Methods are never added, averaged, maximized, or otherwise blended.

## Replenishment and constraints

`target_stock = forecast_protection_demand + safety_stock` and `unconstrained_order_quantity = max(0, target_stock − inventory_position)`. `replenishment_needed` follows the unconstrained value.

Positive need is adjusted in the frozen sequence: MOQ minimum → case-pack upward ceiling → whole-unit upward ceiling → maximum-order cap. Zero remains zero. The engine retains unconstrained and pre-maximum quantities and emits a warning when maximum clips need.

Days of cover is position divided by positive expected daily demand; otherwise undefined. Negative position may yield negative cover. Neutral statuses are sufficient inventory, replenishment recommended, constrained replenishment, and zero expected demand.

## Output and explainability

One stable output row includes snapshot/series identity; inventory components/position; lead/review/protection days; lead-time/protection/daily forecast demand; method and optional buffer days; residual count/MAD/scale; service target and safety stock; target; unconstrained, pre-max, and final order quantities; all constraints; replenishment flag; days of cover; warnings/status; and optional anomaly context.

The numeric fields reconstruct demand + safety = target; target − position, floored at zero = need; MOQ → case pack → unit ceiling → maximum = recommendation. Anomaly context is informational and cannot alter any numeric result. Price, EOQ, holding/ordering cost, and profit optimization remain excluded.

## Serialization, determinism, and verification

`models/inventory/inventory_bundle.joblib` contains the compact state, provenance, and frozen configuration. Save/load validates schema, 70 unique series, 196 residuals per series, finite statistics, exact MAD scaling, and versions. Identical bundle/inputs/forecasts/mode produce identical sorted output regardless of input row order.

Frozen scenarios and production tests cover sufficient/mild/negative stock, service monotonicity, 28/29-day boundaries, MOQ, case pack, combined constraints, maximum warning, zero demand, anomaly independence, invalid inputs, and artifact round-trip. These are scenarios—not historical inventory outcomes.

## Integration and limitations

No authentic inventory history or KPI exists. Recommendations inherit forecast bias, aggregation, 28-day limit, robust-normal approximation, missing supplier uncertainty/capacity, and business-input quality. The Python API `recommend_inventory(inventory_inputs, forecasts, bundle, anomaly_context=None)` is ready for a later FastAPI adapter. No endpoint, database, dashboard, or autonomous workflow exists.

