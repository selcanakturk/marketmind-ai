# MarketMind deployment and production-readiness architecture

Status: **frozen in Phase 9 Step 1; no deployment implemented**  
Profile: public portfolio demo, not multi-tenant commercial SaaS

## Deployment goal and environments

MarketMind should make all six frozen engines publicly demonstrable at low operational cost, with HTTPS, reproducible builds, bounded abuse, safe configuration, useful logs, and simple rollback. It must not introduce persistence, distributed infrastructure, or authentication theatre.

| Profile | Contract |
|---|---|
| Local development | Vite on `localhost:5173`, FastAPI on `localhost:8000`, local ignored artifacts, explicit localhost CORS, reload allowed only here |
| Portfolio/public demo | Cloudflare Pages frontend plus one Render FastAPI web service, public stateless inference, bounded requests/rates/concurrency, managed HTTPS, provider logs |
| Future commercial | Real identity, authorization, tenants, governed persistent data, audit trails, stronger WAF/quotas, SLOs/on-call, compliance, backups/DR, privacy controls and independent security review |

## Selected architecture

```text
Browser
  -> HTTPS Cloudflare Pages (static frontend/dist, SPA fallback)
  -> HTTPS Render web service (FastAPI, one Uvicorn process)
  -> six read-only bundles packaged with the deployed source
```

Cloudflare Pages is the primary frontend because it supports Git-connected static deployment, the Vite `npm run build`/`dist` contract, automatic SPA fallback when no top-level `404.html` exists, CDN caching and deployment rollback. Render is the primary backend because its native Python runtime supports Git deployment, environment configuration, logs, managed TLS, HTTP health checks, rollback, and an ephemeral filesystem that is sufficient for immutable bundled artifacts.

The fallback is Vercel static Vite hosting plus Railway for the same single-process backend contract. Vercel needs an explicit SPA rewrite. The fallback should be evaluated only if the primary providers fail a real build or cost/availability review; do not maintain two live stacks.

Official platform facts were checked on 2026-09-27. Cloudflare Pages documents 500 free-plan deploys/month and built-in SPA routing. Render documents a free 0.1 CPU/512 MB service, 750 workspace hours/month, spin-down after 15 idle minutes, roughly one-minute wake-up, ephemeral filesystems, managed TLS, logs and limited free rollback. Render also offers 512 MB paid compute. Pricing and plan limits can change and must be rechecked at deployment approval; no monthly cost is frozen here.

