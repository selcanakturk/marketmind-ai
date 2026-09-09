# Phase 2 Customer Segmentation — Clustering Experiments

## Frozen snapshot and eligibility

The experiment rebuilt the frozen Complete Journey grocery-household snapshot at **2017-09-30 23:59:59** with the existing point-in-time utility. It contains exactly 2,247 unique eligible households, one row per `household_id`, with no missing clustering features. No post-snapshot transaction, return-risk outcome, or future-fitted preprocessing was used.

Eligibility remains: at least 90 observed-history days, 5 distinct baskets, and 30 active-span days. No monetary threshold applies.

## Final feature set and redundancy control

The feature set was frozen before metric comparison:

| Dimension | Retained features | Reason |
|---|---|---|
| Engagement | recency days; basket frequency | current engagement and repeated trips without duplicate cadence proxies |
| Value | monetary value; average basket value | total observed value and trip size |
| Diversity | unique departments; department-spend HHI | breadth and concentration at an interpretable hierarchy |
| Promotion | discount share of gross; coupon-basket rate | normalized discount intensity and distinct coupon behavior |
| Brand tendency | private-label spend share | reliable, bounded preference measure |

Predeclared exclusions were active days and median shopping gap (near-duplicates of frequency), active span (boundary-compressed tenure/eligibility proxy), unique products (Spearman 0.948 with monetary), discounted-basket rate (ceiling mass and discount overlap), dominant-store share (geography/collection ambiguity), and median basket value (extra trip-size proxy). Selection was conceptual and distribution-based—not chosen from silhouette results.

## Transformations and scaling

`log1p` was applied to recency, basket frequency, monetary value, and average basket value. Unique departments and bounded HHI/discount/coupon/private-label ratios were unchanged. `RobustScaler` was frozen as the primary policy because legitimate heavy shoppers remain and the magnitude features are heavy-tailed. The scaler was fit only on this eligible snapshot.

## Outlier review

No exact transaction duplicates or duplicate `(basket_id, product_id)` lines were found. Extremes form internally coherent shopping records rather than isolated malformed rows:

- household 2337 has 730 baskets across 243 active days, 6,254.23 spend, and 1,066 products;
- household 1023 has the highest spend (17,939.63), 285 baskets, 168 active days, and 865 products;
- household 973 has the highest average basket value (196.09), supported by 36 baskets and 1,000 products;
- household 1453 has the widest product assortment (1,661), 370 baskets, and 9,727.74 spend.

These appear to be plausible heavy or large-trip panel households. None were deleted or capped. `log1p` and robust scaling limit their leverage. The earlier raw-quantity anomaly remains the reason unit features are absent.

## Candidate algorithms, K range, and validation

Exactly KMeans and full-covariance GaussianMixture were evaluated for K=2–8. Base fits use seed 42, KMeans `n_init=20`, and GMM `n_init=5`. Stability is all-pairs ARI across ten deterministic seed refits (45 comparisons per algorithm/K).

### KMeans

| K | Silhouette ↑ | Davies–Bouldin ↓ | Calinski–Harabasz ↑ | Mean ARI | Min ARI | Cluster counts | Minimum share |
|---:|---:|---:|---:|---:|---:|---|---:|
| 2 | 0.1931 | 1.8129 | 581.10 | 0.9932 | 0.9876 | 1,027 / 1,220 | 45.71% |
| **3** | **0.2031** | **1.5647** | 559.69 | **0.9938** | **0.9881** | 293 / 1,077 / 877 | 13.04% |
| 4 | 0.1382 | 1.8301 | 466.34 | 0.9864 | 0.9528 | 758 / 504 / 748 / 237 | 10.55% |
| 5 | 0.1325 | 1.8835 | 414.03 | 0.8760 | 0.7650 | 636 / 485 / 210 / 607 / 309 | 9.35% |
| 6 | 0.1360 | 1.7223 | 380.72 | 0.9426 | 0.8438 | 388 / 394 / 541 / 190 / 538 / 196 | 8.46% |
| 7 | 0.1280 | 1.7135 | 352.66 | 0.9039 | 0.7088 | 157 / 453 / 283 / 459 / 329 / 170 / 396 | 6.99% |
| 8 | 0.1249 | 1.6818 | 329.94 | 0.7622 | 0.6187 | 360 / 398 / 309 / 223 / 180 / 231 / 479 / 67 | 2.98% |

K=3 leads KMeans on silhouette and Davies–Bouldin while retaining near-perfect stability. K=2 leads Calinski–Harabasz, illustrating why no single metric controls the decision. K>=4 has lower separation; K=8 adds a small 67-household group and weaker stability.

### GaussianMixture

