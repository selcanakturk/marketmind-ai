# Production inventory smoke test — scenario only

All operational quantities were explicitly marked **SCENARIO / BUSINESS INPUT — not observed M5 inventory truth**. The forecast was a current-style 28-day fixture used only to verify the production path.

| Operational observation | Result |
|---|---:|
| Decisions / series | 70 / 70 |
| Protection-period range | 1–20 days |
| Robust-normal decisions | 69 |
| Explicit buffer-mode decisions | 1 |
| Zero-order decisions | 4 |
| Positive replenishment decisions | 66 |
| Maximum-constrained decisions | 5 |
| Artifact load | 0.0028 s |
| Single decision | 0.0093 s |
| 70-series batch | 0.3496 s |
| Peak traced Python memory | 446,220 bytes |

No historical stockout, service, fill-rate, cost, order-performance, or other inventory KPI was calculated.

