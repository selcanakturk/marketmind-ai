# MarketMind frontend architecture

## Status and boundary

This document freezes the Phase 8 Step 1 product and frontend contract. It is an implementation specification, not a React application. The frontend is a stateless client of the existing FastAPI V1 service. It must not reproduce model logic, weaken backend validation, infer unsupported outcomes, or join identities across M5, Complete Journey, and RetailRocket.

## Product model

MarketMind is one retail intelligence workspace with three connected operational themes:

- demand planning: Forecasting, Anomalies, and Inventory;
- customer intelligence: Segmentation and Return Risk;
- discovery: Recommendations;
- platform trust: Overview and System / Models.

The application shell provides a persistent product name, environment/readiness indicator, page title, warning region, and navigation. Every inference page follows the same rhythm: **context → input → validate and run → warnings → results → interpretation**. Inputs and results remain on the same page so the user can trace an output to its submitted scenario.

## Information architecture and routes

| Route | Page title | Purpose | API |
|---|---|---|---|
| `/` | Overview | Explain capabilities and current system status; provide quick actions | `GET /ready`, `GET /api/v1/models` |
| `/forecasting` | Demand Forecasting | Submit daily series and inspect a deterministic 28-day forecast | `POST /api/v1/forecast` |
| `/customers/segments` | Customer Segmentation | Assign prepared household features to frozen semantic segments | `POST /api/v1/segments` |
| `/customers/return-risk` | Customer Return Risk | Rank eligible households for no-basket-in-next-28-days risk | `POST /api/v1/return-risk` |
| `/recommendations` | Product Recommendations | Produce a ranked list from compact visitor history | `POST /api/v1/recommendations` |
| `/anomalies` | Sales Anomaly Preview | Review unusual forecast residuals without updating model state | `POST /api/v1/anomalies` |
| `/inventory` | Inventory Recommendations | Turn aligned forecasts and inventory scenarios into explainable orders | `POST /api/v1/inventory/recommend` |
| `/system/models` | System & Models | Inspect API liveness, aggregate readiness, and safe model metadata | `GET /health`, `GET /ready`, `GET /api/v1/models` |

Unknown frontend routes render a local not-found page with a link to Overview; they do not call the inference API.

### Navigation

Desktop uses a left sidebar in this order: Overview; Forecasting; Customers (Segmentation, Return Risk); Recommendations; Anomalies; Inventory; System / Models. Customers is one expandable group, open when either child route is active. Cross-page actions are links, never hidden orchestration:

- forecast results may offer “Prepare inventory payload” and “Use as expected sales,” but V1 requires an explicit reviewable transfer and a separate submit;
- anomaly results may offer “Copy context to inventory,” but context remains informational;
- Overview module cards link to their page, or System / Models when unavailable;
- customer pages cross-link to each other while explicitly retaining their shared Complete Journey dataset boundary.

Mobile uses a header with product name, readiness icon plus text, and a menu button opening a focus-managed navigation drawer. The drawer preserves the same hierarchy and closes after selection.

## Overview contract

The Overview is a truthful capability and system-status page, not a business-performance dashboard.

Sections:

1. Compact introduction: “Forecast demand, understand customer groups, prioritize return risk, recommend products, preview anomalies, and plan inventory.”
2. Readiness banner sourced from `/ready`: ready, degraded, unreachable, or loading.
3. Six capability cards joined client-side by module key with `/api/v1/models`: capability, ready state, model family, version, grain when present, one limitation, and action link.
4. Dataset boundary note: M5, Complete Journey, and RetailRocket are independent historical sources.
5. Quick actions to each workflow and System / Models.
6. Deferred insights notice: revenue, orders, forecast accuracy, conversion, stockout savings, churn prevented, resolution rate, and historical trends require persistence/business integrations and are not shown.

No synthesized “overall AI score” is permitted. The number of ready modules may be displayed as `ready modules / 6`; it is system availability, not business performance.

## Forecasting page contract

### Input

