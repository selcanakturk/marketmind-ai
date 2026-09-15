# Safety-stock method assessment

## Frozen contract and residual source

The Step 1 grain, 28-day limit, snapshot alignment, inventory-position equation, periodic-review policy, and input ownership remain frozen. This uses only the finalized 13,720-row, 70-series, 196-date OOS forecast-residual corpus. Residual is actual minus expected; positive values are underforecast error. No anomaly score, threshold, IF result, or upstream decision is used.

## Contiguous OOS evidence

Seven independent 28-day blocks were retained: 2015-02-02–03-01, 2015-04-27–05-24, 2015-07-20–08-16, 2015-10-12–11-08, 2016-01-04–01-31, 2016-03-28–04-24, and 2016-04-25–05-22. Each has 1,960 rows. Windows never cross gaps; the last block remains consumed and is used only as finalized error evidence.

Each series has 196 residuals. Across series, median mean residual is 4.81 units and median median residual 1.66; ranges are −48.70–43.78 and −99.70–40.34. Median MAD is 36.68 (robust scale 54.38), standard deviation 59.04, positive share 52.04%, and skewness 0.413. Median upper quantiles are 78.94/102.00/124.39/149.34 at 0.90/0.95/0.975/0.99. The top ~1% absolute errors contribute median 4.22% of absolute magnitude (range 3.08%–6.15%). Evidence is heterogeneous and mildly positive-skewed, with nonzero location in some series.

## Serial dependence and horizon evidence

| Lag | Median correlation | IQR | Range |
|---:|---:|---:|---:|
| 1 | 0.400 | 0.263–0.479 | −0.059–0.717 |
| 2 | 0.270 | 0.110–0.405 | −0.137–0.639 |
| 3 | 0.196 | 0.060–0.382 | −0.130–0.626 |
| 7 | 0.311 | 0.211–0.392 | −0.095–0.580 |

| H | Total windows | Per series |
|---:|---:|---:|
| 1 | 13,720 | 196 |
| 2 | 13,230 | 189 |
| 3 | 12,740 | 182 |
| 7 | 10,780 | 154 |
| 14 | 7,350 | 105 |
| 21 | 3,920 | 56 |
| 28 | 490 | 7 |

H>1 windows overlap and are not independent. Median observed cumulative scale / √H-scaled daily scale is 1.16/1.24/1.59/1.92/2.17/2.24 at H=2/3/7/14/21/28. Method A increasingly understates observed cumulative variability; no correction was fitted.

## Candidate comparison and selection

Method A is `max(0, z(target) × 1.4826 × daily MAD × √H)`. It has complete coverage, deterministic monotonicity, service compatibility, and clear deployment, but assumes a normal upper-tail approximation and simple horizon scaling.

Method B is `max(0, empirical target quantile of consecutive H-day residual sums)`. It reflects bias, skew, and dependence, but is sparse. Requiring ten expected tail observations, 0.90 is supported only through H=14; 0.95/0.975/0.99 are unsupported at all horizons, and H=21/28 are unsupported at every target. No bootstrap, interpolation, or pooling was used.

Method C sums forecasts for an explicit integer number of user-selected buffer days. It is deterministic but not a service level. In low/medium/high scale examples, a three-day buffer was 65.16/893.72/8,852.38 units regardless of target. A low-scale H=14, 0.90 comparison was A 39.22 versus B 138.46, illustrating empirical irregularity and dependence.

**Method A is frozen as primary V1** because it alone combines complete 1–28-day availability, service compatibility, monotonicity, determinism, per-series scaling, and lightweight implementation. Its mismatch is a prominent limitation, not tuned away. Method C is the sole optional explicit override and is never blended. Method B is diagnostic only.

Final formula: `max(0, norm.ppf(service_level_target) × (1.4826 × per-series OOS residual MAD) × sqrt(lead_time_days + review_period_days))`. Target range remains [0.50, 0.999]. Zero MAD returns zero plus a warning. Bias is not silently added.

## Policy verification and limitations

Lead-time demand sums days 1…lead time; protection demand sums days 1…lead+review; expected daily demand is protection demand / protection days. Days of cover is position / positive expected daily demand, otherwise undefined. Adjustment order is raw need → MOQ → case-pack ceiling → whole-unit ceiling → maximum cap, preserving pre-max and unconstrained values plus warning.

Post-freeze scenarios/invariants passed: sufficient stock zero; positive mild/negative-position need; service/horizon monotonicity; 28 accepted/29 rejected; MOQ/case-pack/max examples; zero-demand safety; strict forecast alignment; and anomaly-context numeric independence.

The primary is not probabilistically calibrated; dependence, skew, bias, sparse tails, overlapping windows, and aggregation remain limitations. No inventory history or historical KPI exists. Step 3 may implement the frozen engine without retuning it.
