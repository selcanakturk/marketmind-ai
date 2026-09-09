# Phase 2 Customer Segmentation — Temporal Stability and Naming

## Frozen methodology

This analysis retains the Step 2 methodology unchanged: Complete Journey grocery households; eligibility of at least 90 observed-history days, 5 distinct baskets, and 30 active-span days; the nine frozen ordered features; `log1p` on recency, frequency, monetary value, and average basket value; unchanged diversity/promotion/brand ratios; snapshot-fitted `RobustScaler`; and `KMeans(n_clusters=3, init="k-means++", n_init=20, max_iter=300, tol=0.0001, algorithm="lloyd", random_state=42)`.

No future return-risk outcomes, post-snapshot transactions, algorithm changes, K changes, feature changes, or parameter tuning were used.

## Historical snapshots and independent fits

Each month was independently reconstructed, scaled, and fitted using data available by 23:59:59 on its month end.

| Snapshot | Eligible households | Silhouette ↑ | Davies–Bouldin ↓ | Calinski–Harabasz ↑ |
|---|---:|---:|---:|---:|
| 2017-06-30 | 2,085 | 0.2069 | 1.5302 | 548.30 |
| 2017-07-31 | 2,172 | 0.2038 | 1.5668 | 536.74 |
| 2017-08-31 | 2,219 | 0.2035 | 1.5746 | 539.41 |
| 2017-09-30 | 2,247 | 0.2031 | 1.5647 | 559.69 |

June has sufficient support under the unchanged rules. Eligibility rises smoothly as households accumulate history. Separation metrics occupy a narrow range; no isolated month drives the September result.

## Cluster alignment

Raw KMeans IDs are arbitrary. For each snapshot, the median original-unit profile for each cluster was centered on that snapshot's household median and divided by its household IQR across the nine frozen features. Hungarian assignment then minimized total Euclidean distance between each snapshot's relative profile signatures and September's signatures. No future outcomes or semantic names entered alignment.

| Snapshot | Raw → September reference IDs | Matched profile distances by reference ID 0 / 1 / 2 |
|---|---|---|
| June | 0→1, 1→0, 2→2 | 0.579 / 0.158 / 0.183 |
| July | 0→2, 1→1, 2→0 | 0.471 / 0.079 / 0.092 |
| August | 0→0, 1→1, 2→2 | 0.245 / 0.043 / 0.226 |
| September | identity | 0 / 0 / 0 |

The raw permutations demonstrate why integer IDs cannot be a business contract. The high-engagement and lower-engagement signatures are especially close to September throughout; the smaller promotion-oriented group moves more but remains recognizable.

## Population and structural stability

Aligned September reference ID 0 is promotion-oriented, ID 1 is high-engagement/broad, and ID 2 is lower-engagement/focused.

| Snapshot | Promotion-oriented | High-engagement/broad | Lower-engagement/focused |
|---|---:|---:|---:|
| June | 230 (11.03%) | 997 (47.82%) | 858 (41.15%) |
| July | 226 (10.41%) | 1,066 (49.08%) | 880 (40.52%) |
| August | 257 (11.58%) | 1,077 (48.54%) | 885 (39.88%) |
| September | 293 (13.04%) | 1,077 (47.93%) | 877 (39.03%) |

No segment collapses or becomes pathological. The largest absolute share movement from June to September is 2.12 percentage points for the lower-engagement group; the promotion-oriented group grows 2.01 points.

## Profile stability in original units

### Promotion-Oriented Basket Builders (`PROMOTION_BASKET_BUILDERS`)

| Snapshot | Recency | Baskets | Spend | Avg basket | Depts | HHI | Discount share | Coupon rate | Private-label share |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| June | 4 | 25 | 1,057.36 | 42.57 | 11 | 0.348 | 19.02% | 24.53% | 23.75% |
| July | 4 | 27 | 1,130.27 | 44.99 | 11 | 0.350 | 19.08% | 24.68% | 23.90% |
| August | 5 | 32 | 1,331.92 | 43.59 | 11 | 0.345 | 19.23% | 22.22% | 24.71% |
| September | 5 | 34 | 1,412.95 | 43.32 | 11 | 0.349 | 19.47% | 21.43% | 23.96% |