The page supports row-oriented JSON/table entry for `history` and `future_calendar`. A series is `store_id × dept_id`, with `state_id` attached to history. History fields are `d`, `date`, `store_id`, `dept_id`, `state_id`, `sales`. Calendar fields are `d`, `date`, `event_name`, `event_type`, and binary `snap_CA`, `snap_TX`, `snap_WI`.

The client provides structural guidance and early validation but never substitutes for server validation:

- at most 70 series and 3,920 history rows;
- at least 56 consecutive daily history rows per series is explained and checked when practical;
- one shared future calendar must contain exactly 28 consecutive dates beginning one day after the common history cutoff;
- sales must be nonnegative; SNAP fields are 0 or 1;
- duplicate dates, gaps, inconsistent series metadata, and malformed timestamps are surfaced before submit when detected;
- the server remains authoritative and its 422 details are mapped back to rows/fields.

Step 2 provides editable grids plus a JSON paste/import panel. It must not add CSV/file upload because V1 is JSON-only. Demo loading populates a compact authentic M5-derived input and remains visibly labeled.

### Output

Primary chart: selected store/department series, x-axis date, y-axis daily sales. Historical sales comes from the submitted request and uses a muted solid line; returned forecast uses a distinct solid accent beginning after the cutoff. A vertical “forecast starts” marker separates them. There is no confidence band.

Multi-series behavior: one selected series at a time in the detailed chart, with a searchable series selector; optional small summary rows may show all series but must not aggregate incompatible series silently. Changing selection is local and does not rerun inference.

Table columns: date, store, department, state, horizon, predicted sales. Default order follows response order; sort actions are explicit. Show module/artifact version, generation time, and every warning above the result. Empty results use “No forecast rows were returned,” not a zero-demand interpretation.

## Customers: segmentation contract

The page says prominently: “Prepared feature rows only—raw transactions are not accepted in V1.” Inputs are snapshot timestamp and up to 2,500 rows with `household_id` plus exactly these nine features:

1. `recency_days`
2. `basket_frequency`
3. `monetary_value`
4. `avg_basket_value`
5. `unique_departments`
6. `department_spend_hhi`
7. `discount_share_of_gross`
8. `coupon_basket_rate`
9. `private_label_spend_share`

The table-oriented editor groups count/value features separately from bounded shares. It shows field definitions and valid ranges without implementing feature engineering.

Results are a deterministic table: household, snapshot, segment code, segment name, centroid distance. Segment name/code may be filter chips. Centroid distance is a numeric distance and is never rendered as confidence, probability, quality, or a percentage. No segment-size chart is shown by default because a submitted subset is not a population. A simple count-by-segment summary is allowed only when labeled “this response” and computed directly from returned rows.

## Customers: return-risk contract

### Input

Two coordinated editable inputs are required:

- transactions: household, store, basket, product, sales value, retail discount, coupon discount, coupon-match discount, timestamp;
- product mapping: product, department, optional brand.

The context panel contains required `snapshot_at` and optional capacity (`0 < capacity <= 1`). Maximum transaction count is 50,000. The frontend may catch missing product mappings and timestamps at/after snapshot as usability checks, but does not reproduce eligibility or feature logic.

### Output

Summary values computed only from the response: returned households, eligible households, flagged households, and selected capacity. The primary result is a table with household, eligibility/status reason, ranking score, rank, percentile, selected capacity, and flagged status. Eligible ranked rows default to rank order; ineligible rows remain available in a filter.

Percentile may use a labeled 0–100 position bar if the API value is formatted according to its actual scale; it must retain the word “percentile,” not “probability.” The page permanently states that the score is an uncalibrated ranking score for no basket in the next 28 days and is not churn probability or a likelihood percentage.

## Recommendations contract

Input is a visitor ID, snapshot timestamp, `k` (1–1000), and up to 500 distinct nonnegative current-history item IDs. Item history uses token/chip entry with duplicate prevention and a count. No raw event upload exists.

The result header shows response `status` and, when nonempty, `fallback_reason`. Recommendations appear as a ranked table/list with rank, item ID, score, source, and a text-plus-icon “Seen before”/“Novel to supplied history” indicator. Source distinguishes collaborative, popularity fill, and any server-provided value without reinterpretation. Score is labeled “ranking score,” never probability.

