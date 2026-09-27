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

The app has no global state library. TanStack Query owns server-request lifecycle; page-local React state owns forms/results. Cross-module automatic orchestration is deliberately absent.

## Demo input limitations

The bundled examples are small schema-shaped illustrative inputs. Forecast sales, prepared customer features, return-risk transactions, recommendation IDs, and anomaly rows are explicitly labeled synthetic rather than claimed authentic records. Inventory state is prominently labeled **SYNTHETIC BUSINESS INVENTORY STATE** because M5 contains no inventory balances. The API generates all displayed model outputs live; none are hardcoded as authentic outcomes.

## Current limitations

- no authentication, persistence, saved scenarios, uploads, or deployment;
- JSON editors favor truthful contract visibility over spreadsheet-scale editing;
- recommendation V1 exposes item IDs, not catalog titles or imagery;
- direct Forecast → Inventory/Anomaly transfer is deferred to avoid hidden orchestration/global state;
- no business KPI history exists in V1;
- light theme only.
- the Node 23-compatible Vitest line retains a moderate development-only mocker advisory; move to Vitest 4.1.11+ when the project runtime moves to Node 24.
