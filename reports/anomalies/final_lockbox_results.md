# Final anomaly lockbox results

> **THE ANOMALY LOCKBOX IS NOW PERMANENTLY CONSUMED.** This was its first and only evaluation. No threshold, scale, model, capacity, feature, or detector changed afterward.

## Frozen system and strict ordering

The final primary system is the interpretable department-store robust forecast-residual detector. Expected sales come from the unchanged HGBR-4 Full Direct forecast fit only through `d_1913`; residual is actual minus expected; score is the per-series residual centered by prior median and divided by `1.4826 × prior MAD`. Statistical alerts use `|score| ≥ 3`; daily review uses the top five absolute robust scores. IF-3 remains secondary only.

All choices were frozen first. The 11,760-row seed/development/validation OOS reference was constructed next. The authentic HGB forecast, residuals, robust scores, rankings, and policy flags were saved to `lockbox_robust_scores_authentic.csv` before any synthetic injection. IF and synthetic confirmation followed. Consumption metadata was written last.

## Forecast provenance and pre-lockbox state

| Property | Frozen value |
|---|---|
| Forecast training | `d_1–d_1913` |
| Scored block | `d_1914–d_1941`, 2016-04-25–2016-05-22 |
| Forecast training rows | 513,520 |
| Forecast horizon | 28 days |
| Series/rows | 70 / 1,960 |
| Feature specification | forecasting v1 Full Direct, unchanged |
| Forecast pipeline runtime | 15.91 seconds |
| Prior OOS blocks/rows | seed + four DEV + validation / 11,760 |

Each of the 70 series used one median, MAD, and robust scale frozen before `d_1914`. No earlier lockbox day updated later-day scale or forecast inputs.

## Robust score distribution and residual context

All 1,960 scores were defined; undefined count/rate was 0/0%. Median score was 0.434, IQR 1.440, p1 -1.739, p5 -1.097, p95 2.627, and p99 3.919. Minimum was -3.279, maximum and maximum absolute score were 5.632.

Forecast-residual MAE was 60.13 units, mean residual +29.92, and median residual +15.41. This positive shift means actual sales tended to exceed expected sales in this block; it is context, not permission to change the forecast model.

## Statistical alerts and daily review

The frozen threshold flagged 60 rows (3.0612%): 58 spike-direction and 2 drop-direction observations. Alerts covered 30 series and 22 dates. Forty series and six dates had none. A maximum of five alerts occurred in one series and eight on one date.

The daily robust review ranking produced exactly 140 rows—five on every date—and covered 49 series. Ordering was absolute score descending, then store and department ascending.

## Development, validation, and lockbox comparison

| Evidence | Development | Validation | Lockbox |
|---|---:|---:|---:|
| Rows | 7,840 | 1,960 | 1,960 |
| Alert rate | 3.44% | 1.28% | 3.06% |
| Spike/drop alerts | 214/56 | 19/6 | 58/2 |
| Series with alerts | 57 | 16 | 30 |
| Maximum alerts/date | 12 | 4 | 8 |
| Consecutive rows/runs/maximum | 127/48/10 | 8/4/2 | 17/8/3 |

Lockbox volume returned near the development aggregate, but its strong spike imbalance aligns with the block's positive forecast-residual shift. This is reported as temporal behavior, not post-hoc calibration evidence.

## Series and date concentration

The five busiest series contributed 35% of statistical alerts; the top ten contributed 60%. `WI_3/FOODS_1` had five alerts, while `CA_2/FOODS_2`, `TX_2/FOODS_1`, `CA_2/FOODS_1`, and `CA_2/HOUSEHOLD_1` each had four.

The five busiest dates were 2016-05-21 (8), 2016-05-22 (6), 2016-05-15 (6), 2016-05-07 (6), and 2016-04-30 (4). Daily observations remain separate.

Eight same-series consecutive runs contained 17 alert rows: seven two-day runs and one three-day run. No incident merging or causal label was applied.

## Top 15 authentic lockbox observations

