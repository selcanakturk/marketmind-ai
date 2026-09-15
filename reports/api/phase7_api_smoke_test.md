# V1 API smoke test — operational only

All nine routes were exercised in-process through the FastAPI test client and the real load-once registry. Fixtures were compact and deterministic; no outcome evaluation or lockbox analysis occurred.

| Route | Status | Rows | Observed latency |
|---|---:|---:|---:|
| `/health` | 200 | — | ~0.003 s |
| `/ready` | 200 | 6 readiness states | ~0.001 s |
| `/api/v1/models` | 200 | 6 | ~0.001 s |
| `/api/v1/forecast` | 200 | 28 | ~0.054 s |
| `/api/v1/segments` | 200 | 1 | ~0.020 s |
| `/api/v1/return-risk` | 200 | 1 | ~0.084 s |
| `/api/v1/recommendations` | 200 | 5 | ~0.023 s |
| `/api/v1/anomalies` | 200 | 1 | ~0.019 s |
| `/api/v1/inventory/recommend` | 200 | 1 | ~0.012 s |

All six modules reported ready and emitted their required semantic warnings. Recommendation request latency no longer includes the 2.76M-row event scan; graph validation and popularity ordering occur once at startup. Measurements are local operational observations, not performance guarantees or model-quality evidence.

