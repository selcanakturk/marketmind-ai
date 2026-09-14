# Phase 6 inventory decisions

## FROZEN IN STEP 1

| Decision | Frozen outcome |
|---|---|
| Business question | additional units needed to cover the configured protection period given forecast demand and explicit business inventory/planning inputs |
| Role | decision-support scenario engine; not autonomous procurement or optimization |
| Grain | store × department × day; 70 series |
| Forecast | unchanged Phase 1 nonnegative 28-day production forecast |
| Snapshot | forecast days must be the 28 consecutive dates immediately after snapshot date and match series identity |
| Inventory position | on hand + on order − backorders; components nonnegative, result may be negative |
| Required external inputs | all three inventory components, deterministic lead time ≥0, review period ≥1, service target in [0.50, 0.999] |
| Protection | lead time + review period; reject >28 days |
| Policy family | periodic-review order-up-to over protection demand; retain lead-time demand separately |
| Target/order | target = protection demand + safety stock; unconstrained order = max(0, target − position) |
| Constraints | positive need: MOQ, then case-pack ceiling, then max clip with warning; final physical quantity rounds up |
| Defaults | no silent operational defaults; explicit zeros allowed for on-order/backorders |
| Days of cover | descriptive position / mean demand; undefined for nonpositive mean; not core equation |
| Price/EOQ | price excluded; EOQ out of scope without real costs |
| Anomaly | optional informational warning only; cannot alter quantity |
| Evidence | tests/scenarios/invariants only; no fabricated historical inventory KPIs |

## OPEN FOR STEP 2

- Select one safety-stock method from normal robust-scale, empirical horizon residual quantile, or explicit buffer days.
- For empirical quantiles, freeze legitimate horizon-window construction across gapped OOS blocks and minimum sample handling.
- If normal scaling is selected, document residual independence/skew sensitivity and exact fallback for zero uncertainty.
- Freeze final neutral signal/warning vocabulary and batch input schema details.
- Design scenario experiments; do not build the production engine, API, or persistence yet.

