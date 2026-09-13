# Sales anomaly detection methodology

## Purpose

MarketMind will flag department-store daily sales that differ unusually from a point-in-time expectation. A flag is investigation support, not evidence of fraud, stockout, promotion failure, inventory failure, or any other cause. Step 1 freezes methodology only; no detector is fitted.

## Dataset, unit, and grain

The source is authentic M5 `sales_train_evaluation.csv` joined to `calendar.csv`; `sell_prices.csv` was inspected only for availability policy. The anomaly unit is one `(date, store_id, dept_id)` observation. The primary grain remains the forecasting grain: 7 departments × 10 stores = 70 dense daily series. Actual sales are summed item units.

## Anomaly semantics

Let residual `r = actual_sales - expected_sales`. Positive score direction means an unusual sales spike; negative means an unusual sales drop; observations inside the selected policy boundary are normal. Absolute score is severity. Direction and severity are statistical descriptions, not causes or probabilities.

## Expected sales

The primary expectation is the unchanged frozen forecasting specification, refitted separately at each origin using only earlier sales and producing genuinely out-of-sample predictions. It can account for known-ahead weekday, calendar event, and state SNAP context. The all-history production forecasting artifact must never score historical anomaly blocks.

Alternatives retained for controlled comparison are a seasonal historical expectation and a past-only rolling median. A robust rolling expectation is transparent but reacts slowly to level changes; seasonal history is simple but limited; forecast residuals incorporate more context but inherit forecast error; a purely unsupervised feature-space detector is less interpretable and unnecessary as the first baseline.

## Residual definition and normalization

The raw signed residual is `actual - expected`. Absolute and relative residuals are diagnostics only. Raw percentage error is rejected because small expected values make it unstable. The primary anomaly score concept is a per-series robust standardized residual:

`score = (r - median(historical OOS residuals)) / (1.4826 × MAD(historical OOS residuals))`.

The residual archive must contain only earlier out-of-sample residuals. Development block 1 seeds that archive and is not used to choose a threshold. The archive expands chronologically thereafter. A zero or non-finite MAD yields an undefined score and no alert; it is reported, not silently replaced. RMSSE-like naïve-change scaling remains a diagnostic normalization candidate, not the primary score.

## Temporal protocol

All score blocks are 28 days and every expected value is generated from a model trained strictly before its block.

| Role | Training history | Score block | Dates |
|---|---|---|---|
| Scale seed | `d_1–d_1465` | `d_1466–d_1493` | 2015-02-02–2015-03-01 |
| Development 2 | `d_1–d_1549` | `d_1550–d_1577` | 2015-04-27–2015-05-24 |
| Development 3 | `d_1–d_1633` | `d_1634–d_1661` | 2015-07-20–2015-08-16 |
| Development 4 | `d_1–d_1717` | `d_1718–d_1745` | 2015-10-12–2015-11-08 |
| Development 5 | `d_1–d_1801` | `d_1802–d_1829` | 2016-01-04–2016-01-31 |
| Anomaly validation | `d_1–d_1885` | `d_1886–d_1913` | 2016-03-28–2016-04-24 |
| Untouched anomaly lockbox | `d_1–d_1913` | `d_1914–d_1941` | 2016-04-25–2016-05-22 |

The first five blocks contain 9,800 series-days; block 1 seeds scale and blocks 2–5 support development. Validation and lockbox each contain 1,960 series-days. These dates overlap forecasting research by design, but forecasting evidence is not being reinterpreted: the forecast specification is frozen, while anomaly scoring, thresholds, synthetic comparisons, and alert policies are new and temporally isolated.

## Evaluation without labels

M5 has no trustworthy anomaly ground truth. Historical extremes will not be relabeled as truth. Step 2 must combine: score/alert distributions on authentic development data; temporal alert-rate stability; high/low balance; concentration by series and date; repeated daily alerts; top-N qualitative inspection; descriptive event/SNAP relationships; and engineered perturbation response. None alone estimates real-world precision or recall.

## Synthetic injection policy

