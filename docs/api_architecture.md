# FastAPI backend architecture

## Purpose, module map, and dataset boundaries

One lightweight FastAPI service will expose six already-frozen production engines without moving formulas into HTTP code. M5 supports forecasting, anomaly preview, and inventory scenarios; Complete Journey supports segmentation and return-risk; RetailRocket supports recommendations. These research datasets do not share real entities. The product demonstrates modular retail intelligence, not one historical customer journey across all modules.

## Endpoint and versioning map

| Method and path | Purpose |
|---|---|
| `GET /health` | cheap process liveness only |
| `GET /ready` | aggregate and per-module artifact readiness |
| `GET /api/v1/models` | safe module/version/status/grain/method/limitations metadata |
| `POST /api/v1/forecast` | 28-day department-store demand forecast |
| `POST /api/v1/segments` | semantic assignment from prepared eligible feature rows |
| `POST /api/v1/return-risk` | 28-day no-return ranking from bounded history |
| `POST /api/v1/recommendations` | Item-CF from compact visitor history and serving catalog state |
| `POST /api/v1/anomalies` | non-mutating actual-versus-expected preview |
| `POST /api/v1/inventory/recommend` | inventory scenario from supplied 28-day forecast |

Business contracts remain under `/api/v1`; breaking changes require `/api/v2`. Additive optional response fields may remain v1. Health/readiness are operational and unversioned. There is no `analyze-everything` endpoint because entities and datasets differ.

## Registry, lifespan, and readiness

A central `ArtifactRegistry` will resolve paths from settings, deserialize and validate every bundle once during modern FastAPI lifespan startup, and provide read-only typed access. It never trains. Each module records `loading`, `ready`, or `unavailable` plus a sanitized reason code. One failure does not stop unrelated modules: its endpoint returns 503 while others serve. `/health` performs no inference or artifact validation; `/ready` and `/models` read cached registry state.

All six bundles are eager-loaded. Their compressed binaries total 29,505,198 bytes (~28.14 MiB). A local audit loaded all in ~8.02 s; traced current/peak allocations were ~41.35/~69.13 MB. Recommendation validation dominated at ~7.70 s but occurs once. Forecast/segmentation/return-risk/recommendation/anomaly/inventory binary sizes are 535,711 / 3,492 / 11,248,815 / 14,344,306 / 3,369,626 / 3,244 bytes.

## Request and response strategies

All V1 inference uses JSON. Multipart/CSV upload is deferred; large offline jobs should not masquerade as interactive JSON requests. Module-specific limits are enforced before DataFrame construction: forecast up to 70 series and 3,920 history rows plus 28 calendar days; segmentation 2,500 feature rows; return-risk 50,000 transaction rows; recommendations 500 distinct history items; anomalies 70 daily rows; inventory 70 decisions and 1,960 forecast rows. The deployment may additionally enforce a conservative body-byte limit.

Responses use ISO-8601 timestamps, JSON-safe nulls, deterministic ordering, `module_version`, `artifact_version`, `generated_at`, structured `warnings`, and the module payload. They never disclose artifact paths.

### Forecast contract

Request wraps the existing `forecast(bundle, history, future_calendar)`: daily history fields `d,date,store_id,dept_id,state_id,sales` with equal consecutive history (minimum 56 days), plus exactly 28 known future calendar rows `d,date,event_name,event_type,snap_CA,snap_TX,snap_WI` beginning one day later. Response contains store, department, state, forecast date, horizons 1–28, and nonnegative predicted sales. Maximum response is 1,960 rows.

### Segmentation contract

Public V1 exposes only prepared **eligible** feature rows: household ID plus the frozen nine named features and one snapshot date. The service calls `assign_eligible_households` with the loaded bundle components and returns household, date, semantic segment code/name, and centroid distance. Raw transaction/product mode remains an internal/offline callable and may later use file upload. Public output omits raw cluster ID as primary meaning. Distance is geometric atypicality—not confidence, probability, membership likelihood, or risk.

### Return-risk contract

Request supplies bounded point-in-time transactions, required product mapping, explicit snapshot, and optional capacity in `(0,1]`; service calls `score_return_risk`. Response preserves household eligibility/reason, ranking score, rank/percentile, selected capacity, and flag. The target is no basket in the next 28 days, not contractual churn. Score is an uncalibrated ranking score, not probability; default flag capacity remains top 10%.

### Recommendation contract and latency solution

Request supplies visitor ID, snapshot timestamp, `k`, and up to 500 distinct history item IDs—not the 2.76M-event table. A one-time serving state uses fields already in the frozen bundle: sparse 50-neighbor graph, item first-seen timestamps for snapshot availability, and frozen all-history popularity counts. The Step 2 adapter will score summed cosine similarity over distinct known history items, retain self-similarity, allow seen items, tie-break by item ID, and fill from available popularity exactly as frozen.

