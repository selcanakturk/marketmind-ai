# Phase 7 API integration audit

## Exact production engines

| Module | Production callable | Artifact | Bytes | Input/output and integration finding |
|---|---|---:|---:|---|
| Forecast | `forecast(bundle, history, future_calendar)` | `models/forecasting/model.joblib` | 535,711 | ≥56 equal consecutive history rows/series + 28 calendar days → up to 70×28 forecast rows; research generation ~0.0086 s after prepared features |
| Segmentation | `assign_eligible_households(...)`; raw offline `assign_from_transactions(...)` | `models/segmentation/model.joblib` | 3,492 | frozen 9-feature eligible rows → semantic assignment; raw mode scans transaction/product input; reference smoke returned 2,446 rows |
| Return risk | `score_return_risk(transactions, products, snapshot_at, bundle, capacity)` | `models/return_risk/model.joblib` | 11,248,815 | point-in-time raw history → one row per observed household; ET-2 research prediction 0.037 s for 4,529 feature rows, excluding feature construction |
| Recommendations | `recommend_visitor(events, visitorid, snapshot_timestamp, bundle, k)` | `models/recommendations/model.joblib` | 14,344,306 | current API scans/sorts events → up to k ranked items; prior smoke ~3.993 s/visitor because each call revalidated 2.76M rows |
| Anomalies | `score_batch(actual, forecasts, state, calendar, IF)`; mutable workflow `score_and_update(...)` | `models/anomalies/model.joblib` | 3,369,626 | ≤70 one-date rows → score/flags/ranks; smoke ~0.147 s per 70-series date; state mutation is unsafe for preview |
| Inventory | `recommend_inventory(inputs, forecasts, bundle, anomaly_context)` | `models/inventory/inventory_bundle.joblib` | 3,244 | ≤70 decisions + 28 rows/series → one row/decision; smoke ~0.0093 s single/~0.350 s for 70 |

Metadata JSON and state CSVs are review aids, not separate inference models. All binary artifacts exist and validated in the audit. Combined compressed model size is 29,505,198 bytes (~28.14 MiB).

## Startup and footprint

Measured one-process sequential loads: forecast 0.040 s, segmentation 0.002 s, return risk 0.102 s, recommendations 7.701 s, anomalies 0.169 s, inventory 0.005 s; total 8.019 s. Tracemalloc reported ~41.35 MB current and ~69.13 MB peak allocations. Recommendation's thorough sparse-graph validation dominates startup but is paid once. Eager load with per-module failure isolation is feasible on lightweight hosting.

## Mutable state and difficulty

Forecasting, segmentation, return risk, and inventory inference are read-only when bundles are protected. Anomaly has explicit mutable-state helpers; HTTP will call only pure `score_batch`. Recommendation bundle cached properties are lazily materialized but effectively read-only after first access; registry warm-up should materialize them before concurrent traffic.

Forecast integration is moderate because payloads are tabular and calendar/history alignment strict. Segmentation is easy in prepared-feature mode but raw input is large. Return risk is moderate/high because feature construction scans bounded histories. Recommendation is high unless raw events are removed; compact history plus bundle-resident availability/popularity resolves it. Anomaly and inventory are moderate due exact temporal/forecast contracts.

## Dependency and package audit

Current requirements do not include FastAPI, Uvicorn, or Pydantic explicitly. Phase 7 implementation needs FastAPI, Uvicorn standard serving extras, and compatible Pydantic. Existing NumPy/Pandas/scikit-learn/SciPy/joblib remain. JSON-only V1 needs no `python-multipart`; no database, Celery, or new ML library is justified.

