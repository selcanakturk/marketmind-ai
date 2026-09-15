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

## STEP 2 DEVELOPMENT EVIDENCE

The finalized forecast-error corpus contains 13,720 legitimate OOS residuals: 70 series × 196 dates in seven 28-day blocks. Continuity-safe per-series windows fall from 196 at H=1 to only 7 at H=28. Median within-series autocorrelation is positive at lags 1/2/3/7 (0.400/0.270/0.196/0.311). Observed cumulative robust scale increasingly exceeds daily robust scale × √H: median ratio 1.16 at H=2, 1.59 at H=7, 1.92 at H=14, and 2.24 at H=28.

Using a conservative minimum of ten expected upper-tail observations, empirical per-series quantiles are supported at 0.90 only through H=14. They are unsupported at 0.95/0.975/0.99 for every horizon and at every target for H=21/28. Overlapping windows are not independent. Buffer days remain deterministic but do not represent the service target.

## FROZEN SAFETY-STOCK DECISION

Primary V1 is **Method A: robust normal scale**:

`safety_stock = max(0, norm.ppf(service_level_target) × (1.4826 × per-series daily residual MAD) × sqrt(protection_period_days))`.

It is selected for complete horizon/series coverage, deterministic and monotone behavior, direct compatibility with the frozen service input, transparent inputs, and lightweight deployment. It is explicitly an approximation—not an achieved service probability. Positive serial dependence and cumulative-scale ratios show likely long-horizon undercoverage; this limitation must be visible in production metadata and UI. No empirical correction factor was fitted.

Method C remains the only optional secondary method as an explicit user buffer-days scenario override. It is never blended with Method A and service-level target does not determine buffer days. Method B remains diagnostic/reference only because the upper tail is too sample-limited. Zero per-series MAD returns zero with an explicit zero-uncertainty warning.

## POST-FREEZE SCENARIO VERIFICATION

After the decision artifact was written, deterministic scenarios confirmed: sufficient stock → zero; mild need → positive; negative position increases need; raw 40 + MOQ 100 → 100; raw 101 + case pack 24 → 120; raw 40 + MOQ 100 + case pack 24 → 120; pre-max 240 + maximum 200 → 200 with warning; anomaly context leaves all numeric results unchanged. The 28-day boundary is accepted, 29 days rejected, service/horizon monotonicity holds for Method A, and zero demand yields undefined days of cover.

## STEP 3 — productionization

The frozen Method A formula, Method C explicit override, service semantics, 28-day bound, policy equations, and constraint ordering are implemented without change. A compact 70-row uncertainty bundle uses only residual median/MAD/scale and provenance; it embeds neither residual histories nor upstream models. `recommend_inventory` supports independently parameterized series, strict forecast/snapshot alignment, structured explainability, deterministic row ordering, explicit robust-normal limitations, and informational-only anomaly context. Serialization, frozen-scenario regressions, and operational smoke testing passed. No inventory history/KPI, method comparison, retuning, FastAPI endpoint, or upstream change occurred.