No/unknown usable history is a successful fallback state rather than an error. The fallback banner and API warning remain visible: personalization was unavailable or incomplete and deterministic popularity supplied the result. The page never claims conversion or revenue lift.

## Anomalies contract

The title and submit area carry a persistent “Stateless preview—does not update anomaly state” label.

Inputs are aligned actual and expected rows (`date`, `store_id`, `dept_id`, and sales value), optional calendar rows (`event_name`, `event_type`, three SNAP flags), and an explicit secondary-diagnostic checkbox for `include_if_diagnostic` (default off). Maximum actual and expected length is 70; the client verifies key alignment and nonnegative sales before submit where possible.

Results:

- a daily table containing every response field;
- a compact residual chart by date for a selected series, centered on zero, with direction and alert encoded by markers as well as color;
- a top-review queue filtered by `is_review_priority`, ordered by `daily_review_rank`;
- status labels “Spike,” “Drop,” and “Normal” from the returned direction/alert fields, not from a client threshold calculation.

Table fields: date, store, department, actual, expected, residual, anomaly score, direction, statistical alert, daily review rank, review priority, IF score when requested, event context, SNAP active, and undefined-score reason. Copy explains that the frozen statistical threshold is inclusive `|score| >= 3`, while top-five review priority is a separate policy. There is no threshold slider. Anomalies are unusual forecast residuals, not causal diagnoses; IF is secondary only. Zero alerts is a valid result.

## Inventory contract

### Input

The page uses two grids: up to 70 inventory scenarios and up to 1,960 complete aligned forecast rows. Required scenario fields are snapshot, store, department, on-hand, on-order, backorders, lead time, review period, and service target. Optional fields are MOQ, case pack, maximum order, uncertainty method, safety-buffer days, and text anomaly context.

`uncertainty_method` exposes only documented values. `robust_normal` is the default and does not accept buffer days; explicit `user_buffer_days` requires them. The interface describes service target as an input target, never achieved service. It checks the 28-day series alignment and forecast/scenario key match for convenience; backend validation remains authoritative.

### Output

For a selected decision, an equation-style explanation uses returned values:

`forecast protection demand + safety stock = target stock`

`target stock - inventory position = unconstrained need`

Then a constraint rail shows MOQ → case pack → whole-unit rounding → maximum order → recommended quantity. Values come from `unconstrained_order_quantity`, `pre_max_constrained_quantity`, and `recommended_order_quantity`; the UI does not recalculate or replace them.

Summary fields: final recommended quantity, replenishment needed, planning status, days of cover, inventory position, protection-period demand, and safety stock. The detailed table preserves all response fields, including residual evidence, constraint warning, anomaly context, and planning warning. Zero replenishment is a valid outcome. Robust-normal limitations remain visible, and no stockout-prevention or savings claim is made.

## System & Models contract

This technical page independently displays:

- API liveness from `/health`;
- aggregate and per-module readiness from `/ready`;
- six metadata rows/cards from `/api/v1/models`: module, ready, version, model family/method, grain, warnings, safe status reason.

Refresh is manual plus one initial load; no aggressive polling is required for a portfolio/local service. Partial failures preserve any successful panel and offer retry. The page never displays paths, environment values, secrets, or internal errors.

## Shared UI state contract

### Loading

- initial shell: route renders immediately; status areas use labeled skeletons;
- inference: disable duplicate submit, keep inputs visible, show module-specific “Running…” text, and allow cancellation;
- metadata refresh: update control becomes busy but existing safe data remains visible;
- never use a blocking full-screen spinner for a single panel.

### Empty and successful-zero states

- untouched page: instructional empty state with input requirements and demo action;
- zero response rows: “The request completed, but no rows were returned” plus warnings;
- no eligible return-risk output: explain eligibility, not “low risk”;
- recommendation with empty/unknown history: fallback result and reason, not empty/error;
- zero anomaly alerts: “No statistical alerts in this submitted batch,” while retaining all scored rows;
- zero replenishment: “No replenishment recommended for this scenario,” not an error.

