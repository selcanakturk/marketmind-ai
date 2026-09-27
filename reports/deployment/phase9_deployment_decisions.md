# Phase 9 deployment decisions

## Step 1 — architecture freeze (2026-09-27)

| Area | Frozen decision |
|---|---|
| Intended profile | Public stateless portfolio demo; local development and future commercial production are separate profiles |
| Frontend primary | Cloudflare Pages, Git-connected static Vite build |
| Backend primary | Render native Python web service |
| Fallback | Vercel frontend plus Railway backend; do not maintain both stacks |
| URLs | Separate provider HTTPS origins initially; custom domain optional |
| Frontend contract | root `frontend`; Node 24; `npm ci`; `npm run build`; output `dist`; build-time public API URL; SPA fallback |
| Backend runtime | exact Python 3.13 patch, deterministic locked dependencies, Uvicorn direct, dynamic `PORT`, no reload |
| Processes | one Uvicorn worker; eager load once; avoid duplicated model memory |
| Resource candidate | 512 MB minimum candidate, validated by Linux RSS/load tests; public concurrency initially two |
| Artifacts | package six frozen binaries with source and checksum manifest; ordinary Git preferred for this one-time 28.14 MiB set, LFS fallback, no object store |
| Integrity | SHA-256 pre-deploy/startup verification plus existing metadata/bundle version check |
| Filesystem | immutable deployment files only; no persistent disk/database |
| Authentication | none for initial public demo; no shared fake gate |
| Abuse protection | 16 MiB raw body ceiling, logical bounds, endpoint cost-class per-IP rate limits, concurrency limit, provider edge protection |
| CORS | exact frontend HTTPS origin; localhost only in development; GET/POST and required headers only; credentials off |
| Secrets | no app secret required; deploy credentials only in provider/GitHub stores; never in Vite variables |
| Logging | safe structured stdout access/startup logs with request ID; no payloads/IDs/secrets/absolute paths |
| Health | provider check `/health`; monitor `/ready`; all six ready required for initial promotion; later partial degradation may serve |
| API docs | `/docs`, `/redoc`, `/openapi.json` remain public and rate-limited |
| CI | two parallel GitHub jobs, one target Python and one Node 24; tests/typecheck/build/audits/checksums; no broad matrices |
| Promotion | green `main` plus initial manual production promotion; one deployment at a time |
| Rollback | provider-native immutable history; frontend independent; backend source and artifact manifest atomic |
| Docker | unnecessary for initial native Render deployment; pinned slim image only as a fallback |
| Observability | provider logs plus readiness/uptime checks; Sentry deferred |
| Demo privacy | small provenance-labeled illustrative/synthetic input; no raw/private data, payload logging or cross-dataset identity |

## Must resolve in Step 2

1. Clean checkouts lack every binary bundle because the artifacts are ignored.
2. Python installation is not reproducibly locked and runtime version is not repository-pinned.
3. Node is not repository-pinned and Vitest retains two moderate development-only findings.
4. Raw body size and per-client inference frequency are unbounded.
5. Production CORS safety, trusted proxy behavior, structured startup logs and security headers need explicit implementation/tests.
6. Actual Linux RSS and request-cost evidence is required before choosing free versus paid compute.

## Explicitly deferred

Cloud resource creation, deployment, custom DNS, Docker unless native deployment fails, authentication, authorization, accounts, tenancy, persistence, database, Redis/distributed limiting, queues/workers, autoscaling, Terraform, Kubernetes, Sentry, commercial compliance/SLO programs, model changes, training, artifact rebuilding and lockbox analysis.

Phase 9 Step 2 may begin only after this freeze is reviewed and approved.

