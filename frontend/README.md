# MarketMind frontend

React/TypeScript decision workspace for the MarketMind FastAPI V1. The client presents explicit inference requests and authentic API responses; it contains no model logic, persisted customer state, or hardcoded model outcomes.

## Local development

Use Node 24 and npm 11 as pinned by the repository. Start the API from the repository root:

```bash
PYTHONPATH=src .venv/bin/uvicorn marketmind.api.main:app --reload
```

In another terminal:

```bash
cd frontend
npm ci
cp .env.example .env.local
npm run dev
```

Open `http://localhost:5173`. `VITE_MARKETMIND_API_BASE_URL` is normalized centrally; the example local environment points it to `http://localhost:8000`. Vite variables are public browser configuration—never put secrets in them.

## Quality commands

```bash
npm audit --audit-level=high
npm test -- --reporter=dot
npm run typecheck
VITE_MARKETMIND_API_BASE_URL=https://api.example.invalid npm run build
```

The accepted portfolio checkpoint passes 5 Vitest/MSW/Testing Library files with 32 tests, including axe accessibility checks, strict TypeScript type checking, npm's high-severity audit gate, and the production Vite build under the repository's Node 24 CI policy. The output is written to `frontend/dist/` and is not tracked.

## Architecture

- `src/app`: query provider, route tree, and explicit in-memory Forecast draft transfers
- `src/api`: base configuration, typed client, normalized errors, and query/mutation hooks
- `src/components`: shared accessible UI and JSON editor
- `src/features`: Overview, Forecasting, Customers, Recommendations, Anomalies, Inventory, and System pages
- `src/layouts`: responsive application shell and navigation
- `src/demo`: deterministic input-only fixtures with explicit provenance labels
- `src/styles`: design tokens and responsive implementation
- `src/test`: MSW handlers, client, route, workflow, transfer, and accessibility tests
- `src/types`: TypeScript mirrors of the authoritative Pydantic contracts

TanStack Query owns server-request lifecycle; page-local React state owns forms and results. A small in-memory context holds one explicit, reviewable Forecast draft per supported destination. Transfers populate editable input but never submit automatically. Cross-module hidden orchestration and persistent client state remain deliberately absent.

## Product behavior and evidence boundaries

- All six workflows expose a guided business view plus **Advanced input** for the real payload and **Technical details** for full results.
- Raw JSON is hidden by default but never replaced with a simplified contract.
- Readiness is live and partial failures preserve unaffected workflows.
- Loading, validation, network, unavailable-module, empty, and successful-zero states are distinct.
- Forecast output can populate an Inventory forecast draft or Anomaly expected-sales draft. Inventory assumptions and observed anomaly sales remain user-supplied.
- The frontend does not recalculate inventory policy, anomaly thresholds, model scores, or recommendation rankings.

## Demo-input limitations

Bundled examples are small schema-shaped illustrative inputs. Forecast sales, prepared customer features, return-risk transactions, recommendation IDs, and anomaly rows are explicitly labeled synthetic rather than claimed authentic records. The anomaly example uses one aligned date, matching the production contract. Inventory state is prominently labeled **synthetic business inventory state** because M5 contains no inventory balances.

The API generates every displayed model output live from the committed frozen artifacts. Recommendation V1 intentionally exposes authentic item IDs without invented titles or imagery.

## Current limitations

- no authentication, persistence, saved scenarios, uploads, or deployment;
- JSON editors favor truthful contract visibility over spreadsheet-scale editing;
- recommendation V1 exposes item IDs rather than catalog metadata;
- Forecast drafts are in memory and disappear on refresh;
- no historical business KPI layer exists;
- light theme only.

Manual browser QA of the accepted redesign covered the supported desktop, tablet, and mobile layouts and the six workflow journeys. Deployment remains intentionally deferred.