### High-Engagement Broad Shoppers (`HIGH_ENGAGEMENT_BROAD`)

| Snapshot | Recency | Baskets | Spend | Avg basket | Depts | HHI | Discount share | Coupon rate | Private-label share |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| June | 2 | 42 | 1,309.21 | 30.48 | 12 | 0.313 | 14.25% | 3.33% | 27.49% |
| July | 2 | 48 | 1,482.57 | 30.26 | 12 | 0.310 | 14.45% | 3.35% | 27.75% |
| August | 2 | 55 | 1,624.05 | 29.78 | 12 | 0.309 | 14.26% | 3.23% | 27.99% |
| September | 2 | 61 | 1,830.30 | 30.01 | 13 | 0.309 | 14.10% | 3.20% | 27.89% |

### Lower-Engagement Focused Shoppers (`LOWER_ENGAGEMENT_FOCUSED`)

| Snapshot | Recency | Baskets | Spend | Avg basket | Depts | HHI | Discount share | Coupon rate | Private-label share |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| June | 11 | 13 | 287.62 | 20.04 | 7 | 0.391 | 15.04% | 0% | 25.42% |
| July | 11 | 14 | 316.46 | 20.35 | 7 | 0.385 | 14.92% | 0% | 24.89% |
| August | 13 | 15 | 345.22 | 20.57 | 8 | 0.377 | 15.02% | 0% | 24.47% |
| September | 13 | 17 | 378.33 | 19.65 | 8 | 0.376 | 15.01% | 0% | 25.92% |

Counts and cumulative spend/frequency naturally rise with time. Relative meaning does not reverse: the high-engagement group remains most frequent, highest-spend, broadest and least concentrated; the promotion group retains the largest baskets and coupon/discount association; the lower-engagement group remains least frequent, lowest-spend, narrower, and more concentrated.

## Household transitions

Only households eligible in both consecutive snapshots are compared. “Unchanged” refers to aligned behavioral identity.

| Interval | Common households | Unchanged | Moved | Cross-time ARI |
|---|---:|---:|---:|---:|
| June → July | 2,085 | 90.65% | 9.35% | 0.7133 |
| July → August | 2,172 | 90.38% | 9.62% | 0.7001 |
| August → September | 2,219 | 90.67% | 9.33% | 0.7175 |

Row-normalized transitions use P = promotion, H = high-engagement, and L = lower-engagement:

| Interval/from | To P | To H | To L |
|---|---:|---:|---:|
| June→July P | 86.09% | 10.43% | 3.48% |
| June→July H | 0.70% | 94.28% | 5.02% |
| June→July L | 1.40% | 10.96% | 87.65% |
| July→August P | 96.02% | 1.77% | 2.21% |
| July→August H | 2.63% | 90.99% | 6.38% |
| July→August L | 0.57% | 11.25% | 88.18% |
| August→September P | 94.94% | 3.89% | 1.17% |
| August→September H | 2.60% | 91.27% | 6.13% |
| August→September L | 2.03% | 9.27% | 88.70% |

Cross-time ARI is not seed stability: it combines genuinely accumulated shopping behavior, eligibility changes, and independently refitted geometry. Roughly 9–10% monthly movement is compatible with a useful dynamic segmentation system; forcing zero movement would be undesirable.

## September reference-model sensitivity

As a separate centroid-consistency diagnostic, earlier eligible vectors were transformed by the fitted September scaler and assigned to September centroids.

| Earlier snapshot | Agreement with independent aligned fit | ARI |
|---|---:|---:|
| June | 90.46% | 0.7061 |
| July | 93.28% | 0.7923 |
| August | 95.40% | 0.8529 |

Agreement increases toward September, supporting centroid consistency. This is not a historical deployment simulation because the September model was unavailable in earlier months.