Synthetic cases are explicitly **ENGINEERED TEST CASES**. Candidate changes are a one-day positive spike, one-day negative drop, two-to-three-day sustained spike, and two-to-three-day sustained drop. Positions and random seeds, if sampling is used, are frozen before comparison. Magnitudes will use each series' prior-history robust variation (candidate multiples 2 and 4 of a trailing robust scale), never lockbox behavior. Drops are clipped at zero; original and perturbed copies remain separate. These tests ask whether a detector responds to controlled perturbations, never what its real-world anomaly precision is.

## Authentic-data diagnostics

Report alert rate, signed score distribution, high/low ratio, per-series and per-date counts, cross-series concentration, consecutive alerts, undefined-scale rate, top-N examples, and descriptive association with event and SNAP days. Do not use these diagnostics to infer causes.

## Baseline and detector candidates

Step 2 begins with the interpretable per-series robust residual score above. Only two predeclared candidate thresholds, `|score| ≥ 3` and `|score| ≥ 4`, may be compared in development; neither is ground truth. Candidate challengers are (1) a past-only rolling-median/MAD rule and (2) one lightweight Isolation Forest using residual/context features. No model zoo or detector fitting is authorized in Step 1.

## Alert policy

Score and alert capacity are separate. Step 2 will compare fixed thresholds 3 and 4 plus operational top-5 and top-10 per day policies. Threshold policies preserve absolute statistical meaning but yield variable volume; top-N controls workload but forces alerts on quiet days. Selection considers stability and review capacity, not fabricated accuracy. Daily alerts remain separate; a future dashboard may visually group consecutive records without changing them into inferred incidents.

## Calendar, SNAP, and price policy

Known-ahead primary event and state-specific SNAP fields remain inside the forecasting expectation; they are not separately double-counted in the first anomaly score. Secondary event columns and event/SNAP flags may accompany results for descriptive review. Price is excluded from Phase 5's first system to match the frozen forecast contract. Observed historical prices may later be diagnostic, but future realized prices are never assumed known.

## Output contract

Required future fields are `date`, `store_id`, `dept_id`, `actual_sales`, `expected_sales`, `residual`, `anomaly_score`, `direction`, `is_alert`, and `severity_rank`. Optional descriptive context is `event_name`, `event_type`, and `snap`. No causal explanation or unsupported severity label is emitted.

## Leakage register

- No random splits; all fits, residual archives, scales, and policies are chronological.
- Expected sales for date X cannot use sales on or after X.
- Rolling windows are trailing and shifted; centered windows are prohibited.
- In-sample forecast errors cannot be anomaly evidence.
- Future/full-history residual distributions and retrospectively computed all-history MAD are prohibited.
- The production forecast model trained through `d_1941` cannot score historical anomaly research.
- Calendar fields must have been knowable at issuance; future realized sales and prices are prohibited.
- Anomaly lockbox scores cannot influence threshold, detector, injection, or policy selection.
- Synthetic labels/locations cannot enter fitting or normalization, and authentic extremes cannot become fabricated labels.

## Forecasting integration and lockbox policy

The intended flow is frozen forecast specification → point-in-time expected sales; observed sales → actual sales; residual/scaling layer → signed anomaly score; separate policy → alert. The forecasting lockbox remains consumed as forecasting evidence. The anomaly lockbox `d_1914–d_1941` is frozen now for the new objective and remains untouched: only its structural feasibility count was checked.

## Open for Step 2

Step 2 may generate development-block forecasts, build the earlier-only residual archive, execute the robust baseline, compare the two thresholds and capacity policies, and run the frozen engineered tests. Final threshold/policy choice, whether one challenger is justified, minimum residual-history handling beyond undefined scores, and optional neutral severity bands remain open. Lockbox access is not authorized.

## Production status (appended after research completion)

Research subsequently selected robust threshold 3 and top-five/day, retained IF-3 only as secondary, completed one final lockbox evaluation, and permanently consumed it. Production now persists exact OOS residual history through `d_1941` and applies score-then-update daily semantics. Earlier chronology remains unchanged; see `docs/anomaly_production.md`.
