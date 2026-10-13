# MarketMind V1 API usage

Status: **current operational documentation**. The V1 backend and React/TypeScript client are implemented; deployment is intentionally deferred.

## Start the API

From the repository root with Python 3.13.2:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
PYTHONPATH=src python -m marketmind.api.artifacts
PYTHONPATH=src uvicorn marketmind.api.main:app --reload
```

OpenAPI is available at `/docs` and `/openapi.json`. For the complete frontend startup sequence, see [`frontend/README.md`](../frontend/README.md).

## Configuration and runtime behavior

`MARKETMIND_ENV`, `MARKETMIND_ARTIFACT_ROOT`, `MARKETMIND_CORS_ORIGINS`, `MARKETMIND_LOG_LEVEL`, `MARKETMIND_MAX_CONCURRENT_REQUESTS`, `MARKETMIND_MAX_BODY_BYTES`, queue timeout, and rate-limit settings configure runtime behavior. Artifact root defaults to the project working directory. Development CORS defaults to explicit localhost origins; production requires explicit HTTPS origins.

Every response receives a server-generated `X-Request-ID`. Business responses include module and artifact versions, generation time, and structured warnings. Errors use the safe envelope `{"error":{"code":"...","message":"...","details":...},"request_id":"..."}` without tracebacks, environment values, or local paths.

## Operations and models

| Method and route | Purpose |
|---|---|
| `GET /health` | Process liveness without inference |
| `GET /ready` | Aggregate and per-module artifact readiness |
| `GET /api/v1/models` | Safe versions, methods, grain, readiness, and limitations |

The registry validates and loads all six artifacts once during application startup. If one artifact is unavailable, its module can return 503 while unaffected modules remain usable.

## Demand forecasting

`POST /api/v1/forecast` wraps the frozen 28-day forecasting engine. Requests contain at least 56 shared consecutive history dates per series and exactly 28 future calendar dates. Response rows contain date, store, department, state, horizon 1–28, and nonnegative predicted sales. V1 returns point forecasts without intervals.

## Customer segmentation

`POST /api/v1/segments` accepts prepared eligible feature rows: household ID, snapshot, and the frozen nine behavioral features. It returns stable semantic segment code/name and centroid distance. Distance is geometric atypicality—not probability, confidence, or membership likelihood.

## Customer re-engagement

`POST /api/v1/return-risk` accepts bounded Complete Journey transactions, product mappings, a snapshot, and optional selection capacity. Output preserves household eligibility/reason, score, rank, percentile, capacity, and flag.

The target is no basket in the next 28 days, not permanent churn. The score is an uncalibrated ranking signal rather than probability; default flagging capacity is the top 10% of eligible households.

## Product recommendations

```json
{"visitor_id":42,"snapshot_timestamp":"2015-09-18T03:00:00Z","k":20,"history_item_ids":[1001,1002]}
```

`POST /api/v1/recommendations` accepts up to 500 distinct item IDs rather than the raw event table. Results contain rank, item ID, score, collaborative/popularity source, and seen-before status. Empty or unknown history returns deterministic popularity fallback. Seen items are intentionally allowed by the frozen Item-CF policy, and scores are not probabilities.

## Sales anomaly preview

```json
{
  "actual_sales":[{"date":"2016-05-23","store_id":"CA_1","dept_id":"FOODS_1","actual_sales":120}],
  "expected_sales":[{"date":"2016-05-23","store_id":"CA_1","dept_id":"FOODS_1","expected_sales":100}],
  "include_if_diagnostic":false
}
```

`POST /api/v1/anomalies` accepts exactly one aligned date per batch. It is a stateless, non-mutating preview returning residual, robust score, direction, inclusive `|score| >= 3` statistical flag, and separate review rank. Optional Isolation Forest output remains secondary. Scores are not probabilities or causal diagnoses.

## Inventory recommendations

`POST /api/v1/inventory/recommend` accepts user-supplied business inventory rows plus a complete aligned 28-day forecast per decision. Required state includes snapshot/store/department, on-hand, on-order, backorders, lead/review days, and service target. Optional fields cover MOQ, case pack, maximum order, explicit buffer mode/days, and anomaly context.

The response retains demand, uncertainty, target stock, unconstrained/pre-maximum/final order quantities, coverage, constraints, status, and warnings. M5 supplies forecast evidence but no authentic inventory balances; these inputs and outputs are scenario decision support, not historical inventory optimization claims.

## Limits and verification

V1 is JSON-only. Limits are 70 forecast series / 3,920 history rows, 2,500 segment rows, 50,000 return-risk transaction rows, 500 recommendation history items, 70 anomaly rows on one date, and 70 inventory decisions / 1,960 forecast rows.

```bash
PYTHONPATH=src python -m marketmind.api.artifacts
PYTHONPATH=src pytest
PYTHONPATH=src python scripts/production_verify.py
```

Dataset ownership is fixed: M5 powers forecasting, anomaly preview, and inventory forecast input; Complete Journey powers segmentation and re-engagement; RetailRocket powers recommendations. The sources contain unrelated historical identities and are never joined into a unified customer record.

Current portfolio limitations include no authentication, persistence, anomaly commit endpoint, upload workflow, saved scenarios, or deployment. The implemented frontend consumes these routes through a centralized typed client.
