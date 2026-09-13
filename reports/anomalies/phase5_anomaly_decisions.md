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

## Step 3 — DEVELOPMENT-SELECTED IF CONFIGURATION

Written before IF validation scoring:

| Decision | Frozen outcome |
|---|---|
| Features | robust score, residual, absolute residual, expected sales, weekday sine/cosine, event-present, state SNAP; exact order frozen |
| Identifiers/prices | excluded |
| Configurations | IF-1 200/auto; IF-2 300/512; IF-3 300/1024; contamination auto, all features, no bootstrap, seed 42, one job |
| Score | negative sklearn `score_samples`; higher means more anomalous, never a probability |
| Selected challenger | **IF-3** |
| Development basis | best engineered top-5%/top-2% entry rates at both magnitudes, broadest series coverage, lowest concentration, and highest robust-ranking overlap |
| Complexity | maximum observed serialized model 11.84 MB; still lightweight |
| Validation status | not IF-scored at selection freeze |
| Existing policies | robust threshold 3 and robust top-5/day unchanged |
| Lockbox | untouched |

## Step 3 — VALIDATION EVIDENCE AND FINAL CHALLENGER DECISION

After IF-3 was frozen, it was fit on the 9,800 prior seed/development rows and scored validation once. IF top-5/day overlapped robust top-5/day on 36/140 rows (25.71%) and included 14/25 robust-threshold alerts. Engineered rows entered the prior-training top 5% at 65.00% for 2× and 88.33% for 4× changes; direction correctness was 100%.

**Final decision: C — Isolation Forest is useful only as a secondary diagnostic.** It adds complementary ranking signal at low compute cost but is less interpretable, trails the robust baseline's validation engineered sensitivity, and has no authentic labels to validate its disagreements. No ensemble, hybrid, or further detector family is authorized. Robust threshold 3 and top-5/day remain unchanged. The anomaly lockbox remains completely untouched.

## Step 4 — FIRST AND FINAL ANOMALY LOCKBOX EVALUATION

The frozen HGBR-4 expectation was fit through `d_1913`; one frozen robust reference used exactly 11,760 earlier OOS residuals. The 1,960-row `d_1914–d_1941` lockbox produced 60 threshold-3 alerts (3.0612%): 58 spikes and 2 drops across 30 series. All scores were defined. Robust engineered detection was 77.50% at 2× and 97.50% at 4×. IF-3 remained a responsive but concentrated secondary diagnostic.

**Final primary assessment: STRONG GENERALIZATION**, with positive residual shift and spike imbalance documented as limitations. Detector/model search is closed, no setting changed, and the anomaly lockbox is **permanently consumed**.

## Step 5 — productionization

The frozen robust detector, threshold 3, top-five capacity, 70-series grain, forecast dependency, and research decisions are unchanged. State initializes from 13,720 legitimately OOS residuals through `d_1941`, including the consumed lockbox only as historical state—not fresh evidence. Exact histories support correct median/MAD updates. Live T batches score from state through T−1 and update only after the date is complete. IF-3 is optional secondary diagnostic, fit on that OOS corpus without outcome metrics. No evaluation, detector comparison, or policy selection occurred.