Sources: [Cloudflare Pages](https://developers.cloudflare.com/pages/), [Pages build configuration](https://developers.cloudflare.com/pages/configuration/build-configuration/), [Pages SPA behavior](https://developers.cloudflare.com/pages/configuration/serving-pages/), [Render free services](https://render.com/docs/free), [Render compute plans](https://render.com/docs/compute-plans), [Render health checks](https://render.com/docs/health-checks), [Render Python versions](https://render.com/docs/python-version).

## Frontend hosting contract

- Root directory: `frontend`.
- Package manager: npm; `package-lock.json` is mandatory and CI/deploy uses `npm ci`.
- Target runtime: Node 24, recorded with `.nvmrc` and `package.json.engines` in Step 2.
- Build: `npm run build`; output: `frontend/dist`.
- Production public configuration: `VITE_MARKETMIND_API_BASE_URL=https://<backend-host>` with no trailing slash requirement. Vite embeds it at build time; it is not a secret.
- Local mapping: `http://localhost:5173` -> `http://localhost:8000`.
- Deployment mapping: `https://<frontend-host>` -> `https://<backend-host>`.
- Client-side routes require root `index.html` fallback. Cloudflare Pages supplies this for SPAs without a top-level `404.html`; fallback hosts need an explicit rewrite.
- Do not hardcode deployed URLs in source. Preview builds must target an intentionally selected backend, not silently production.
- Production source maps are disabled by the current Vite default and remain disabled for the public demo. If later enabled for error monitoring, upload privately and do not publish them.
- Hashed JS/CSS assets may be cached immutably; `index.html` should revalidate. HTTPS is mandatory.
- The frontend displays sanitized API errors and request IDs only. No backend secret or artifact path may use a `VITE_` variable.

## Backend serving contract

- Python: pin the exact Step 2 runtime to `3.13.x`, initially matching the artifact environment (`3.13.2`) if the provider still supports that patch; record it in `.python-version` and CI. Do not accept a moving provider default.
- Dependencies: produce a deployment-focused, fully resolved lock/constraints strategy in Step 2. The current broad `requirements.txt` is not reproducible enough.
- Install: deterministic locked install, then verify artifact checksums and import the app. Training and notebooks must not run.
- Start: `PYTHONPATH=src uvicorn marketmind.api.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1`; never `--reload`.
- Use Uvicorn directly. Gunicorn adds no demonstrated benefit for this one-process demo.
- One process avoids duplicating loaded models. The existing load-once registry eagerly loads all six bundles and isolates failures per module.
- Initial public setting: `MARKETMIND_MAX_CONCURRENT_REQUESTS=2`, subject to Step 2 load testing. The local default remains four.
- Frontend inference timeout is 60 seconds and status timeout is 10 seconds. Platform/startup health must allow the observed roughly eight-second artifact load plus margin.
- Logs go to stdout/stderr. The runtime filesystem is read-only in policy and ephemeral in fact; no persistence is expected.

## Artifact strategy

The six binary bundles are the runtime source of truth. They currently total **29,505,194 bytes (28.14 MiB)**:

| Module | File | Bytes | SHA-256 |
|---|---|---:|---|
| Forecast | `models/forecasting/model.joblib` | 535,711 | `1a07b04afb0ed49466bc85f772074c134b68f9313b2672784ce86c1619cf429f` |
| Segmentation | `models/segmentation/model.joblib` | 3,492 | `a368119e9e5fc4aad8d700f7203d1e53840517595a671c408e464beb1a0a0b90` |
| Return risk | `models/return_risk/model.joblib` | 11,248,815 | `00d5cc9cd449adc052257b8cc5b1dcfa2de746bf0ec8ff0e88f3ee34a753f54e` |
| Recommendations | `models/recommendations/model.joblib` | 14,344,306 | `623b1b048c2c4660cf602d9226c6c6870343491c3a55f7af0788166e323396ba` |
| Anomalies | `models/anomalies/model.joblib` | 3,369,626 | `b1bd5cc855346ef5f5075bf979768fd4d2593ab1cd85eb4977a942cc84e680e1` |
| Inventory | `models/inventory/inventory_bundle.joblib` | 3,244 | `dfcc8228b603aed389bd86dc8ad3a3bba2bc497d2823147810b58c98498fc565` |

They exist locally but are all Git-ignored. A clean Git deployment therefore has zero runnable modules: this is the primary Step 2 blocker.

Step 2 should deliberately unignore and commit these six immutable binaries plus a reviewed checksum manifest. Each is below GitHub's enforced 100 MiB object limit and the one-time 28.14 MiB payload is practical for this portfolio repository. GitHub recommends LFS for binaries and objects over its smaller recommended threshold, but LFS introduces another deployment fetch dependency; it is not necessary for these frozen, infrequently changing bundles. Object storage/release downloads are also unnecessary. If repository policy rejects ordinary Git binaries, use Git LFS as the single fallback—not ad hoc runtime downloads.

Build/startup must verify SHA-256 before deserialization. Metadata and bundle versions must continue matching. A missing/corrupt bundle marks only that module unavailable, while checksum failure must fail pre-deploy verification. Never deserialize user-supplied artifacts.

## Compute and memory

The earlier local registry audit measured about 8.02 seconds to load all bundles, ~41.35 MB traced current allocation and ~69.13 MB traced peak allocation. These are Python allocation observations, not total resident memory. Return risk and recommendations are the largest bundles; recommendation validation dominates startup. Eager loading and one process remain appropriate.

Use **512 MB as the minimum candidate class**, not a guaranteed requirement. Step 2 must measure process RSS at cold start and representative maximum-contract requests, including the 50,000-row return-risk path, on Linux. Advance to a larger class if peak RSS lacks at least ~30% headroom or latency is unacceptable. Free Render's 0.1 CPU/512 MB is suitable only for trial/portfolio tolerance of cold starts; paid 512 MB is the initial always-on candidate. Concurrency remains bounded and horizontal scaling is deferred.

## Public-demo security model

### Must have before public demo

- 16 MiB raw request-body ceiling at the application or trusted proxy, validated against every documented maximum request; reject early with 413.
- Existing Pydantic strict validation and logical row/item limits retained and moved as close to schema parsing as practical.
- Per-client application rate limiting in the single process, using a small maintained library such as `slowapi`; correctly resolve the provider's trusted forwarding header and never trust arbitrary forwarded chains.
- Proposed starting buckets, finalized by Step 2 load tests: operations GETs 60/minute/IP; segmentation/recommendation/inventory 10/minute/IP; forecast/anomaly 6/minute/IP; 50k-row return risk 3/minute/IP; global short burst ceiling. These distinguish endpoint cost and bound casual scraping, not commercial quotas.
- Existing process-wide concurrency limiter set to two for public deployment; platform connection/request protections retained.
- Explicit production CORS origin, HTTPS, sanitized errors, no debug mode, payload-free logs, exact dependency/runtime pins and artifact checksums.
- Provider spend/usage alerts where available. Rate limiting is defense-in-depth, not DDoS immunity.

### Should have

- Security headers on the static frontend: CSP restricted to self plus the configured API `connect-src`, `X-Content-Type-Options: nosniff`, strict referrer policy, frame denial, and HSTS supplied only at the HTTPS edge.
- Minimal dependency audit in CI; fail high/critical runtime findings, report moderate development findings with an explicit exception.
- Bot/WAF controls only if abuse appears. Optional uptime checks for `/health` and a separate readiness monitor.
- Redact query strings and keep finite provider log retention.

### Future commercial requirement

Authentication, authorization, per-tenant quotas and isolation, database-backed distributed limiting, audit events, data retention/deletion policy, encryption governance, secrets rotation, vulnerability management, penetration testing, SLO/on-call/incident response, regional/privacy analysis and model extraction controls.

CORS is browser policy, not authentication. The portfolio API remains publicly callable.

## Authentication decision

Choose **Option A: public stateless demo**. There are no accounts, saved data, tenants or private records, so real authentication adds operational risk without protecting a meaningful user boundary. A simple shared gate is easy to leak and creates false assurance. Rate limits, bounds and non-persistent demo inputs are proportionate. Revisit real identity only with persistence or private user data.

## CORS and configuration inventory

Production uses exactly the deployed frontend origin in `MARKETMIND_CORS_ORIGINS`; preview origins are explicitly enumerated or use a dedicated non-production backend. Credentials remain enabled only because the current middleware contract does so; Step 2 should set `allow_credentials=False` because the chosen public demo uses no cookies/auth. Methods remain `GET, POST`; headers remain `Content-Type, X-Request-ID`. Wildcards are prohibited.

| Variable | Class | Production contract |
|---|---|---|
| `VITE_MARKETMIND_API_BASE_URL` | Public frontend config | HTTPS backend origin; build-time public value |
| `MARKETMIND_ENV` | Backend config | `production` |
| `MARKETMIND_ARTIFACT_ROOT` | Backend config | deployment working root, normally `.` |
| `MARKETMIND_CORS_ORIGINS` | Backend config | exact HTTPS frontend origin(s), comma-separated |
| `MARKETMIND_LOG_LEVEL` | Backend config | `INFO` |
| `MARKETMIND_MAX_CONCURRENT_REQUESTS` | Backend config | initial `2` |
| `MARKETMIND_MAX_BODY_BYTES` | Backend config, Step 2 | initial 16 MiB after contract-size verification |
| rate-limit variables | Backend config, Step 2 | explicit class defaults; non-secret |
| `PORT` | Provider runtime | dynamic listener port; local fallback 8000 |
| `PYTHON_VERSION` | Build config | exact supported 3.13 patch |

No application secret is needed. Provider deploy tokens, if CI ever requires them, live only in provider/GitHub environment secret stores. `.env` and `.env.*` remain ignored while root and frontend `.env.example` files contain safe placeholders only. Never place secrets in a `VITE_` variable.

## Logging and observability

Keep provider logs plus the existing access log. Step 2 should configure consistent single-line JSON or key-value stdout logs containing timestamp, level, environment, request ID, method, normalized route template, status, total latency, safe module and error code. Add startup events for each module with readiness/version/load duration, never absolute paths.

Never log bodies, transaction rows, visitor histories, IDs from payloads, secrets, environment dumps or client-facing stack traces. Server exceptions may include stack traces in restricted provider logs, correlated by request ID. Sentry is deferred until provider logs prove insufficient; it is not necessary for the initial demo.

## Health and readiness

Render's restart/deployment health check uses `/health`: it proves the process can serve and preserves intentional partial readiness. `/ready` reports aggregate and per-module state and may return HTTP 200 with `status=degraded`; it is monitored separately.

Promotion requires `/health` 200, `/ready` reporting all six true, `/api/v1/models` reporting all six ready, and one bounded smoke per inference route. After deployment, a single module failure produces degraded readiness and 503 only for that module; it should not create a restart loop for unaffected modules.

## OpenAPI and public URLs

Keep `/docs`, `/redoc` and `/openapi.json` public. Typed API documentation is valuable portfolio evidence and hiding it would not secure a public API. It must disclose no paths/secrets and remains subject to general GET rate limits.

Use provider HTTPS hostnames initially:

- frontend: `https://<frontend-host>`
- backend: `https://<backend-host>`

A custom domain is optional polish, not a blocker. Separate origins preserve independent static/API deployments and require the explicit CORS mapping above.

## CI/CD and promotion

Step 2 creates one GitHub Actions CI workflow with two parallel jobs on pull requests and `main`:

- Backend: exact Python setup with pip cache, deterministic install, `pip check`, checksum verification, import/compile smoke, and all 213+ tests.
- Frontend: Node 24 with npm cache, `npm ci`, tests, typecheck, build, and `npm audit --audit-level=high`. High/critical findings block; the known moderate test-only issue must be removed by the narrow Vitest migration or documented until then.

Do not deploy directly from untested commits. Provider Git integration may auto-build previews, but production deploys should occur only from green `main` and initially require a manual provider/GitHub-environment promotion. After stable operation this may become automatic-after-green. Allow one production deployment at a time.

Rollback uses provider-native immutable deployment history: roll back frontend independently; roll back backend source and its matching artifact manifest as one unit. Build/test/checksum failure blocks deployment. Backend startup or all-module readiness failure blocks promotion. A later single-module failure may serve degraded. Contract incompatibility requires rolling back the newer side; backend V1 remains backward compatible throughout Phase 9.

## Docker decision

Choose **C: Docker unnecessary for initial deployment**. Render natively supports Python; immutable artifacts fit the source bundle; a Dockerfile would add build surface without solving a current requirement. Reconsider only if native wheels/runtime reproducibility fails. If needed, Step 2 fallback is a pinned slim Python 3.13 image, locked installs, non-root user, source/artifact copy with checksum verification, dynamic `PORT` entrypoint and no training/data files. Kubernetes is explicitly excluded.

## Demo data and privacy

Frontend fixtures contain small illustrative/synthetic inputs only: no private user data, raw datasets or stored model outcomes. Inventory business state remains visibly synthetic. Complete Journey, M5 and RetailRocket identities stay separate. Requests and results are stateless and not logged. Public users must be warned not to submit personal/confidential data. Do not bundle consumed lockbox outcomes as fresh evidence.

## Production-readiness checklist

### Before Step 2

- [x] Freeze Cloudflare Pages + Render and one fallback.
- [x] Identify ignored binaries as the deployment blocker.
- [x] Freeze public/no-auth demo profile.
- [ ] Approve ordinary-Git artifact packaging and 512 MB starting-class assumption.

### Step 2 implementation

- [ ] Package six frozen bundles and checksum manifest; verify before load.
- [ ] Pin Python 3.13 runtime and resolved dependencies; add `.python-version`.
- [ ] Move frontend to Node 24/Vitest 4.1.11+ narrowly; add `.nvmrc` and engines.
- [ ] Add production start/config examples, dynamic `PORT`, no reload.
- [ ] Add 16 MiB body limit, per-IP cost-class rates, production concurrency two and trusted-proxy handling.
- [ ] Disable CORS credentials; validate production origins and unsafe configurations.
- [ ] Add safe structured startup/access logging and security headers.
- [ ] Add root `.env.example`, refine frontend example, and add focused config/security tests.
- [ ] Add CI only; no deployment workflow or cloud resource creation until approval.

### Pre-deploy QA

- [ ] Green backend/frontend suites and audits on target runtimes.
- [ ] Measure cold-start/load time, RSS and representative/max-contract latency on Linux.
- [ ] Clean-clone build proves all artifacts available and checksums match.
- [ ] Test 413/422/429/503, CORS allow/deny, redaction, partial readiness and graceful shutdown.
- [ ] Real-browser desktop/tablet/mobile sign-off and HTTPS mixed-content check.
- [ ] Recheck official provider pricing/limits and set spend/usage controls.

### Deployment

- [ ] Create provider projects only after explicit approval.
- [ ] Configure production environment values and exact CORS/API origins.
- [ ] Deploy backend, verify all-module readiness/smoke, then build frontend against its URL.
- [ ] Record deployment commit, artifact manifest, URLs and rollback points.

### Post-deploy verification

- [ ] Verify HTTPS, security headers, docs, all eight frontend routes and all six workflows.
- [ ] Verify cold-start UX, rate/body limits, logs/request IDs and no payload leakage.
- [ ] Confirm rollback procedure and monitor error/latency/readiness for an initial observation window.

### Future commercial hardening

- [ ] Identity/authorization/tenancy, persistent governed data and distributed quotas.
- [ ] Formal threat modeling, privacy/legal review, SLO/on-call/DR and independent security testing.
- [ ] Autoscaling/load testing, managed observability and artifact registry/signing if operating scale warrants them.

## Exact Step 2 plan

Step 2 is limited to repository production-readiness implementation: reproducible runtime/dependency pins, reviewed artifact packaging and integrity verification, request-body/rate/concurrency controls, production-safe CORS/config/logging/headers, narrow Node/Vitest remediation, safe environment examples, CI checks, focused tests, clean-clone/local production smoke and updated runbooks. It must stop before cloud project creation or deployment.

## Step 2 implementation status

The plan is implemented in repository configuration and code. Six frozen binaries are narrowly packaged with SHA-256 verification; Python 3.13.2 and Node 24 policies are recorded; production configuration rejects unsafe origins; request bodies, rates, inference concurrency and queueing are bounded; CORS credentials are off; safe security headers and JSON production logs are active; CI and production verification scripts are present. No cloud deployment occurred.

Maximum-contract payloads remain below the 16 MiB ceiling, with return risk largest at 9,216,819 bytes. All six maximum-contract requests completed locally. The non-Linux harness peaked at 497.16 MiB, so the 512 MB candidate is no longer recommended for initial deployment; use the next practical 2 GB Render class and measure real Linux RSS before any downgrade. Node 24 was unavailable locally, so the configured policy and Vitest 4 migration require CI/Step 3 verification.
