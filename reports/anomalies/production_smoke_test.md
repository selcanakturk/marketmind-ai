# Production smoke test — no outcome metrics

Run on a two-date, current-style forward scoring fixture immediately after the persisted `d_1941` state. This verifies operations only and is not evaluation.

| Operational observation | Result |
|---|---:|
| Rows scored | 140 |
| Dates | 2016-05-23–2016-05-24 |
| Defined / undefined scores | 140 / 0 |
| Statistical alerts | 2 |
| Review-priority rows | 10 |
| Direction distribution | 79 drop / 61 spike |
| IF diagnostic available | yes |
| Artifact load | 0.0665 s |
| 70-series daily scoring | 0.1467 s |
| Two-day runtime | 0.2933 s |
| Peak traced Python memory | 1,462,404 bytes |
| Explicit state update | success through 2016-05-24 |

The smoke path calculated no accuracy, precision, recall, F1, synthetic sensitivity, lockbox result, or other outcome-quality metric.
