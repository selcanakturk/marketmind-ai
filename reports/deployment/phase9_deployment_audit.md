# Phase 9 Step 1 deployment architecture audit

Date: 2026-09-27  
Scope: repository and public-demo deployment readiness; no implementation or deployment

## Repository evidence

- Git branch `main`, GitHub origin `selcanakturk/marketmind-ai`; 420 tracked files and approximately 28 MiB of tracked working-tree content at audit time.
- No `pyproject.toml`, lock/constraints file, `.python-version`, `.nvmrc`, Dockerfile, CI workflow or deployment manifest exists.
- `requirements.txt` uses mostly unpinned top-level packages. The active environment is Python 3.13.2 and `pip check` reports no broken requirements, but recreating its exact versions is not guaranteed.
- Frontend has exact direct versions and lockfile v3. It uses Node 23.9.0 locally, has no engines declaration, and has a known Node-24-dependent Vitest remediation.
- Vite builds with `npm run build` to `dist`; `VITE_MARKETMIND_API_BASE_URL` is centralized with local fallback `http://localhost:8000`. No production URL is hardcoded.
- Vite's default public-source-map behavior is retained. Cloudflare Pages needs root directory `frontend`, build `npm run build`, output `dist`.

## Backend evidence

- `APISettings` reads `MARKETMIND_ENV`, `MARKETMIND_ARTIFACT_ROOT`, `MARKETMIND_LOG_LEVEL`, `MARKETMIND_CORS_ORIGINS`, and `MARKETMIND_MAX_CONCURRENT_REQUESTS`.
- CORS defaults to explicit localhost origins, methods `GET/POST`, headers `Content-Type/X-Request-ID`, and credentials enabled. Production origin validation is not enforced.
- `RequestContextMiddleware` creates UUID request IDs, logs method/path/status/latency/safe error code, and bounds whole-process concurrency (default four). It does not log payloads.
- Errors are centrally enveloped; unexpected client messages are generic and path/joblib-like engine messages are redacted.
- Pydantic forbids extra fields and non-finite numbers. Service adapters enforce 3,920 forecast history rows/70 series, 2,500 segmentation rows, 50,000 risk transactions, 500 recommendation history IDs, 70 anomaly rows, 70 inventory decisions and 1,960 inventory forecast rows.
- No raw request-byte limit or per-client rate limiter exists. Large strings and a valid 50,000-row risk request can still consume material parsing memory/CPU.
- Six synchronous inference routes execute through FastAPI's controlled threadpool. Lifespan eagerly loads all artifacts once. One artifact failure is caught and marks only that module unavailable.
- `/health` is cheap liveness; `/ready` returns HTTP 200 with `ready` or `degraded`; `/api/v1/models` exposes safe metadata only. OpenAPI, Swagger and ReDoc are public by default.
- Existing application logs do not explicitly configure root/Uvicorn format or startup module timings. `module` is not currently an explicit access-log field, despite older architecture wording.

## Artifact evidence

All six required binaries exist locally and load in the verified application, but `.gitignore` excludes every one and `git ls-files models` confirms none is tracked. Total binary size is 29,505,194 bytes; recommendation is largest at 14,344,306 bytes, followed by return risk at 11,248,815. No SHA-256 manifest exists. Metadata records versions and some library versions but not binary integrity.

This contradicts any assumption that a clean Git checkout can serve models. It is a **Step 2 blocker**, not a reason to retrain. The regular-Git proposal is below GitHub's enforced 100 MiB per-object limit, although GitHub recommends LFS for large binaries.

Historical API evidence measured sequential eager load at ~8.02 seconds, traced Python current/peak allocation ~41.35/~69.13 MB, with recommendation validation ~7.70 seconds. These do not equal full RSS. A 512 MB host is plausible but requires Linux RSS and max-request measurement before deployment.

## Frontend/demo/privacy evidence

The eight-route frontend calls only the configured API origin. Demos are small input fixtures labeled illustrative/synthetic; Inventory explicitly says M5 has no inventory balances. No private data or stored model output is bundled. Forecast transfers are in-memory, user-controlled and non-persistent. Dataset identities remain separated.

## Dependency/security evidence

- `pip check`: passed in the current environment; no Python vulnerability scanner is installed or claimed.
- Latest completed npm audit: zero high/critical and two moderate development-only findings in Vitest/`@vitest/mocker` 3.2.7. Node 24 plus Vitest 4.1.11+ is the narrow planned fix.
- Runtime Python ranges allow future incompatible releases; `numpy`, `pandas`, `scikit-learn`, `scipy`, and `joblib` are not pinned despite joblib deserialization compatibility needs.
- CORS is appropriately explicit by default but credential support is unnecessary for the selected no-auth demo.
- There is no authentication, persistence or tenant data. This makes public bounded stateless inference appropriate, but endpoints are presently susceptible to request flooding and model scraping.

## Documentation discrepancies

- `docs/api_architecture.md` says logs include `module`; current middleware logs route but not a separate module field.
- Phase 7 left a body-byte ceiling open; it remains unimplemented.
- The root README describes model bundles as ignored while local API operation assumes them present. That is accurate locally but insufficient for Git deployment.
- `requirements.txt` now includes FastAPI/Uvicorn/Pydantic despite an older Phase 7 audit sentence saying they were absent at that earlier time; the historical report is not rewritten.

## Hosting evidence and risk

Cloudflare Pages natively matches Vite's build/output and SPA needs. Render natively runs Python and supports Git deploys, HTTPS, logs, health checks and rollback. Immutable artifacts need no persistent disk. Render's documented free service is 0.1 CPU/512 MB, sleeps after 15 idle minutes and can take roughly one minute to wake; it is acceptable for trial/demo tolerance, not an always-on promise. Current limits/pricing were verified only as of the audit date and must be rechecked before resource creation.

## Readiness conclusion

The application architecture is suitable for a small single-process portfolio deployment, but the repository is not deployable from a clean clone today. Step 2 must package artifacts, lock runtimes/dependencies, add body/rate protections and production-safe configuration, verify memory, and establish CI. No model or API-contract redesign is needed.

## Step 1 verification

- Backend: 213 tests passed; three existing Starlette/httpx/AnyIO/loky deprecation/platform warnings, no failures.
- Frontend: 21 tests passed across four files; Recharts emitted only the known zero-size jsdom notices.
- Strict TypeScript typecheck: passed.
- Vite 7.3.6 production build: passed with route-level chunks and no size warning.
- `npm audit --audit-level=high`: exit 0; zero high/critical and two moderate development-only Vitest mocker findings.
- `pip check`: no broken requirements. This is compatibility verification, not a Python vulnerability scan.
- Documentation-only diff: no application, model, artifact, dependency or test file changed.
