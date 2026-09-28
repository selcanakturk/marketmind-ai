# MarketMind deployment preparation runbook

This runbook prepares and verifies MarketMind without creating cloud resources. Production deployment remains Phase 9 Step 3.

## Local production-like backend

Use Python 3.13.2 and install the pinned runtime requirements:

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
PYTHONPATH=src .venv/bin/python -m marketmind.api.artifacts
MARKETMIND_ENV=production \
MARKETMIND_CORS_ORIGINS=https://frontend.example \
MARKETMIND_MAX_CONCURRENT_REQUESTS=2 \
PYTHONPATH=src .venv/bin/uvicorn marketmind.api.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 1
```

Never use `--reload` in production. The placeholder origin must be replaced with the actual HTTPS frontend origin in Step 3.

## Local production-like frontend

Use Node 24 and npm 11:

```bash
cd frontend
npm ci
VITE_MARKETMIND_API_BASE_URL=https://api.example.invalid npm run build
```

For local interactive development, copy `frontend/.env.example` to an ignored `.env.local` and use `http://localhost:8000`. Production builds reject a missing or localhost API base. Every `VITE_` value is public.

## Artifact verification

Run:

```bash
PYTHONPATH=src .venv/bin/python -m marketmind.api.artifacts
```

Expected: `verified 6 immutable production artifacts`. The manifest is `models/artifact_manifest.json`. Verification rejects missing files, size/hash mismatches and unsafe paths before deserialization. It never trains or rebuilds.

## Environment variables

Use `.env.example` as the safe inventory. Production requires `MARKETMIND_ENV=production`, an exact HTTPS `MARKETMIND_CORS_ORIGINS`, project-relative `MARKETMIND_ARTIFACT_ROOT`, concurrency two, 16 MiB body ceiling and positive rate/queue settings. `PORT` is provider-controlled. Real `.env*` files remain ignored except examples.

## CI

`.github/workflows/ci.yml` runs parallel backend and frontend jobs without deployment credentials. Backend verifies checksums, dependencies, compilation/import, tests and production smoke on Python 3.13.2. Frontend runs Node 24, `npm ci`, high-severity audit, tests, typecheck and production build.

## Health and readiness

- `/health`: cheap liveness; expected 200 `{"status":"ok"}`.
- `/ready`: cached module readiness; initial promotion requires `status=ready` and all six booleans true.
- `/api/v1/models`: six safe module records; no filesystem paths.

Hosting liveness uses `/health`. A single failed checksum produces degraded `/ready` and only that module returns 503; unaffected modules continue serving.

## Common startup failures

- `invalid CORS origin`: replace wildcard, HTTP production origin, path/query or missing origin with the exact HTTPS frontend origin.
- `ARTIFACT_MANIFEST_INVALID`: restore the reviewed manifest from the same commit as the binaries.
- module unavailable: inspect safe startup `reason_code`; do not rebuild an artifact.
- incompatible deserialization/import: confirm Python 3.13.2 and pinned requirements, then roll back the source/artifact unit.
- frontend build rejects API URL: set a non-local explicit `VITE_MARKETMIND_API_BASE_URL`.

## Checksum failure

Stop promotion. Confirm the binary and manifest came from the same reviewed commit. Restore/rollback them together. Never update a hash merely to accept an unexplained binary.

## Degraded module

`/health` remains live. `/ready` reports degraded and the affected endpoint returns canonical `MODULE_UNAVAILABLE`. For initial deployment, do not promote. After deployment, unaffected workflows may remain available while the last known-good backend is restored.

## Rate and body limits

Production rate excess returns 429 `RATE_LIMITED`, a request ID and `Retry-After`. The app identifies the socket peer after server-level trusted-proxy normalization and never parses arbitrary `X-Forwarded-For`. Validate Render's proxy-header behavior in Step 3.

Bodies above 16,777,216 bytes return 413 `REQUEST_TOO_LARGE` with the canonical envelope and request ID before inference. The largest constructed maximum contract is return risk at 9,216,819 bytes.

## Verification commands

```bash
PYTHONPATH=src .venv/bin/python scripts/production_verify.py
PYTHONPATH=src .venv/bin/python scripts/maximum_contract_verify.py
PYTHONPATH=src .venv/bin/pytest -q
cd frontend
npm test -- --reporter=dot
npm run typecheck
VITE_MARKETMIND_API_BASE_URL=https://api.example.invalid npm run build
```

## Rollback principle

Frontend deployments roll back independently. Backend source, requirements, artifact manifest and all six binaries are one atomic release unit. Build/checksum/test failure blocks deployment; all-module readiness failure blocks initial promotion.

## Step 3 checklist

- Recheck provider limits and select Render 2 GB initially; 512 MB is not supported by current conservative memory evidence.
- Create one Render native-Python service and one Cloudflare Pages project only after approval.
- Configure exact production environment values; add no secrets to Vite.
- Validate Render's effective Python patch and trusted proxy/client IP behavior.
- Verify checksums and all-six readiness before exposing the frontend.
- Configure Cloudflare SPA fallback/static headers and production API URL.
- Run HTTPS, CORS, 413, 429, degraded readiness, docs, eight-route browser and six-workflow smoke checks.
- Record commit, URLs and rollback identifiers; observe memory, latency and errors before considering a smaller compute class.

