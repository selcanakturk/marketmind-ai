# Phase 2 Segmentation Decisions

Status: Step 3 temporal stability and naming review complete; not productionized.

| Decision | Frozen outcome | Evidence / boundary |
|---|---|---|
| Snapshot | 2017-09-30 23:59:59 | 2,247 eligible households; no later behavior |
| Feature set | 9 ordered features | balanced behavioral families; redundant proxies excluded before scoring |
| Transform | `log1p` recency, frequency, monetary, average basket value | Step 1 skew evidence |
| Scaling | RobustScaler | preserves heavy households while limiting leverage |
| Algorithms evaluated | KMeans; full-covariance GMM | predeclared only |
| K range | 2–8 | unchanged after results |
| Stability | ten seeds; 45 pairwise ARIs per algorithm/K | label-permutation safe |
| Selected research solution | KMeans K=3 | best balance under frozen multi-criterion policy |
| Naming | semantic names defined in Step 3 | numeric IDs remain arbitrary and version-specific |
| Production | not authorized | operational principles defined; no serialization, serving, or monitoring implementation |

## Frozen feature order

1. `recency_days` — `log1p`
2. `basket_frequency` — `log1p`
3. `monetary_value` — `log1p`
4. `avg_basket_value` — `log1p`
5. `unique_departments` — unchanged
6. `department_spend_hhi` — unchanged
7. `discount_share_of_gross` — unchanged
8. `coupon_basket_rate` — unchanged
9. `private_label_spend_share` — unchanged

## Selection record

KMeans-3: silhouette 0.20313, Davies–Bouldin 1.56473, Calinski–Harabasz 559.69, mean/min seed ARI 0.99378/0.98808, sizes 293/1,077/877.

GMM-3: hard silhouette 0.09889, BIC 11,277.04, AIC 10,339.39, mean/min seed ARI 0.99943/0.99879, sizes 484/917/846.

KMeans-3 wins because the small stability advantage for GMM-3 does not offset KMeans-3's stronger separation, clearer behavioral profiles, and lower operational complexity. Likelihood improvements at higher GMM K conflict with declining separation and seed stability and therefore do not control selection.

## Step 3 temporal evidence

The frozen KMeans-3 methodology was independently refit at June, July, August, and September month ends with unchanged eligibility, features, transformations, scaling, and parameters. Eligible counts were 2,085, 2,172, 2,219, and 2,247. Silhouette remained 0.2031–0.2069; Davies–Bouldin remained 1.5302–1.5746. Aligned segment shares remained non-pathological, and 90.38%–90.67% of common households retained their semantic segment month to month. Consecutive ARI was 0.7001–0.7175 and is interpreted as combined behavior/geometry movement, not seed instability.

KMeans K=3 remains frozen and is considered temporally credible for this panel period.

## Frozen semantic mapping for the September research model

| Raw ID | Segment code | Display name |
|---:|---|---|
| 1 | `HIGH_ENGAGEMENT_BROAD` | High-Engagement Broad Shoppers |
| 0 | `PROMOTION_BASKET_BUILDERS` | Promotion-Oriented Basket Builders |
| 2 | `LOWER_ENGAGEMENT_FOCUSED` | Lower-Engagement Focused Shoppers |

Raw IDs are model-version-specific. Semantic mapping is derived from profiles: highest frequency identifies high engagement; highest coupon use among remaining profiles identifies promotion-oriented; the remaining profile is lower engagement/focused. Names do not imply profitability, loyalty, risk, or causality.

## Frozen operational contract principles

- Ineligible households receive `insufficient_history`, not a fourth segment.
- Eligible assignment uses frozen ordered features → frozen transforms → fitted RobustScaler → nearest KMeans centroid → versioned semantic mapping.
- Output includes household/snapshot/model version, raw ID, semantic code/name, eligibility status, and centroid distance.
- Centroid distance is geometric atypicality, never probability or confidence.
- Reassess eligibility and assignment monthly at calendar month-end.
- Review the model quarterly once deployed; refit only after sustained multi-signal drift or semantic deterioration, not automatically by calendar.
- Monitor feature distributions, segment shares, centroid/profile movement, assignment-distance distributions, eligibility rates, and semantic ordering.

Productionization still requires model serialization/versioning, mapping persistence, forward validation, monitoring baselines, and governance. Customer Return Risk remains a separate future phase.
