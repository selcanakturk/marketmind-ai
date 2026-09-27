# Phase 8 frontend API audit

## Scope

This audit reads the Phase 7 FastAPI implementation, Pydantic schemas, registry, middleware, API architecture/usage documents, smoke report, decisions, and README. Runtime implementation is authoritative. No endpoint was changed.

## Actual surface

| Method | Path | Request | Response/useful UI data |
|---|---|---|---|
| GET | `/health` | none | `{status}`; cheap liveness only |
| GET | `/ready` | none | aggregate `status` and six module booleans |
| GET | `/api/v1/models` | none | six safe metadata objects: module, ready, version, family/method, grain, warnings, reason |
| POST | `/api/v1/forecast` | history + future calendar | `meta` + forecast rows |
| POST | `/api/v1/segments` | snapshot + prepared feature rows | `meta` + household segment rows |
| POST | `/api/v1/return-risk` | transactions + products + snapshot + optional capacity | `meta` + eligibility/ranking rows |
| POST | `/api/v1/recommendations` | visitor, snapshot, optional/default `k`, optional/default compact history | `meta`, status, fallback reason, ranked rows |
| POST | `/api/v1/anomalies` | actual + expected + optional calendar/IF flag | `meta` + scored preview rows |
| POST | `/api/v1/inventory/recommend` | inventory scenarios + forecast rows | `meta` + explainable decision rows |

All POST routes accept JSON. Response metadata contains nullable `module_version`, nullable `artifact_version`, UTC `generated_at`, and warning strings. Extra Pydantic fields are forbidden; infinity/NaN are rejected.

## Request and response findings

### Forecasting

Required history row: `d`, timestamp-compatible `date`, string store/department/state IDs, and nonnegative sales. Required calendar row: `d`, date, non-null string event name/type, and each state SNAP flag as 0/1. Both top-level arrays are required.

Response rows: date, store, department, state, integer horizon, predicted sales. History is not echoed; a historical-plus-forecast chart must retain submitted history client-side. There are no intervals or accuracy fields. Service limits history to 3,920 and distinct series to 70; the production engine owns consecutive-history and exact-calendar validation. Warning: fixed 28-day horizon.

### Segmentation

Top level requires snapshot and feature rows. Each row requires household ID and exactly nine numeric features. Recency/count/value fields are nonnegative; HHI and three share/rate fields are bounded `[0,1]`. Limit: 2,500 rows.

Response rows: household, snapshot, segment code/name, centroid distance. No population distribution, probability, or confidence exists. Warning explicitly forbids probability/confidence interpretation.

### Return risk

Transactions require household/store/basket/product IDs, nonnegative sales value, three nonnegative discount fields, and timestamp. Products require product ID and department; brand is optional. Snapshot is required; capacity is optional and must be greater than zero and at most one. Limit: 50,000 transactions.

Response rows preserve household, snapshot, eligibility status/reason, nullable risk score/rank/percentile, selected capacity, and flag. Nullable ranking fields matter for ineligible households. Warning identifies score as uncalibrated ranking rather than churn probability. No historical outcome timeline is returned.

### Recommendations

Visitor ID is a nonnegative integer; snapshot is required; `k` defaults to 20 and is bounded 1–1000; history defaults empty, is limited to 500, must be distinct, and uses nonnegative integers.

Response contains global status and fallback reason plus rank, visitor, snapshot, item, numeric score, source, and seen-before flag. Empty/unknown usable history can succeed through deterministic popularity fallback. The score has no probability semantics. No product title/image/category is available, so V1 must display item IDs rather than invent catalog attributes.

### Anomalies

Actual and expected arrays are required and use date/store/department keys plus nonnegative values. Optional calendar context carries nullable event name/type and default-zero binary SNAP fields. `include_if_diagnostic` defaults false. Actual or expected length above 70 is rejected.

Response includes actual, expected, residual, nullable robust score, direction, alert flag, nullable daily rank, review priority, nullable IF score, nullable event context, SNAP active, and nullable undefined reason. HTTP service calls only pure `score_batch`; state is not updated. API warning covers non-probability and non-mutation; the router also warns that IF is secondary. The frozen inclusive `|score| >= 3` threshold and top-five review policy come from the authentic production contract and must not become adjustable UI controls.

