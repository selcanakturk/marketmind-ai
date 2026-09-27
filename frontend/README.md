# MarketMind frontend

React/TypeScript dashboard for the existing MarketMind FastAPI V1. The client presents explicit inference requests and authentic API responses; it contains no model logic or stored model outcomes.

## Local development

From the repository root, start the API:

```bash
PYTHONPATH=src .venv/bin/uvicorn marketmind.api.main:app --reload
```

In another terminal:

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open `http://localhost:5173`. `VITE_MARKETMIND_API_BASE_URL` defaults centrally to `http://localhost:8000`; set it in `.env.local` when the API lives elsewhere. Vite variables are public browser configuration—never put secrets in them.

## Quality commands

```bash
npm run typecheck
npm test
npm run build
```

The production output is written to `frontend/dist/`. Deployment is not part of Phase 8 Step 2.

## Architecture

- `src/app`: query provider and lazy route tree
- `src/api`: base configuration, typed client, normalized errors, query/mutation hooks
- `src/components`: shared accessible UI and JSON editor
- `src/features`: Overview, Forecasting, Customers, Recommendations, Anomalies, Inventory, and System pages
- `src/layouts`: responsive application shell/navigation
- `src/demo`: compact input-only fixtures and explicit provenance labels
- `src/styles`: design tokens and responsive implementation
- `src/test`: MSW handlers, test setup, client, route, workflow, and accessibility tests
- `src/types`: TypeScript mirrors of authoritative Pydantic contracts

The app has no global state library. TanStack Query owns server-request lifecycle; page-local React state owns forms/results. A small in-memory React context owns one explicit, reviewable Forecast draft per supported destination. Cross-module automatic orchestration remains deliberately absent.

## Demo input limitations

The bundled examples are small schema-shaped illustrative inputs. Forecast sales, prepared customer features, return-risk transactions, recommendation IDs, and anomaly rows are explicitly labeled synthetic rather than claimed authentic records. Inventory state is prominently labeled **SYNTHETIC BUSINESS INVENTORY STATE** because M5 contains no inventory balances. The API generates all displayed model outputs live; none are hardcoded as authentic outcomes.

## Current limitations

- no authentication, persistence, saved scenarios, uploads, or deployment;
- JSON editors favor truthful contract visibility over spreadsheet-scale editing;
- recommendation V1 exposes item IDs, not catalog titles or imagery;
- Forecast drafts are intentionally in-memory only and disappear on refresh;
- no business KPI history exists in V1;
- light theme only.
- the Node 23-compatible Vitest line retains a moderate development-only mocker advisory; move to Vitest 4.1.11+ when the project runtime moves to Node 24.

## Phase 8 Step 3 verification

Forecasting now exposes explicit actions to populate, but never submit, an Inventory forecast draft or an Anomaly expected-sales draft. Inventory assumptions and anomaly actual sales remain empty and user-supplied; imported drafts are editable and clearable. The bundled demos and provenance labels are unchanged because no safer authentic-derived replacement was established without additional source-data review.

Strict type checking, the production build, 21 Vitest/MSW/Testing Library tests (including axe transfer coverage), and all 213 Python tests pass. The authentic local API and Vite server started successfully; health, readiness, six model statuses, and all inference routes were smoke-tested against existing artifacts. Node 23.9.0 was used because Node 24 was unavailable. `npm audit --audit-level=high` passes its high-severity gate but reports two moderate, development-only Vitest mocker findings.

No real-browser viewport inspection is claimed: the available computer-use integration had no usable browser permission. Static responsive review and automated DOM/accessibility checks found no transfer-specific clipping or overflow defect. Desktop (>=1200px), tablet (768–1199px), and mobile (<768px) behavior still requires final visual sign-off on an enabled browser before deployment.
