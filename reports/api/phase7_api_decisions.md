# Phase 7 API decisions

## FROZEN IN STEP 1

| Area | Decision |
|---|---|
| Surface | `/health`, `/ready`, `/api/v1/models`, and six atomic POST endpoints; no analyze-everything workflow |
| Versioning | business routes under `/api/v1`; breaking changes require v2 |
| Registry | central typed registry; validate/load each artifact once in lifespan; never retrain |
| Failure | partial readiness: unavailable module returns 503; unaffected modules serve |
| Loading | eager all six; recommendation cached mapping warmed before readiness |
| Forecast | existing history + 28-day calendar JSON contract |
| Segmentation | public V1 accepts prepared eligible nine-feature rows only; raw mode stays offline/later upload |
| Return risk | bounded transaction/product JSON plus snapshot/capacity; score explicitly uncalibrated ranking |
| Recommendation | compact distinct visitor history IDs; bundle first-seen/popularity/neighbor state replaces request-time raw event scan; frozen rank semantics unchanged |
| Anomaly | caller supplies actual and expected rows; stateless `score_batch` preview only; no HTTP commit |
| Inventory | caller supplies business rows plus complete 28-day forecast; no hidden forecast invocation |
| Orchestration | atomic only; forecast and anomaly dependencies remain explicit contracts |
| Payloads | JSON only with module row/item limits; file upload deferred |
| Execution | synchronous `def` inference routes in controlled threadpool with bounded concurrency |
| Errors | sanitized standard envelope; 400/404/409/422/500/503 semantics |
| Warnings | structured semantic warnings in responses, not docs-only |
| CORS | explicit configurable origins; localhost defaults; no wildcard+credentials |
| Observability | server UUID request ID; method/route/status/latency/module/safe error logs; no payload logging |
| Persistence | none for V1 inference; anomaly state commits explicitly out of scope |
| Security | no fake auth; document real future controls |
| OpenAPI | generated from typed schemas with summaries, response models, warnings, and error examples |
| Deployment | single process feasible; worker count constrained by duplicated artifact memory |

## OPEN FOR IMPLEMENTATION

- Exact Pydantic envelope class names, aliases, and pagination-free response nesting.
- Concrete registry loader interfaces and sanitized readiness reason enumeration.
- Body-byte middleware ceiling in addition to frozen per-module row limits.
- Threadpool/concurrency semaphore values after local API load testing.
- Whether optional anomaly IF diagnostics default enabled or require an explicit request flag.
- Exact FastAPI/Uvicorn compatible version pins after environment installation.

These are integration details. No implementation choice may modify production engine logic or frozen model semantics.