### Inventory

Scenario required fields: snapshot, store, department, nonnegative on-hand/on-order/backorders, nonnegative lead days, review days at least one, and service target `.5–.999`. Optional fields: positive MOQ, positive integer case pack, positive integer maximum, uncertainty method defaulting `robust_normal`, buffer days `0–28`, and string anomaly context. Forecast rows require date/store/department and nonnegative prediction. Limits: 70 decisions and 1,960 forecast rows; engine requires complete aligned horizon/series.

Response preserves the full explanatory chain: inventory position; protection period; lead/protection demand; expected daily demand; uncertainty method/buffer; residual evidence/scale; target input; safety stock; target stock; unconstrained need; MOQ/case/max and pre-max/final quantities; replenishment flag; coverage; constraint warning; anomaly context; planning status/warning. The service target is an input, not achieved performance. Anomaly context is informational.

## Operational contracts

- Registry eagerly attempts all six artifacts once during lifespan and tracks readiness independently.
- `/health` performs no registry access. `/ready` returns `ready` only when all module booleans are true, otherwise `degraded`.
- An unavailable required module raises `503` with code `MODULE_UNAVAILABLE`; successful modules remain usable.
- All responses receive a server UUID `X-Request-ID`. Error bodies include the same canonical identifier.
- Error shape is `{"error":{"code","message","details"},"request_id"}`. Current handlers explicitly produce 422 validation/engine errors, 503 unavailable, and sanitized 500. Architecture reserves 400/404/409 semantics, so the frontend supports them without assuming every case is currently emitted by custom handlers.
- CORS is explicit and environment-configured. Bounded request concurrency defaults to four.
- Warning strings are semantic API output and must not be discarded.

## Visualization-safe fields and prohibited interpretations

| Safe visualization | Required caveat |
|---|---|
| Submitted history + returned predicted sales over date | no confidence band or live accuracy |
| Response-only segment counts | submitted subset, not population share; distance is not confidence |
| Risk rank/percentile and flagged response counts | score is uncalibrated, not probability |
| Recommendation rank/source/seen flag | score is not probability; no conversion/lift claim |
| Actual vs expected/residual/score/review flags | anomaly is not causal; IF secondary; preview does not commit |
| Inventory position, demand, safety stock, target, constraints, final order | service target is not achieved service; no savings/stockout claim |
| Module readiness count and metadata | system status, not business performance |

## Documentation and implementation discrepancies

1. The Phase 8 prompt’s context names `POST /api/v1/inventory/recommendations`; runtime, Phase 7 contracts, API usage, smoke report, and tests all use **`POST /api/v1/inventory/recommend`**. Frontend freezes the runtime path.
2. `src/marketmind/api/__init__.py` still says routes are “not implemented yet,” while the application and all routes exist. This is a stale package docstring, not a runtime contract.
3. README status correctly says Phase 7 is implemented, but a later sentence says “No API ... implementation is claimed complete.” That sentence is stale and is corrected in the Phase 8 update.
4. Phase 7 architecture mentions 400/404/409 policy, but current centralized custom handlers specifically implement 422, 500, and 503; framework routing may provide other shapes in edge cases. The frontend will defensively normalize all specified status classes and prefer the canonical envelope when present.
5. OpenAPI descriptions are useful but terse: routers define summaries and response models, while most schema fields lack per-field descriptions. Frontend planning therefore relies on implementation plus Phase 7 documentation, not OpenAPI descriptions alone.
6. Forecast `CalendarRow.event_name` and `event_type` are required strings in runtime, even though anomaly calendar equivalents are optional. The frontend must not treat them as optional in forecast input.

None of these discrepancies blocks the frozen UI. No backend change is required for Step 2.

## Feasibility conclusion

All planned screens can be implemented truthfully using current V1. The principal product constraint is intentional statelessness: Overview cannot show business KPIs/history, workflows begin with explicit request inputs, and cross-module transfers require user-visible payload construction. Recommendation lacks catalog presentation data, so item IDs are the honest display. Inventory scenarios require synthetic business inputs where no authentic stock state exists.

