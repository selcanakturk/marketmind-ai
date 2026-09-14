# Inventory decision-support methodology

## Purpose and business decision

V1 answers: **Given MarketMind's forward demand forecast and explicitly supplied inventory/planning parameters, how many additional units should be ordered to cover the configured protection period?** It is transparent scenario-based decision support—not autonomous procurement, warehouse/supplier optimization, SKU allocation, or causal stockout diagnosis.

## Data support matrix and input ownership

| Ownership | Supported fields |
|---|---|
| Observed M5 | daily unit sales `d_1…d_1941`; item, department, category, store, and state IDs; calendar date/week/day/month/year; events and types; state SNAP flags; weekly item-store sell price |
| MarketMind generated | nonnegative 28-day department-store daily forecast; legitimately OOS per-series residual histories/uncertainty candidate; optional recent anomaly context |
| Business/user supplied | snapshot on-hand, on-order, backorders, deterministic lead time, review period, planning service target; optional MOQ, case pack, maximum order |
| Not observed in M5 | inventory balances/position, purchase orders, backorders, supplier lead time/reliability, review cadence, service targets, MOQ/case packs, warehouse capacity, ordering/holding/shortage costs |

No absent operational value may be inferred from M5. On-order and backorders are required explicit inputs in V1, even when the business supplies zero; there are no silent inventory defaults.

## Planning grain and forecast dependency

The frozen grain is store × department × day, matching the Phase 1 global HGBR-4 forecast: 70 series and 28 consecutive future dates. Department aggregation improves forecast stability but cannot produce SKU ordering or allocation. Forecasts must start the day after `snapshot_date`, match the inventory series exactly, contain each of 28 consecutive dates once, and be finite/nonnegative. The upstream model already clips negative predictions to zero; inventory validation rejects any negative supplied demand.

## Inventory state and time definitions

All quantities are compatible physical units. `inventory_position = on_hand_inventory + on_order_inventory − backorders`; the three components must be finite and nonnegative, while position may be negative. `lead_time_days` is a business-supplied deterministic integer ≥0. `review_period_days` is a business-supplied integer ≥1. V1 periodic-review protection is `lead_time_days + review_period_days`.

Protection exceeding 28 days is rejected. V1 neither extrapolates nor substitutes a historical average. A later version may define an explicit external extended-forecast contract.

## Demand aggregation, uncertainty, and service semantics

`forecast_lead_time_demand` sums forecast days 1 through lead time; `forecast_protection_demand` sums days 1 through protection period. They remain separate. `expected_daily_demand` is the protection-period mean.

The anomaly state is feasible as an uncertainty source because it stores 13,720 legitimate OOS daily residuals by the same grain. Reuse is limited to forecast-error estimation; anomaly threshold, robust score, IF, and alert policy have no inventory meaning.

Step 2 will compare three transparent safety-stock candidates without reopening forecast/anomaly research:

1. `normal z × robust daily residual scale × sqrt(protection days)`: compact and monotone, but assumes independent normal-like errors and may miss skew/serial dependence.
2. Empirical comparable-horizon residual-sum quantile: fewer distributional assumptions, but needs enough same-horizon chronological OOS windows and careful treatment of research-block gaps.
3. User-specified demand-buffer days: clearest scenario control, but wholly business supplied and not statistical uncertainty.

Selection remains open for Step 2. The planning `service_level_target` is a cycle-service safety-factor parameter, not a guaranteed probability of avoiding stockout. V1 accepts `[0.50, 0.999]`; candidate A uses a statistical inverse-normal function, never hard-coded approximations. No probabilistic demand forecast is claimed.

## Periodic-review target policy

The frozen policy family is order-up-to:

`target_stock = forecast_protection_demand + safety_stock`

`unconstrained_order_quantity = max(0, target_stock − inventory_position)`

This is distinct from a continuous-review reorder point. For dashboard explanation, `inventory_position_below_lead_time_demand`, `inventory_position_below_target_stock`, `projected_inventory_after_lead_time`, `protection_period_gap`, and `replenishment_needed` are neutral planning signals—not stockout probabilities or diagnoses.

Positive raw need below MOQ is raised to MOQ; zero remains zero. Next, positive quantity rounds upward to the next case pack. A maximum then clips the allowed recommendation, while unconstrained quantity is preserved and `constraint_warning` exposes unmet calculated need. Precise intermediate values remain fractional; only the physical final recommendation rounds upward to whole units. A maximum may therefore cap below the unconstrained need; it must never be hidden.

`days_of_cover = inventory_position / expected_daily_demand` is an approximate descriptive field because daily demand varies. It is undefined when expected daily demand ≤0 and is not the ordering equation.

## Output contract and explainability

Stable proposed fields: `snapshot_date`, `store_id`, `dept_id`, `on_hand_inventory`, `on_order_inventory`, `backorders`, `inventory_position`, `lead_time_days`, `review_period_days`, `protection_period_days`, `forecast_lead_time_demand`, `forecast_protection_demand`, `expected_daily_demand`, `forecast_uncertainty`, `uncertainty_method`, `service_level_target`, `safety_stock`, `target_stock`, `unconstrained_order_quantity`, `recommended_order_quantity`, `replenishment_needed`, `days_of_cover`, `constraint_warning`, and optional `recent_anomaly_context`.

Every recommendation decomposes as forecast protection demand + safety stock = target stock; target stock − inventory position, floored at zero = unconstrained need; MOQ → case-pack ceiling → maximum cap → upward whole-unit rounding = recommendation.

## Scenario verification

Because M5 has no inventory ground truth, verification uses mathematics, unit/contract tests, monotonicity, deterministic scenario tests, and edge cases. Required scenarios are sufficient stock, mild need, negative position from backorders, high service target, 28-day boundary, rejected >28 days, MOQ, case pack, maximum cap, and zero demand. Scenario inputs must be labeled hypothetical—not historical M5 outcomes.

## Price, EOQ, anomaly relationship, and unsupported claims

Sell price is available but excluded from V1. EOQ is out of scope because M5 lacks ordering and holding costs and supplier economics. Recent anomaly context may display a warning to review inputs; it cannot multiply or otherwise change an order recommendation without separate future research.

Prohibited claims include historical stockout reduction, fill-rate improvement, inventory-cost reduction, probability of stockout, causal stockout diagnosis, autonomous optimization, or observed inventory performance. No pseudo inventory history may be constructed from cumulative sales.

## Limitations and open decisions

Recommendations inherit forecast bias, the 28-day limit, and department-store aggregation. V1 has no SKU inventory, supplier uncertainty, lead-time distribution, warehouse capacity, or observed inventory history. Safety-stock candidate selection, empirical window construction, residual dependence diagnostics using existing OOS state, and exact warning vocabulary remain open for Step 2. Production engine, persistence, API, and dashboard are later work.

