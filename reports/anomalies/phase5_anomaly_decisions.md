# Phase 5 anomaly decisions

## FROZEN in Step 1

| Decision | Frozen outcome |
|---|---|
| Purpose | surface unusual sales behavior for investigation; no causal diagnosis |
| Unit/grain | one department × store × day; 70 dense series |
| Semantics | signed high-side spike, signed low-side drop, otherwise normal; absolute magnitude is severity |
| Actual | summed item units for that department-store date |
| Primary expectation | unchanged forecasting specification, refit point-in-time before every scored block |
| Production forecast artifact | prohibited for historical anomaly research because it trained through `d_1941` |
| Residual | `actual_sales - expected_sales` |
| Primary score concept | per-series residual centered by median and divided by `1.4826 × MAD` from earlier OOS residuals only |
| Undefined scale | score is undefined/no alert and counted; no silent substitute |
| Development | block 1 `d_1466–1493` scale seed; blocks 2–5 `d_1550–1577`, `d_1634–1661`, `d_1718–1745`, `d_1802–1829` development |
| Validation | `d_1886–d_1913`, 1,960 series-days |
| Anomaly lockbox | `d_1914–d_1941`, 2016-04-25–2016-05-22, 1,960 structural rows; untouched |
| Labels | M5 has no trustworthy anomaly labels; extremes are not ground truth |
| Evaluation layers | authentic diagnostics, stability/concentration, qualitative review, and engineered sensitivity tests |
| Engineered cases | positive spike, negative drop, 2–3 day sustained spike/drop; prior robust-scale magnitudes 2×/4×; drops floored at zero |
| Calendar/SNAP | handled in forecast expectation; descriptive output allowed, no causal claim |
| Price | excluded from first system and future realized prices prohibited |
| Step 2 baseline | interpretable robust standardized forecast residual |
| Threshold candidates | only `|score| ≥ 3` and `|score| ≥ 4` |
| Capacity candidates | top 5/day and top 10/day, compared separately from continuous score |
| Consecutive alerts | daily records remain separate; dashboard grouping may come later |
| Output | date, store, department, actual, expected, residual, score, direction, alert, severity rank; optional event/SNAP context |
| Forecasting evidence | forecasting lockbox remains consumed; no forecast selection claims are reopened |

## OPEN FOR STEP 2

- Which of thresholds 3 or 4, or capacity top-5/top-10, is operationally preferred after development diagnostics.
- Whether the past-only rolling median/MAD baseline adds useful contrast.
- Whether one lightweight Isolation Forest challenger is justified after the interpretable baseline.
- Minimum earlier OOS residual archive size beyond the frozen first-block seed.
- Exact deterministic injection locations within development and whether both 2-day and 3-day durations are necessary.
- Whether neutral severity bands can be justified; no critical/danger/fraud labels.

No anomaly model, threshold selection, lockbox scoring, or production engine was completed in Step 1.

## Step 2 — DEVELOPMENT-SELECTED DECISION

These choices were written after inspecting only DEV-1 through DEV-4 and before validation residual scoring or diagnostic inspection:

| Decision | Frozen outcome |
|---|---|
| Robust score | per-series `(residual − prior OOS residual median) / (1.4826 × prior OOS residual MAD)` |
| Scale timing | one state frozen at block start; current block appended only after every row is scored |
| Statistical threshold | **`|score| ≥ 3`** |
| Threshold rationale | 270/7,840 development alerts (3.44%), broader series coverage and less concentration than threshold 4, plus materially higher engineered 2×/4× sensitivity |
| Operational capacity | **top 5 defined absolute scores per day**, deterministic store/department ties |
| Capacity rationale | 560 review candidates over 112 development dates; half the workload of top 10 while ranking independently of statistical-alert status |
| Validation status at freeze | OOS forecast generated and sealed; robust scores and diagnostics not inspected |
| Lockbox | untouched; no forecast, residual, score, injection, or alert artifact |

## Step 2 — VALIDATION EVIDENCE (NO RE-SELECTION)

After the freeze above, validation `d_1886–d_1913` was scored once. All 1,960 scores were defined. The frozen threshold produced 25 authentic review candidates (1.2755%), comprising 19 spikes and 6 drops across 16 series. Threshold 4 produced 8 rows only as non-selected context. The exact engineered confirmation detected 74.17% of 2× rows and 97.50% of 4× rows, with 100% direction correctness in both groups. These results did not change the threshold, capacity, scoring rule, or scale policy.

The interpretable baseline is established. One controlled Isolation Forest challenger is justified for Step 3 under the same temporal partitions, but not trained here. The anomaly lockbox remains completely untouched.
