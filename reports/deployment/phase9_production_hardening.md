# Phase 9 Step 2 production hardening

## Outcome

The repository is prepared for clean-checkout production-mode verification without raw datasets. No cloud resource or deployment was created. Six original frozen binaries are now narrowly unignored and paired with a machine-readable SHA-256 manifest; no artifact was rebuilt.

## Implemented controls

- Python 3.13.2 pin and exact top-level runtime/development dependency sets.
- Node 24/npm 11 policy. Node 24 was unavailable locally, so Vitest remains 3.2.7 pending CI/Step 3 verification; no unsafe downgrade was used.
- Production frontend builds require an explicit non-local API origin.
- Production settings reject wildcard, missing/non-HTTPS or malformed CORS origins and invalid protection values.
- Streaming-safe 16 MiB body ceiling with canonical 413.
- In-process fixed-window public-demo limits by endpoint cost class with canonical 429 and `Retry-After`; development is not rate-limited.
- Inference-only capacity two in production with a finite 0.25-second queue wait; accepted execution is not incorrectly cancelled by the queue timeout. Operational GETs bypass inference capacity.
- CORS credentials disabled; exact origins, GET/POST and required headers only.
- `nosniff`, no-referrer, frame denial/frame-ancestors headers; HSTS only in production. Swagger/ReDoc remain public.
- Production JSON access/startup logs include safe route/module/error fields and no bodies or paths.
- CI performs checksum/build/audit/test/smoke gates and never deploys.

## Maximum-contract evidence

Compact serialized request sizes:

| Endpoint | Bytes | Result | Local latency |
|---|---:|---:|---:|
| Forecast (70 series, 3,920 history) | 428,895 | 200 | 83.268 ms |
| Segmentation (2,500 rows) | 591,445 | 200 | 35.491 ms |
| Return risk (50,000 transactions) | 9,216,819 | 200 | 531.182 ms |
| Recommendations (500 history IDs) | 1,978 | 200 | 21.454 ms |
| Anomalies (70 aligned rows) | 12,511 | 200 | 15.385 ms |
| Inventory (70 decisions, 1,960 forecasts) | 214,776 | 200 | 90.719 ms |

Inputs were synthetic contract-valid operational data. These timings are local observations, not SLAs or model-quality measurements. The largest request occupies about 55% of the 16 MiB ceiling.

## Resource evidence

Environment: macOS 14.6.1 arm64, Python 3.13.2—not representative Render Linux. Production smoke verified artifacts in 0.012 seconds, loaded the registry in 0.688 seconds and observed 351.22 MiB peak RSS. The conservative maximum-contract harness, which also holds generated fixtures, peaked at 497.16 MiB after the return-risk case.

Therefore 512 MB is **marginal/unsafe as an initial choice**, not proven sufficient. No Linux runtime was available. Step 3 should begin on Render's next practical 2 GB class, observe real Linux RSS and only consider lowering memory after evidence. Models were not altered to fit memory.

## Artifact inventory

The manifest verifies all six files and totals 29,505,194 bytes. Largest file is recommendations at 14,344,306 bytes; no file approaches GitHub's 100 MiB object ceiling. Registry verification failures are isolated per module and never trigger training.

## Verification limitations

Node 24 is configured but could not be executed locally; local Node is 23.9.0. Consequently Vitest 4.1.11+ was not installed. CI is the first required Node 24 verification environment. Linux/Render resource behavior and provider proxy identity must be verified in Step 3.

## Final verification

- Artifact verifier: six passed.
- Python compile/import and `pip check`: passed.
- Python tests: 223 passed (213 existing plus 10 focused hardening cases), with three existing deprecation/platform warnings.
- Production-mode API smoke: health, all-six readiness, models and six inference routes passed.
- Frontend tests: 21 passed; only known Recharts zero-size jsdom notices.
- Strict TypeScript typecheck: passed.
- Production build with explicit non-local API origin: passed.
- npm audit high-severity gate: exit 0; zero high/critical and two moderate development-only Vitest/`@vitest/mocker` findings remain.
- Intended-clean-checkout copy: passed artifact verification, all API smoke routes, `npm ci` and production build. It used the existing Python environment rather than downloading a fresh wheel set; CI owns the clean Python install proof.