This removes per-request raw event validation/sorting while preserving Item-CF semantics. No visitor history is persisted in V1; callers provide current compact history. Bundle popularity is explicitly a training-cutoff snapshot until a future governed refresh exists.

### Anomaly contract and state policy

Request supplies one daily batch of actual and expected sales with optional calendar context; the service calls `score_batch`, never `score_and_update`. Expected sales are explicit—no hidden forecast orchestration. Output preserves robust score, direction, inclusive `|score|>=3`, independent top-five review rank, optional secondary IF score, and context. Score is not probability or causal diagnosis.

HTTP V1 is **stateless preview only**. It never mutates or persists residual state. A future authenticated, idempotent, chronological commit endpoint requires durable locking/versioning and is outside V1.

### Inventory contract

Request supplies business inventory/planning rows plus a complete aligned 28-day forecast and optional anomaly context; service calls `recommend_inventory`. There is no hidden forecast call. This keeps issuance/snapshot provenance visible and avoids sending 56-day forecast history/calendar merely to replenish. Robust-normal remains default, buffer days explicit, protection ≤28, and MOQ → case pack → whole-unit ceiling → maximum remains unchanged. Inventory warnings state approximation and scenario semantics.

## Dependencies and state

The logical DAG is Forecasting contract → Anomaly expected input; Forecasting contract → Inventory forecast input; Anomaly output → optional informational Inventory context. Segmentation, return risk, and recommendations are independent. Atomic request contracts prevent hidden circular or chained execution.

Loaded sklearn estimators and bundle arrays/DataFrames are treated read-only. Routes cannot mutate registry bundles. Anomaly updates are forbidden. Recommendation request history is local. Inventory is stateless. CPU-bound inference routes use synchronous `def` handlers (FastAPI threadpool), with bounded concurrency/backpressure rather than decorative `async`; no Celery is needed.

## Errors, warnings, CORS, and observability

Errors use `{"error":{"code":"...","message":"...","details":...},"request_id":"..."}`. Use 400 malformed syntax/contract envelope, 422 field/domain validation, 404 unknown entity, 409 temporal/state conflict, 503 unavailable module, and sanitized 500 unexpected error. Details use safe field/index information only—never paths, tracebacks, environment values, or raw exception internals. Full exceptions are logged internally.

Structured warnings preserve: segmentation distance is not confidence; return-risk score is not probability; recommendation fallback/no-history; anomaly score is not probability; inventory robust-normal limitation. Request IDs are server-generated UUIDs, returned in `X-Request-ID` and included in logs. Logs record ID, route, method, status, latency, module, and sanitized error code—not payloads or customer rows.

CORS comes from configuration. Development defaults to explicit localhost ports 3000 and 5173. Production requires explicit origins; wildcard with credentials is prohibited.

## Configuration, OpenAPI, security, and deployment

Settings cover environment, `/api/v1`, project-relative/environment-configurable artifact root, log level, explicit CORS origins, request limits, and request-ID header. Runtime contains no developer absolute path. FastAPI-generated OpenAPI uses summaries, descriptions, typed request/response models, warning semantics, and error examples; no parallel documentation system is needed.

V1 has no fake authentication. Before real customer data or public multi-tenant deployment it needs authentication, authorization, rate limiting, tenant isolation, TLS/secret management, secure storage, and retention policy. No database is required for stateless inference. Future persistence is needed for anomaly commits, saved scenarios, users/uploads, or server-owned visitor histories.

Single-process deployment is practical from artifact/memory size. Heavy raw Complete Journey inputs and recommendation startup validation are the main risks; limits and compact history contracts address request-time pressure. Multiple workers duplicate ~40+ MB loaded state, so worker count should follow hosting memory. Secondary IF is already inside the anomaly bundle and remains optional output.

Implementation adds `fastapi`, `uvicorn` (standard extras for local serving), and their compatible Pydantic dependency. `python-multipart`, database clients, task queues, and observability frameworks are not required for JSON-only V1.

## Router/service/schema structure and frontend

`api/main.py`, `settings.py`, `registry.py`, `errors.py`, and `middleware.py`; thin routers per endpoint; Pydantic schemas in module files plus common envelopes; service adapters per production engine. Routers validate/envelope, services translate DataFrames and call existing engines, registry owns artifacts. The React client consumes stable semantic JSON and never artifact formats.

Open implementation details are exact Pydantic field aliases/envelopes, body-byte middleware limit, threadpool capacity, and whether optional IF output defaults on or off. These do not reopen module methodology.

