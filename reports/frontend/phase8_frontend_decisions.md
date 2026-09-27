# Phase 8 frontend decisions

## Step 1 — frozen product and implementation decisions

| Area | Frozen decision |
|---|---|
| Product | One e-commerce intelligence workspace, not six disconnected demos |
| Top-level IA | Overview, Forecasting, Customers, Recommendations, Anomalies, Inventory, System / Models |
| Customers | Segmentation and Return Risk are nested siblings under Customers |
| Frontend routes | `/`, `/forecasting`, `/customers/segments`, `/customers/return-risk`, `/recommendations`, `/anomalies`, `/inventory`, `/system/models` |
| Inventory API path | Runtime-authoritative `/api/v1/inventory/recommend` |
| Overview | System readiness, safe model metadata, capability explanation, quick actions; no fabricated business KPIs |
| Page workflow | Context → input → validate/run → warnings → results → interpretation |
| Forecast visual | Submitted historical sales plus returned 28-day point forecast; no interval |
| Segmentation | Prepared nine-feature rows only; response-subset table; distance never confidence |
| Return risk | Transaction/product input; ranking table; score never probability |
| Recommendations | Compact distinct history only; item-ID ranked list; visible fallback and seen/novel state |
| Anomalies | Explicit stateless preview; fixed policy; no threshold slider; IF secondary |
| Inventory | Returned equation/constraint explanation; service target not achieved service |
| Cross-module | Explicit reviewed payload transfer only; no hidden orchestration |
| Dataset identity | Never join M5, Complete Journey, and RetailRocket identities |
| Warnings | Render every API warning persistently adjacent to results |
| Degraded service | Keep navigation/capabilities visible; identify unavailable modules; 503 remains authoritative |
| Forms | Editable structured/JSON inputs; V1 has no file-upload UI |
| API base | `VITE_MARKETMIND_API_BASE_URL`, centralized and never hardcoded in components |
| Client | One typed client with timeout, cancellation, stale-response guard, request-ID/error normalization |
| Server state | TanStack Query; no automatic retries for inference mutations |
| App state | Router/query/local form state; no global state library |
| Stack | React, TypeScript, Vite, React Router, TanStack Query, Recharts, Lucide, CSS Modules/tokens, React Hook Form, Zod; pin stable compatible versions in Step 2 |
| Tests | Vitest, Testing Library/user-event, MSW, axe smoke; optional local FastAPI integration |
| Visual direction | Neutral, restrained, data-dense, accessible light theme; semantic colors and minimal motion |
| Responsive | Persistent desktop sidebar, adaptive tablet rail/drawer, mobile drawer; grids reflow and tables scroll |
| Demo inputs | Compact provenance-labeled authentic-derived inputs where allowed; inventory business state explicitly synthetic |
| Demo outputs | Produced by live API; mocked test fixtures never presented as authentic results |
| Dependencies now | None; frontend packages are deferred to Step 2 |

## Deferred until supporting architecture exists

- business-performance KPIs and historical dashboards;
- saved requests/results, sharing, audit history, and anomaly commits;
- authentication, authorization, tenancy, and user preferences;
- raw file upload/import services;
- product catalog enrichment for recommendation cards;
- background orchestration or automatic Forecast → Anomaly/Inventory execution;
- live production monitoring/polling and dark theme;
- cross-dataset customer identity or Customer 360.

## Phase 8 Step 2 recommendation

Create a new `frontend/` Vite React TypeScript application and implement in this order:

1. scaffold, strict TypeScript, lint/test setup, design tokens, accessible application shell, and route tree;
2. capture/generate reviewed OpenAPI-derived types and build the centralized API client with MSW contract fixtures;
3. implement Overview and System / Models first to prove connectivity, readiness, degraded/error states, and responsive navigation;
4. implement shared input grids/JSON editor, result tables, warning/error panels, and chart accessibility primitives;
5. implement Forecasting, Segmentation, Return Risk, Recommendations, Anomalies, then Inventory using page-local adapters only;
6. generate compact provenance-labeled demo **inputs** without touching consumed lockboxes; keep inventory scenarios explicitly synthetic;
7. complete responsive, keyboard, axe, mocked-state, and opt-in local FastAPI integration tests;
8. stop before deployment and report any contract blocker rather than modifying backend semantics.

No React application, frontend dependency, backend change, model operation, or lockbox access occurred in Step 1.

## Step 2 — implementation decisions

- Created an isolated `frontend/` Vite application and pinned all direct dependencies.
- Kept a single typed API client and exact runtime endpoint paths, including `/api/v1/inventory/recommend`.
- Used JSON row editors for large schema-first inputs plus structured scalar controls; no multipart/file behavior was implied.
- Added route-level lazy loading after the first production build identified a large combined chart/application chunk.
- Conservatively labeled all bundled request demos synthetic/illustrative because new authentic extraction would require additional provenance review. No stored outputs exist.
- Used TanStack Query for operational queries and inference lifecycle; inference retry remains disabled.
- Implemented light theme only and no global state library.
- Deferred explicit cross-page forecast transfer until a reviewed draft-transfer mechanism is designed; users can copy explicit payloads today.
- Kept test fixtures as MSW UI-state mocks, clearly separate from demo inputs and authentic model results.
- No backend/model/business changes, persistence, lockbox access, or deployment occurred.