| K | BIC ↓ | AIC ↓ | Hard silhouette ↑ | Mean ARI | Min ARI | Component counts | Minimum share |
|---:|---:|---:|---:|---:|---:|---|---:|
| 2 | 21,100.55 | 20,477.36 | 0.1731 | 0.9992 | 0.9982 | 1,533 / 714 | 31.78% |
| **3** | 11,277.04 | 10,339.39 | 0.0989 | **0.9994** | **0.9988** | 484 / 917 / 846 | 21.54% |
| 4 | 10,663.89 | 9,411.79 | 0.1147 | 0.9162 | 0.7179 | 129 / 890 / 825 / 403 | 5.74% |
| 5 | 10,146.60 | 8,580.04 | 0.0581 | 0.7400 | 0.6402 | 470 / 572 / 118 / 826 / 261 | 5.25% |
| 6 | 9,507.17 | 7,626.16 | -0.0062 | 0.7256 | 0.4639 | 836 / 128 / 194 / 193 / 437 / 459 | 5.70% |
| 7 | **9,360.45** | 7,164.99 | -0.0018 | 0.6832 | 0.4525 | 490 / 823 / 354 / 128 / 84 / 186 / 182 | 3.74% |
| 8 | 9,482.86 | **6,972.94** | 0.0208 | 0.6489 | 0.4501 | 134 / 458 / 115 / 225 / 728 / 300 / 220 / 67 | 2.98% |

BIC favors K=7 and AIC K=8, but those solutions have near-zero hard-assignment silhouette, materially lower stability, and small components. GMM K=3 is the serious stable comparison. Its median maximum responsibility is 0.9964, tenth percentile 0.9083, and 1.34% fall below 0.60; these measure assignment ambiguity under the fitted mixture model, not customer confidence.

## Candidate profiles in original units

### Selected KMeans K=3

Cluster numbers are arbitrary and are not names.

| Cluster | Households | Share | Median recency | Baskets | Spend | Avg basket | Products | Departments | Dept HHI | Discount share | Coupon-basket rate | Private-label share |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 293 | 13.04% | 5 | 34 | 1,412.95 | 43.32 | 323 | 11 | 0.349 | 19.47% | 21.43% | 23.96% |
| 1 | 1,077 | 47.93% | 2 | 61 | 1,830.30 | 30.01 | 380 | 13 | 0.309 | 14.10% | 3.20% | 27.89% |
| 2 | 877 | 39.03% | 13 | 17 | 378.33 | 19.65 | 99 | 8 | 0.376 | 15.01% | 0.00% | 25.92% |

Neutral descriptions supported by the medians are:

- cluster 0: moderate-frequency, larger-basket households with the strongest discount/coupon association;
- cluster 1: recent, frequent, high-spend, broad-assortment households with lower category concentration;
- cluster 2: less-recent, lower-frequency, lower-spend, narrower-assortment households with no median coupon use.

The overall assigned-centroid distance median is 1.688 scaled units and P95 is 2.898. Cluster-specific P95 values are 3.595, 2.389, and 3.242. These are atypicality diagnostics, not probabilities.

GMM K=3 yields related size/value gradients but separates the promotion-associated behavior less clearly: component median coupon rates are 14.29%, 4.76%, and 0%. Its hard silhouette is less than half KMeans-3's.

## PCA visualization

PCA was used only to display KMeans-3. PC1 explains 32.09% and PC2 22.66% (54.75% combined). Clustering was not performed in PCA space, and axes are not treated as segments.

## KMeans versus GMM and selection decision

The predeclared preference order was stability, separation, sensible sizes, behavioral interpretability, then operational simplicity. **KMeans K=3 is selected as the research methodology candidate.** It combines near-perfect stability with the best KMeans silhouette/DB scores, no pathological group size, a clear promotion-associated subgroup and engagement/value gradient, and a simpler assignment contract than full-covariance GMM.

GMM K=3 is marginally more seed-stable but substantially weaker on hard separation. Higher-component GMM solutions illustrate a conflict between likelihood criteria and usable, stable behavioral partitions; the selection policy resolves that conflict against them.

## Analytical outputs

- [Internal metrics by K](figures/clustering_metrics_by_k.png)
- [Stability by K](figures/clustering_stability_by_k.png)
- [KMeans-3 PCA display](figures/kmeans_k3_pca.png)
- [KMeans-3 profile heatmap](figures/kmeans_k3_profile_heatmap.png)
- [Reproducible executed notebook](../../notebooks/07_segmentation_clustering_experiments.ipynb)

## Known limitations and remaining work

- Internal validity does not establish causal, commercial, or demographic meaning.
- Seed stability is strong, but temporal/repeated-snapshot and subsample stability remain to be tested before productionization.
- The single household panel may reflect retailer coverage and enrollment effects.
- Cluster 0's larger centroid distances merit later case review and monitoring design.
- Business-friendly names, naming governance, minimum operating sizes, new-household handling, assignment/retraining cadence, drift monitoring, and versioned artifacts remain open.
- No final customer-facing segment labels or production model were created. Customer Return Risk remains separate and untouched.
