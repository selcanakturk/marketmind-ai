# Phase 2 Segmentation Decisions

Status: Step 2 methodology selected; not productionized.

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
| Naming | deferred to review | numeric IDs are arbitrary; only neutral descriptions used |
| Production | not authorized | no serialization, assignment service, API, or monitoring contract |

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

The next authorized decision is whether to approve neutral profile descriptions for a segment-naming exercise. Productionization and Return Risk require separate phases.
