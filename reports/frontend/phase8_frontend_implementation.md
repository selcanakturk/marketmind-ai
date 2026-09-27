# Phase 8 Step 2 frontend implementation

## Outcome

A working Vite/React/TypeScript dashboard now implements the eight frozen frontend routes against all nine authentic FastAPI endpoints. The frontend is isolated under `frontend/`; no Python API or production-engine code changed.

## Implemented product surface

- responsive application shell with desktop sidebar, tablet rail, mobile focus-managed drawer, skip link, active routes, and live readiness indicator;
- Overview driven by readiness/model metadata with six capability cards and explicit dataset boundaries;
- System / Models with liveness, aggregate readiness, per-module metadata, safe reasons, and refresh;
- Forecasting with 56-day/28-day demo input, JSON editors, submitted-history plus prediction chart, table, and warning preservation;
- Segmentation with snapshot and prepared nine-feature rows, response-subset counts, assignments, and distance semantics;
- Return Risk with coordinated transaction/product input, capacity, response aggregates, eligibility/ranking table, and uncalibrated-score language;
- Recommendations with compact distinct history editor, personalized/fallback state, zero-row handling, and seen/novel labels;
- Anomalies with stateless-preview messaging, aligned inputs, optional IF diagnostic, fixed ±3 chart references, review queue, and full table;
- Inventory with explicit scenario/forecast inputs, recommendation summary, returned-value equations, constraint path, full decision table, and robust-normal warnings.

## API and state architecture

`src/api/client.ts` centralizes the environment base URL, JSON requests, 10-second operational and 60-second inference timeouts, AbortController propagation, safe non-JSON/network handling, canonical error envelopes, and request IDs. Page code uses named adapters only. TanStack Query caches operational GETs and manages inference mutations without automatic retries. Routes are lazy-loaded for smaller initial delivery.

## UX, accessibility, and responsiveness

CSS variables implement the frozen neutral surface hierarchy, 4px-derived spacing, semantic colors, moderate radii, table density, focus indicators, and reduced-motion rule. Shared components standardize headings, cards, status, persistent warnings, errors with request IDs, skeletons, empty states, metrics, tables, and chart summaries.

Desktop uses a 256px sidebar, tablet an icon rail, and mobile a drawer with Escape/return-focus behavior. Forms/grids collapse to one column and tables retain fields inside labeled horizontal regions. Charts have textual summaries and their canonical data is also tabular.

## Demo fixtures

All frontend fixtures populate requests only. Because reviewed non-lockbox extraction scripts were not added in this step, potentially authentic-looking examples are conservatively labeled illustrative/synthetic:

- Forecasting: M5-shaped dates/IDs with synthetic sales and calendar context.
- Segmentation: synthetic prepared Complete Journey-shaped features.
- Return risk: synthetic Complete Journey-shaped transaction/product rows.
- Recommendations: synthetic RetailRocket-shaped IDs; fallback is possible.
- Anomalies: synthetic M5-shaped actual/expected rows.
- Inventory: explicitly synthetic business inventory state and synthetic aligned forecast.

No outputs or quality metrics are bundled. No consumed lockbox was touched.

## Verification

- TypeScript strict type-check: passed.
- Vitest/MSW/Testing Library/axe: 17 tests passed.
- Production build: passed with Vite route-level code splitting.
- Python repository: 213 tests passed.
- Browser servers: FastAPI and Vite both started successfully on localhost. Visual inspection could not be performed because this environment exposed no browser surface and computer-use permission was unavailable; no visual-QA claim is made.
- Dependency audit: patched React Router and Vite advisories; two moderate development-only Vitest mocker advisories remain because the fixed Vitest 4.1.11 requires Node 24 while this environment provides Node 23.9. They do not enter the production bundle. Recheck under Node 24 in Step 3.

The test environment emits only harmless zero-size Recharts notices under jsdom; browser layout supplies real dimensions.

## Scope deliberately deferred after Step 2

Step 2 deferred explicit Forecast → Inventory/Anomaly transfer pending a reviewed draft-transfer mechanism. Authentication, persistence, file uploads, product catalog enrichment, dark mode, deployment, and historical KPI integrations remained absent.

## Step 3 — transfer, polish, and final verification

A small `ForecastDraftContext` now holds one in-memory draft per destination. Forecast results expose two explicit actions. Inventory receives 28 forecast rows only, shows an import notice, leaves its business-input array empty, and requires review and manual submission. Anomalies receives 28 expected-sales rows and exactly date-matched request calendar context, shows an import notice, leaves actual sales empty, and likewise requires manual submission. Both drafts are editable and clearable; clearing does not substitute demo data.

No demo fixture was relabeled or replaced: all remain input-only and retain their exact illustrative/synthetic provenance, including the prominent synthetic inventory-state label. No backend, schema, model, artifact, or lockbox changed.

Final gates used Node 23.9.0 because Node 24 was not installed. Vitest remains 3.2.7. Strict type checking passed; 21 frontend tests passed; the Vite production build passed; and all 213 Python tests passed with three existing deprecation/platform warnings. The dependency audit passed the high-severity gate and reported two moderate development-only findings in Vitest/`@vitest/mocker`; the offered force fix is a breaking downgrade, so it was not applied.

FastAPI and Vite both ran locally. `/health`, `/ready`, and `/api/v1/models` were healthy/ready, all six modules reported ready, the frontend root and `/forecasting` returned HTTP 200, and the repository smoke client exercised all nine API routes using existing production artifacts. Browser/computer-use permission was unavailable, so no rendered viewport or route visual inspection is claimed. Static responsive review plus DOM and axe coverage found no new transfer-specific issue; real desktop/tablet/mobile visual sign-off remains a pre-deployment limitation.