### Errors

The client parses the canonical envelope and stores the `X-Request-ID` response header, falling back to body `request_id`. A concise page-level alert shows code, safe message, field details where present, request ID, and retry when useful.

| Condition | User treatment |
|---|---|
| 400 | Request could not be parsed; preserve input and identify format issue |
| 404 | Requested resource/route was not found |
| 409 | Submitted timestamp/state conflicts with the model contract |
| 422 | Map safe validation details to fields/rows and show a summary |
| 500 | Generic service failure; show request ID, never internal details |
| 503 `MODULE_UNAVAILABLE` | Module unavailable; preserve input and link to System / Models |
| Network/timeout | API unreachable/timed out; distinguish from model rejection and offer retry |

### Degraded and warnings

If `/ready` is degraded, a shell banner names unavailable modules using readiness booleans. Navigation remains enabled; unavailable pages explain the state instead of hiding capabilities. A 503 is still authoritative at submit time.

Every `meta.warnings` entry is rendered in a persistent semantic-warning panel adjacent to results. Warnings are not toast-only, dismissed automatically, or converted into errors. Duplicate warnings may be visually coalesced only when their exact text is preserved. Recommendation `fallback_reason`, inventory row warnings, and anomaly undefined-score reasons are additional domain messages.

## Design system direction

- **Typography:** system-first sans stack; tabular numerals for measurements; 14–16 px body; restrained 12 px metadata; clear 20–30 px page hierarchy.
- **Spacing:** 4 px base with 4/8/12/16/24/32/48 steps. Operational pages cap readable width while grids may use the full workspace.
- **Radius:** 6–10 px for controls and surfaces; no pill-shaped containers except status/tags.
- **Surfaces:** neutral canvas, one raised primary work surface, borders rather than nested shadows; cards only when they communicate discrete status or capability.
- **Color:** neutral slate base, one blue/teal action accent. Green=ready/success, amber=warning/degraded, red=error/alert, blue=informational. Direction and state always also use text/icon/shape.
- **Tables:** sticky header where useful, tabular numbers, right-aligned metrics, readable row density, visible sort state, horizontal scroll rather than clipped columns.
- **Forms:** persistent labels, helper text for semantic constraints, inline error plus summary, units in labels, predictable add/remove-row controls.
- **Charts:** flat backgrounds, sparse grid lines, direct units, accessible palette, point/line patterns for status, tooltips that repeat series/date/value, no 3D or decorative smoothing.
- **Feedback:** inline banners for enduring warnings/errors; transient toast only for actions such as copy. Avoid gratuitous motion.
- **Theme:** Step 2 implements light theme first with tokens prepared for later dark mode. Do not ship an incomplete dark toggle.

## Accessibility contract

- complete keyboard operation, logical tab order, skip link, and focus restoration after route changes;
- clearly visible `:focus-visible` indicators with adequate contrast;
- one `h1` per page and semantic heading order/landmarks;
- programmatic labels, instructions, units, required state, and `aria-describedby` links for errors;
- validation summary focuses after failed submit; individual invalid controls remain identified;
- status never relies only on color; icons are decorative when text already names state;
- native tables with captions, header scope, announced sort state, and scroll-region labeling;
- each chart has a nearby textual summary and access to the equivalent data table;
- WCAG 2.2 AA contrast target; zoom/reflow at 200%; minimum practical touch targets of 44×44 px;
- loading announcements use restrained live regions; reduced-motion preference disables nonessential transitions;
- drawer traps focus, closes on Escape, returns focus to its trigger.

## Responsive contract

### Desktop (`>=1200px`)

Persistent 240–264 px sidebar; page header and controls remain visible; overview uses three capability cards per row; forms may use two columns; chart and result summary may share a 2:1 layout. Wide tables use available width with sticky key columns only if accessible.

### Tablet (`768–1199px`)