| Date | Series | Actual | Expected | Residual | Score | Direction | Alert | Review rank | Context |
|---|---|---:|---:|---:|---:|---|---|---:|---|
| 2016-05-05 | WI_2/HOBBIES_2 | 83 | 28.39 | 54.61 | 5.632 | spike | yes | 1 | Cinco de Mayo; SNAP 1 |
| 2016-05-21 | CA_2/HOUSEHOLD_2 | 573 | 410.40 | 162.60 | 5.486 | spike | yes | 1 | no event; SNAP 0 |
| 2016-05-14 | CA_2/HOUSEHOLD_2 | 575 | 413.11 | 161.89 | 5.463 | spike | yes | 1 | no event; SNAP 0 |
| 2016-05-15 | CA_2/FOODS_2 | 881 | 681.20 | 199.80 | 4.825 | spike | yes | 1 | no event; SNAP 0 |
| 2016-04-29 | WI_2/HOUSEHOLD_1 | 1,635 | 979.08 | 655.92 | 4.773 | spike | yes | 1 | no event; SNAP 0 |
| 2016-05-21 | CA_2/FOODS_1 | 809 | 549.31 | 259.69 | 4.575 | spike | yes | 2 | no event; SNAP 0 |
| 2016-04-30 | CA_3/HOBBIES_2 | 131 | 54.46 | 76.54 | 4.557 | spike | yes | 1 | Pesach End; SNAP 0 |
| 2016-05-22 | CA_2/FOODS_2 | 835 | 653.40 | 181.60 | 4.410 | spike | yes | 1 | no event; SNAP 0 |
| 2016-05-04 | WI_3/FOODS_1 | 407 | 218.35 | 188.65 | 4.370 | spike | yes | 1 | no event; SNAP 0 |
| 2016-05-03 | WI_3/FOODS_1 | 422 | 235.63 | 186.37 | 4.320 | spike | yes | 1 | no event; SNAP 1 |
| 2016-05-01 | WI_1/FOODS_2 | 1,047 | 772.51 | 274.49 | 4.272 | spike | yes | 1 | Orthodox Easter; SNAP 0 |
| 2016-05-03 | TX_3/FOODS_1 | 463 | 260.26 | 202.74 | 4.219 | spike | yes | 2 | no event; SNAP 1 |
| 2016-05-09 | WI_2/FOODS_3 | 3,388 | 2,584.97 | 803.03 | 4.202 | spike | yes | 1 | no event; SNAP 1 |
| 2016-05-13 | CA_2/FOODS_1 | 683 | 448.70 | 234.30 | 4.141 | spike | yes | 1 | no event; SNAP 0 |
| 2016-05-21 | CA_2/HOBBIES_1 | 691 | 470.08 | 220.92 | 4.126 | spike | yes | 3 | no event; SNAP 0 |

These are deterministic unusual-residual examples, not verified business anomalies or causal findings.

## Calendar context

Twelve statistical alerts occurred on primary-event dates and 24 had the applicable state SNAP flag. For descriptive context only, corresponding counts among 1,900 non-alert rows were 268 and 676. These overlaps do not establish causes.

## ENGINEERED TEST CASE confirmation

Injections changed only actual sales and recomputed derived residual features. Expected sales, forecast model, prior residual state, MAD, robust scale, and other rows remained fixed.

| Family | 2× detection | 4× detection |
|---|---:|---:|
| One-day drop | 80.00% | 90.00% |
| One-day spike | 80.00% | 100.00% |
| Two-day drop | 45.00% | 100.00% |
| Two-day spike | 85.00% | 100.00% |
| Three-day drop | 80.00% | 93.33% |
| Three-day spike | 90.00% | 100.00% |
| **All engineered rows** | **77.50%** | **97.50%** |

Direction correctness was 99.17% at 2× and 100% at 4×. These are engineered sensitivity measures, never authentic recall.

| Magnitude | Development | Validation | Lockbox |
|---|---:|---:|---:|
| 2× robust detection | 61.25% | 74.17% | 77.50% |
| 4× robust detection | 94.79% | 97.50% | 97.50% |

## Isolation Forest secondary diagnostic

Frozen IF-3 was fit on the same 11,760 pre-lockbox OOS rows. Lockbox IF scores had median 0.447, IQR 0.106, p95 0.616, p98 0.648, p99 0.667, and maximum 0.752.

Its daily top-five list contained 140 rows across 34 series; the five busiest series contributed 51.43%, and `CA_3/FOODS_3` contributed 20 rows. It overlapped robust top-five rankings on 48 rows (34.29%). Thirty-one IF top-five rows crossed the robust threshold, representing 51.67% of the 60 robust alerts.

For engineered cases, 2× changes entered the fixed prior-training IF top 5% on 72.50% and top 2% on 47.50%. At 4×, results were 93.33% and 81.67%. IF remains directionless; direction correctness comes from the robust residual.

**SECONDARY DIAGNOSTIC CONFIRMED.** IF-3 remained responsive and complementary, but its repeated high-volume FOODS_3 concentration, lower interpretability, and absence of authentic labels provide no basis to replace the primary detector or create a hybrid.

## Generalization assessment and limitations

### **PRIMARY ROBUST SYSTEM — STRONG GENERALIZATION**

The lockbox alert rate sits near development aggregate behavior, every scale remained usable, engineered sensitivity matched or improved on validation, direction semantics stayed correct, concentration remained reviewable, and the detector stayed interpretable. The assessment includes an important limitation: positive residual shift produced a 58-to-2 spike/drop imbalance, demonstrating dependence on forecast calibration and period context.

M5 still supplies no authentic anomaly labels; alerts cannot be assigned precision, recall, accuracy, false-positive, or true-positive semantics. Forecast errors are not causes. Results do not authorize policy revision, productionization, or another model family.

## Permanent lockbox warning

**THE ANOMALY LOCKBOX IS PERMANENTLY CONSUMED.** Detector search is closed. Robust threshold 3, MAD factor 1.4826, prior-state policy, top-5/day capacity, forecast specification, IF-3 configuration, features, and primary/secondary roles are unchanged. Any future architecture change requires a new research cycle and genuinely new evidence.
