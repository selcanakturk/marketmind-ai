# MarketMind V1 API usage

## Starting the API

Install `requirements.txt`, then run from the repository root:

```bash
PYTHONPATH=src .venv/bin/uvicorn marketmind.api.main:app --reload
```

OpenAPI is available at `/docs` and `/openapi.json`. This is local serving only; no deployment is claimed.

## Environment configuration

`MARKETMIND_ENV`, `MARKETMIND_ARTIFACT_ROOT`, `MARKETMIND_CORS_ORIGINS`, `MARKETMIND_LOG_LEVEL`, and `MARKETMIND_MAX_CONCURRENT_REQUESTS` configure runtime behavior. Artifact root defaults to the project working directory. CORS defaults to `http://localhost:3000,http://localhost:5173` and must be explicit in production.

Every response has a server-generated `X-Request-ID`. Business responses include module/artifact versions, generation time, and structured warnings.

## Health, readiness, and models

`GET /health` returns `{"status":"ok"}` without touching artifacts or inference. `GET /ready` returns `ready` or `degraded` plus six module booleans. `GET /api/v1/models` returns safe versions, readiness, model/method, grain, and limitations; it never returns filesystem paths.

## Forecast

`POST /api/v1/forecast` wraps the existing forecast engine. The abbreviated shape below must actually contain at least 56 consecutive history dates per series and exactly 28 future calendar dates:

```json
{"history":[{"d":"d_1886","date":"2016-03-28","store_id":"CA_1","dept_id":"FOODS_1","state_id":"CA","sales":100}],"future_calendar":[{"d":"d_1942","date":"2016-05-23","event_name":"none","event_type":"none","snap_CA":0,"snap_TX":0,"snap_WI":0}]}
```

Response rows contain `date`, store/department/state, horizon, and nonnegative predicted sales.

## Segmentation

`POST /api/v1/segments` accepts eligible prepared rows only:

```json
{"snapshot_at":"2017-09-30T23:59:59","feature_rows":[{"household_id":1,"recency_days":10,"basket_frequency":10,"monetary_value":500,"avg_basket_value":50,"unique_departments":5,"department_spend_hhi":0.25,"discount_share_of_gross":0.1,"coupon_basket_rate":0.1,"private_label_spend_share":0.2}]}
```

It returns semantic segment code/name and centroid distance. Distance is not probability or confidence.

## Return risk

`POST /api/v1/return-risk` accepts bounded Complete Journey transaction rows, product mapping, snapshot, and optional capacity. A transaction contains household/store/basket/product IDs, sales and three nonnegative discount fields, and timestamp. Output contains eligibility, score, rank, percentile, capacity, and flag. Score ranks no-basket-in-next-28-days risk; it is uncalibrated and is not contractual churn probability.

## Recommendations

```json
{"visitor_id":42,"snapshot_timestamp":"2015-09-18T03:00:00Z","k":20,"history_item_ids":[1001,1002]}
```

`POST /api/v1/recommendations` accepts at most 500 distinct item IDs and never accepts the raw event table. Rows contain rank, item, score, collaborative/popularity source, and seen-before status. Empty/unknown history returns deterministic popularity fallback rather than an error. Scores are not probabilities.

## Anomalies

```json
{"actual_sales":[{"date":"2016-05-23","store_id":"CA_1","dept_id":"FOODS_1","actual_sales":120}],"expected_sales":[{"date":"2016-05-23","store_id":"CA_1","dept_id":"FOODS_1","expected_sales":100}],"include_if_diagnostic":false}
```

`POST /api/v1/anomalies` is preview-only: it returns residual, robust score, direction, threshold flag, and review rank without updating state. Scores are not probabilities or causal diagnoses; IF is secondary only.

## Inventory

`POST /api/v1/inventory/recommend` accepts business inventory rows plus 28 aligned forecast rows per decision. Required inventory fields are snapshot/store/department, on-hand, on-order, backorders, lead/review days, and service target. Optional fields are MOQ, case pack, maximum, explicit buffer mode/days, and anomaly context. Output retains full demand, uncertainty, target, unconstrained/pre-max/final order, coverage, constraints, status, and warnings.

## Errors and limits

Errors use `{"error":{"code":"...","message":"...","details":...},"request_id":"..."}`. No traceback, environment, or local path is returned. Limits are 70 forecast series/3,920 history rows, 2,500 segment rows, 50,000 return-risk transactions, 500 recommendation history items, 70 anomaly rows, and 70 inventory decisions/1,960 forecast rows.

V1 is JSON-only. M5 powers forecast/anomaly/inventory, Complete Journey powers segments/return risk, and RetailRocket powers recommendations. Their historical identities are unrelated. Current limitations include no authentication, persistence, anomaly commits, upload workflow, frontend, or deployment.