Sidebar collapses to an icon rail or drawer at the lower end; cards use two columns; forms become one or two columns based on field complexity; charts sit above tables; utility panels move below primary content. Tables scroll horizontally inside labeled regions.

### Mobile (`<768px`)

Navigation becomes a drawer. Cards and form sections are one column. Page actions use a non-obscuring sticky bottom area only when necessary. Charts occupy full width with reduced tick density and remain paired with textual summaries. Dense result tables use horizontal scroll with the first identity column visible when feasible; they are not converted into dozens of nested cards. Large row editors default to JSON paste/demo workflows with a small row preview, count, and error list. No content is hidden solely because of viewport size.

## Frontend API/data layer contract

- Environment variable: `VITE_MARKETMIND_API_BASE_URL`; normalize once and default to an empty same-origin base for production-friendly proxying. Local development documents `http://localhost:8000` in `.env.local`, never components.
- A single typed client module owns URL construction, JSON headers, timeout, cancellation, response parsing, and error normalization.
- Generated or hand-authored TypeScript types mirror the authoritative Pydantic/OpenAPI contract. Step 2 should generate from a pinned local `/openapi.json` snapshot when reproducibility is established, then review the diff.
- Default timeouts: 10 seconds for health/readiness/models and 60 seconds for inference; timeout is a distinct client error. Values are configuration constants, not page literals.
- Use `AbortController` for navigation, replacement submit, and explicit cancel. Ignore stale responses using request identity/generation guards.
- `ApiError` contains HTTP status, API code, safe message, typed field details, and request ID. It never exposes raw HTML or a JavaScript stack as server detail.
- Business responses retain `meta`, especially `warnings`; page adapters may format but not discard it.
- Components never call `fetch` directly. Domain modules call named client methods.
- TanStack Query is justified for the three idempotent status/metadata GETs: caching, independent retry, cancellation, and partial rendering. Mutations can also use it for consistent lifecycle handling, but inference results are not treated as persistent server state and are not automatically retried. No global state library is needed; URL/router state, query cache, and local form/result state suffice.

## Frozen Step 2 technology stack

| Technology | Decision and purpose |
|---|---|
| React + TypeScript | Typed component model; pin mutually compatible stable versions during Step 2 |
| Vite | Lean development/build tooling; `VITE_` environment contract |
| React Router | Nested Customers routes, not-found handling, accessible route shell |
| TanStack Query | GET caching, request lifecycles, cancellation, normalized server state; no automatic inference retry |
| Recharts | Small composable line/residual charts with custom accessible summaries; use tables as the canonical data alternative |
| Lucide React | Consistent restrained interface icons with explicit accessible-label rules |
| CSS Modules + CSS custom properties | Local styles and design tokens without a heavy UI framework or runtime styling system |
| React Hook Form | Efficient complex forms and row collections |
| Zod | Client structural validation and form typing; backend remains authoritative |
| Vitest + React Testing Library + user-event | Component, routing, form, API-state tests |
| MSW | Contract-shaped network mocks at the fetch boundary |
| axe-core integration | Automated accessibility smoke checks |

Exact compatible package versions will be pinned during Step 2 after scaffold creation. Do not add Redux/Zustand, a component megaframework, animation library, or data-grid dependency initially. Reassess virtualization only if authentic maximum-size workflows demonstrate a need.

## Demo-data strategy

Demo fixtures are compact request inputs, never claimed outcomes. They live separately from application code (proposed `frontend/src/demo/`) with provenance metadata: dataset, source/preparation script, extraction boundary, generated date, and `authentic-derived` or `synthetic-scenario` label.