## Segment naming decision

The temporal evidence supports these stable semantic identities:

| September raw cluster | Stable segment code | Display name | Evidence-based description |
|---:|---|---|---|
| 1 | `HIGH_ENGAGEMENT_BROAD` | High-Engagement Broad Shoppers | Most recent/frequent, highest spend, broadest departments, lowest HHI in every snapshot |
| 0 | `PROMOTION_BASKET_BUILDERS` | Promotion-Oriented Basket Builders | Largest average basket and clearly highest observed coupon/discount utilization in every snapshot |
| 2 | `LOWER_ENGAGEMENT_FOCUSED` | Lower-Engagement Focused Shoppers | Less recent, lowest frequency/spend, narrowest departments, highest HHI in every snapshot |

The first column is version-specific and may change after any refit. APIs, tables, and dashboards must contract on `segment_code`, `display_name`, and version metadata—not raw `cluster_id`. Names describe observed behavior; they do not claim profitability, loyalty, risk, or causal promotion response.

## New-household and assignment policy

Households failing any frozen rule receive status `insufficient_history`. This is an eligibility state, not a learned fourth segment. They are reassessed at the next snapshot and become assignable only after ≥90 observed-history days, ≥5 distinct baskets, and ≥30 active-span days.

For an eligible household:

1. construct the nine frozen point-in-time features in deterministic order;
2. apply the four frozen `log1p` transformations;
3. apply the fitted RobustScaler without refitting;
4. assign the nearest fitted KMeans centroid;
5. map version-specific `cluster_id` to the stable semantic contract.

Conceptual output fields are `household_id`, `snapshot_date`, `model_version`, `cluster_id`, `segment_code`, `segment_name`, `eligibility_status`, and `distance_to_centroid`. Distance is a geometric atypicality diagnostic—not probability, confidence, or membership likelihood.

## Refresh cadence, drift, and refit policy

- **Eligibility and assignment:** monthly at calendar month-end. Daily re-segmentation is not warranted by this panel cadence.
- **Model review:** quarterly once deployed, with no automatic calendar refit.
- **Refit:** evidence-triggered after sustained, corroborating drift or loss of semantic meaning; a single noisy indicator is insufficient.

Future monitoring should cover:

- feature drift: medians and key quantiles by feature; PSI only after bins/reference policy is validated;
- population drift: eligible/insufficient-history rates and segment shares;
- geometry drift: aligned centroid/profile movement in the frozen feature space;
- assignment atypicality: distance-to-centroid median, upper quantiles, and segment-specific distributions;
- semantic drift: whether defining profile orderings and descriptions remain true.

Potential refit triggers are sustained multi-period feature shifts, material persistent segment-share changes, growing distance distributions, profile inversion/loss of interpretability, or material retailer/domain changes. Numeric alert thresholds are not invented from four historical months; they require production baseline evidence and business review.

## Known limitations and productionization readiness

- The historical check covers four cumulative snapshots within one retailer panel and no seasonally comparable second year.
- Cumulative magnitude features rise mechanically with observation length; a fixed-window alternative was not authorized and remains a future methodology question.
- Alignment uses relative median profiles and can conceal within-segment distribution changes.
- Cross-time movement cannot separate behavioral evolution from independent refitting effects.
- The semantic codes are justified, but naming requires stakeholder review for dashboard clarity.
- Model serialization, versioned mapping storage, monitoring baselines, retraining governance, and forward post-September validation are not implemented.

The K=3 methodology is **temporally credible** and ready for naming review approval. It is **not yet productionized or production-ready**. No model artifact, serving layer, Customer Return Risk target, or API was created.

## Reproducible outputs

- [Executed temporal notebook](../../notebooks/08_segmentation_temporal_stability.ipynb)
- [Population stability figure](figures/temporal_population_stability.png)
- [Transition matrices](figures/temporal_transition_matrices.png)
- [Profile stability figure](figures/temporal_profile_stability.png)
- Aggregated CSV artifacts are under `reports/segmentation/artifacts/`.