- Forecast: curate one or two authentic M5 store-department series with the required 56-day history and 28-day calendar. No model output is stored as an alleged KPI.
- Segmentation: create a few authentic prepared Complete Journey feature rows using existing production feature tooling and a non-lockbox snapshot. Do not expose raw household transaction history in the bundle.
- Return risk: curate a bounded authentic non-lockbox transaction/product request sufficient to demonstrate eligibility and ranking. Outputs come from the live API.
- Recommendations: curate one authentic RetailRocket visitor’s distinct pre-cutoff history IDs and snapshot from non-lockbox source data; include a separate empty-history fallback request.
- Anomalies: actual and expected inputs may use a compact authentic M5/non-lockbox operational example generated through existing allowed production inputs. Label expected values as model forecasts, not observed truth; do not persist new evaluation metrics.
- Inventory: use clearly labeled synthetic business scenarios because M5 has no on-hand/on-order/lead-time inventory. Forecast rows may be authentic API output, but business state remains synthetic.

Generation occurs via reviewed repository scripts in Step 2, writing only small JSON fixtures. If generation touches a consumed lockbox or cannot establish provenance, stop and use a clearly labeled synthetic input instead. Never ship raw datasets or artifact bundles in the browser.

## Cross-module workflow rules

1. Forecast → Inventory: user explicitly selects/copies a 28-day forecast into a reviewed inventory request. Inventory business state must still be supplied. No hidden chained call.
2. Forecast → Anomalies: forecast rows may populate expected sales only after actual sales exist and the user reviews alignment. No hidden forecast invocation.
3. Anomalies → Inventory: a returned status may become text `recent_anomaly_context`; it cannot alter the inventory calculation.
4. Complete Journey supports Segmentation and Return Risk, but the UI does not assume an endpoint-produced segment is accepted by return risk.
5. M5, Complete Journey, and RetailRocket identities never join. There is no Customer 360, shared customer key, or cross-dataset narrative.

## Step 2 test plan

### Mocked API tests (required)

- route rendering, nested Customers navigation, active links, not-found route, mobile drawer keyboard behavior;
- typed client URL/base handling, JSON headers, timeouts, abort behavior, stale-response rejection, error-envelope parsing, and request-ID capture;
- initial/inference/refresh loading, untouched/zero-row/fallback empty states, and input preservation after errors;
- 400/404/409/422/500/503/network/timeout treatments, field-detail mapping, module-unavailable link, degraded banner;
- exact rendering of all `meta.warnings` and domain warnings;
- deterministic table order/formatting and response-only summaries;
- forecast request-history overlay without confidence intervals;
- segmentation nine-feature messaging and distance semantics;
- return-risk percentile/rank language and ineligible behavior;
- recommendation personalized and fallback cases, seen/novel labels;
- anomaly stateless copy, threshold-policy copy, zero-alert result, IF optional field;
- inventory equation/constraint rail from returned fields, zero-order case, robust-normal warning;
- desktop/tablet/mobile critical layout classes and table overflow behavior;
- axe smoke tests, keyboard paths, focus movement, labels, headings, live regions, and non-color status.

MSW responses should be minimal fixtures copied from schema shapes, explicitly labeled mocks, and tested as UI-state fixtures—not authentic model outcomes.

### Optional local FastAPI integration

A separate opt-in suite points `VITE_MARKETMIND_API_BASE_URL` to a locally started API and verifies health, ready, models, one compact request per inference route, error-envelope parsing, CORS, and request IDs. It does not run in ordinary unit tests, assert model quality, reopen lockboxes, or duplicate the backend’s 213-test suite.

## Implementation boundaries for Step 2

Step 2 may scaffold the frontend, implement the frozen pages/components/client, add compact curated input fixtures, and test the presentation contract. It may not change backend schemas, ML/business semantics, model artifacts, lockboxes, anomaly state, or inventory calculations. Any discovered contract blocker is documented and reviewed before backend change.

## Step 2 implementation status

The frozen architecture is implemented under `frontend/` with strict React/TypeScript/Vite, lazy routes, the responsive shell, centralized typed API client, TanStack Query lifecycles, all six inference workflows, Overview, System / Models, shared semantic states, Recharts visualizations, input-only demo fixtures, MSW isolation tests, and accessibility smoke coverage. CSS Modules were not necessary for the compact shared component set; global design tokens and deliberately scoped semantic class names implement the same frozen CSS-custom-property direction without a runtime styling dependency. Cross-page payload transfer is deferred; no hidden orchestration or global state was introduced.
