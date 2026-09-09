# Customer Segmentation Methodology

This document is the source of truth for MarketMind AI Customer Segmentation. It defines Phase 2 Step 1 only: household grain, point-in-time construction, eligibility, candidate features, and review policy. It does **not** claim that clusters, personas, or a final feature matrix exist.

## Frozen decisions

### Objective and unit

The objective is to discover statistically defensible, reasonably stable, interpretable groupings of purchasing behavior for business analysis. Optimizing a clustering score or forcing a preferred persona count is not the objective.

The segmentation entity is a **grocery-retail household** identified by `household_id` in Complete Journey 2.0. One future segmentation row represents one household—not an individual e-commerce customer, basket, transaction line, or product.

The audited data contains 2,469 households, 155,848 baskets, and 1,469,307 transaction lines. Every basket maps to exactly one household and one store; `(basket_id, product_id)` is unique. A basket may contain many transaction lines/products.

### Point-in-time snapshot

The primary snapshot is **2017-09-30 23:59:59**. Every feature and eligibility input must use transactions at or before this timestamp. The source begins at 2017-01-01 11:53:26, giving 273 represented calendar dates (about 272.5 elapsed days) and leaving the three complete calendar months October–December untouched. The incomplete 2018-01-01 boundary is not part of the feature history or the reserved complete-month period.

This month-end was selected from calendar coverage and observation-depth evidence, not clustering performance. The same construction contract must support later repeated snapshots.

### Eligibility

Filters are deterministic and sequential:

1. at least 90 calendar days from the household's first observed basket to the snapshot;
2. at least 5 distinct baskets by the snapshot;
3. at least 30 calendar days between first and last observed basket.

No minimum-spend filter is used. At the primary snapshot, 2,446 households have appeared; 52 fail observed history, 144 additional households fail basket count, and 3 additional households fail active span. The eligible population is 2,247 (91.86% of observed households); 199 are excluded from this snapshot, not deleted from source data. The 23 households not yet observed by the snapshot are outside its at-risk population rather than “excluded.”

### Feature semantics

All features use distinct baskets where basket behavior is intended. Transaction rows are never substituted for frequency. Source `sales_value` is treated as observed net sales; gross value is `sales_value + retail_disc + coupon_disc + coupon_match_disc`, because the audited discount fields are nonnegative amounts. Product metadata is left joined and missing departments are assigned an explicit `UNKNOWN` bucket.

The compact audited candidate set is:

| Feature | Exact definition | Source | Unit | Snapshot-safe | Interpretation | Candidate transform | Redundancy concern | Status |
|---|---|---|---|---|---|---|---|---|
| `recency_days` | Calendar days from last basket date to T | transactions | days | Yes | current engagement | `log1p` candidate | cadence | Core candidate |
| `basket_frequency` | Distinct baskets through T | transactions | baskets | Yes | shopping frequency | `log1p` candidate | active days, cadence | Core candidate |
| `monetary_value` | Sum of net `sales_value` through T | transactions | source currency | Yes | observed value | `log1p` candidate | products, frequency | Core candidate |
| `avg_basket_value` | Mean basket-level net sales | transactions | source currency/basket | Yes | trip value | `log1p` candidate | monetary | Core candidate |
| `active_days` | Distinct calendar dates containing a basket | transactions | days | Yes | repeat activity | `log1p` candidate | frequency (very high) | Secondary candidate |
| `active_span_days` | Calendar days between first and last basket | transactions | days | Yes | observation/activity span | review distribution | eligibility/history | Core candidate |
| `median_days_between_shops` | Median gap between distinct shopping dates | transactions | days | Yes | shopping cadence | `log1p` candidate | frequency (very high) | Secondary candidate |
| `unique_products` | Distinct purchased product IDs | transactions | products | Yes | assortment breadth | `log1p` candidate | monetary, departments | Core candidate |
| `unique_departments` | Distinct departments, including `UNKNOWN` if used | transactions + products | departments | Yes | broad category reach | none/standard candidate | products | Core candidate |
| `department_spend_hhi` | Sum of squared department shares of net spend | transactions + products | ratio [0,1] | Yes | category concentration | bounded/robust review | top-department share | Core candidate |
| `discount_share_of_gross` | Total discounts / (net sales + discounts) | transactions | ratio [0,1] | Yes | discount utilization intensity | bounded/robust review | discounted-basket rate | Core candidate |
| `discounted_basket_rate` | Share of baskets with any recorded discount | transactions | ratio [0,1] | Yes | discount-associated trips | bounded/robust review | discount share | Secondary candidate |
| `coupon_basket_rate` | Share of baskets with coupon or match discount | transactions | ratio [0,1] | Yes | coupon utilization | zero-aware review | discount measures | Core candidate |
| `private_label_spend_share` | Private-brand net sales / total net sales | transactions + products | ratio [0,1] | Yes | private-label preference | bounded/robust review | brand measures | Core candidate |
| `dominant_store_basket_share` | Largest store basket count / all baskets | transactions | ratio [0,1] | Yes | store concentration proxy | bounded/robust review | geography/collection | Secondary candidate |

“Core candidate” means proceed to preprocessing review, not guaranteed inclusion. “Secondary candidate” means retain for sensitivity analysis. No final transformations or scaling are frozen.

### Rejected and deferred candidates

- Total units and items-per-basket are **problematic/rejected for initial modeling**: `quantity` is available but has a maximum of 89,638 and likely mixes count conventions or weighted-item encodings.
- Active weeks and active months are derivable but rejected initially as coarser duplicates of frequency/active days.
- Average inter-basket gap and cadence variability are derivable but deferred; irregular observation and same-day trips complicate interpretation. Median shopping-day gap is more robust.
- Median basket value is derivable and a secondary audit candidate, but average basket value is retained initially to keep the matrix compact.
- Top-department share is derivable but rejected as a near-conceptual duplicate of department HHI.
- Product entropy, brand/manufacturer diversity, top-brand concentration, and high-dimensional product/category profiles are derivable but deferred to avoid redundant or sparse preference dimensions.
- Total discount and average discount per basket are derivable but rejected initially because they largely encode shopping volume. Normalized discount measures are preferred.
- Promotion exposure/response features need the 20.9M-row promotions table and careful exposure semantics; they are deferred. No causal promotion claims are permitted.
- Unique stores and store diversity are derivable but rejected initially because they may primarily encode geography or panel collection. Dominant-store share remains secondary only.
- Demographic features are rejected from behavioral clustering because coverage is only 801 of 2,469 households and they change the construct being segmented.

### Quality, redundancy, transformations, and outliers

Before clustering, candidate features must be reviewed using missingness, quantiles, skewness, zero share, near-zero variance, Spearman/Pearson relationships, and conceptual overlap. A correlation threshold is a diagnostic, not an automatic deletion rule. Highly redundant alternatives must be tested in small, named feature-set variants rather than jointly overweighting one behavioral dimension.

Nonnegative heavy-tailed counts and amounts may use `log1p`; bounded ratios should not be transformed blindly. Robust scaling and standard scaling remain candidates and must be fit on the analysis population for each snapshot/experiment—never using later snapshots. Final transformation and scaling choices precede clustering but are not made in Step 1.

High-value and high-frequency households are not errors by definition. Extremes must be traced to source lines, basket aggregation, unusual quantity encodings, and product joins. Prefer robust transformations/scaling. Capping or winsorization requires documented evidence of error or undue estimator leverage and a sensitivity comparison; it may not be used merely to improve a clustering score.

### Leakage checklist

For every snapshot and experiment verify that:

- no basket, spend, discount, promotion activity, or metadata state after T enters a feature;
- no full-year aggregate is used when T is earlier;
- eligibility uses only information available by T;
- preprocessing parameters are not fit with future snapshots or reserved periods;
- future return/no-return outcomes do not define, tune, select, name, or validate clusters;
- any repeated-snapshot analysis preserves point-in-time joins and independently fit preprocessing where required.

Customer Segmentation is unsupervised descriptive grouping. Customer Return Risk is a later supervised prediction problem using future outcomes. They may share leakage-safe historical features, but the future target is forbidden from segmentation construction. Any later segment label used as return-risk context must itself be generated with a documented point-in-time-safe pipeline.

## Open / experimental decisions

- whether exposure-adjusted rates or multiple history windows improve comparability;
- subsample and seasonally comparable second-year stability beyond the completed seed/month-end checks;
- stakeholder approval of display names and descriptions;
- production artifact/version schema, new-model semantic remapping governance, and monitoring baselines;
- whether assignment remains reliable beyond September with cumulative magnitude features;
- future return-risk horizon, target, eligibility, and evaluation—explicitly outside this phase.

These questions do not reopen the frozen Step 2 algorithm, K, feature, transform, or scaling decisions without a separately authorized methodology review.

## Step 2 frozen experiment decisions

The first clustering experiment reconstructed the same 2,247-household snapshot and froze the following **before** comparing algorithm metrics.

- Final clustering features, in deterministic order: `recency_days`, `basket_frequency`, `monetary_value`, `avg_basket_value`, `unique_departments`, `department_spend_hhi`, `discount_share_of_gross`, `coupon_basket_rate`, and `private_label_spend_share`.
- `log1p` transformations: recency, basket frequency, monetary value, and average basket value.
- Unchanged features: unique departments and the four naturally bounded ratios.
- Scaling: `RobustScaler`, fit only on the frozen eligible snapshot. Legitimate extremes remain included.
- Algorithms: KMeans and full-covariance GaussianMixture only.
- Cluster-count range: K=2 through K=8, without post-result expansion.
- Base fit: random state 42; KMeans uses 20 initializations and GMM uses 5.
- Stability: ten deterministic seed refits per algorithm/K and all 45 pairwise Adjusted Rand Indices. ARI handles label permutation.
- Selection policy, in order: stability, separation, non-pathological sizes, behavioral interpretability, and operational simplicity. No single metric decides.
- PCA is visualization-only; clustering is performed in the nine-dimensional transformed and scaled space.

The following were excluded from the first comparison for predeclared conceptual reasons: `active_days` and median cadence duplicate frequency; `active_span_days` is boundary-compressed and partly reflects tenure/eligibility; `unique_products` is strongly entangled with monetary value; discounted-basket rate has ceiling mass and overlaps normalized discount intensity; dominant-store share may encode geography or panel structure; median basket value adds another trip-size proxy.

## Step 2 selected research solution

The selected methodology candidate is **KMeans with K=3**. It has the best KMeans silhouette (0.20313) and Davies–Bouldin value (1.56473), near-perfect seed stability (mean pairwise ARI 0.99378; minimum 0.98808), and cluster shares of 13.04%, 47.93%, and 39.03%. K=2 has a slightly higher Calinski–Harabasz score but weaker silhouette and Davies–Bouldin separation. K>=4 loses separation; K=8 creates a 2.98% group and is materially less stable.

GMM K=3 is also highly seed-stable (mean ARI 0.99943) with non-small components, but its hard-assignment silhouette is only 0.09889. GMM AIC keeps decreasing through K=8 and BIC reaches its minimum at K=7, while separation turns near-zero/negative and stability falls from K=4 onward. Information criteria therefore do not override the full selection policy. KMeans-3 is preferred for stronger separation and simpler operation.

Cluster numbers are arbitrary identifiers. Current descriptions are deliberately neutral: a promotion/coupon-associated larger-basket group; a frequent, high-spend, broad-assortment group; and a lower-frequency, lower-spend, narrower-assortment group. Business-friendly naming remains a separate review step. KMeans centroid distance is not a probability; GMM posterior responsibility is assignment under mixture assumptions, not customer confidence.

At the end of Step 2, the clustering methodology was ready for temporal and naming review but was **not productionized**. Step 3 below records the later temporal evidence and semantic contract. Customer Return Risk remains out of scope.

## Step 3 temporal and semantic decisions

Independent fits at 2017-06-30, 2017-07-31, 2017-08-31, and 2017-09-30 preserve the frozen methodology. Eligible populations are 2,085, 2,172, 2,219, and 2,247. Silhouette remains 0.2031–0.2069, no aligned segment collapses, and 90.38%–90.67% of common households remain in the same aligned segment month to month. The predeclared temporal-credibility policy is satisfied.

Cluster identity alignment uses snapshot-relative median profiles across the nine frozen original-unit features: subtract the snapshot household median, divide by snapshot IQR, calculate Euclidean cluster-profile distances to the September reference, and solve one-to-one matching with Hungarian assignment. Raw integer IDs must never be compared or exposed as stable semantics without this versioned mapping.

The approved semantic codes and display names are:

- `HIGH_ENGAGEMENT_BROAD` — **High-Engagement Broad Shoppers**;
- `PROMOTION_BASKET_BUILDERS` — **Promotion-Oriented Basket Builders**;
- `LOWER_ENGAGEMENT_FOCUSED` — **Lower-Engagement Focused Shoppers**.

Semantic identity is derived from behavioral profiles, not integer order. Names describe observed shopping behavior and do not imply loyalty, profitability, risk, causal promotion response, or individual-customer identity.

An eligible household is assigned by frozen ordered feature construction, frozen transformations, the already-fitted RobustScaler, and nearest frozen KMeans centroid. The resulting raw cluster ID is mapped through a model-versioned semantic mapping. `distance_to_centroid` is a geometric atypicality diagnostic, not probability or confidence.

Any household failing ≥90 history days, ≥5 baskets, or ≥30 active-span days receives `insufficient_history`. This is an eligibility status, not a fourth learned segment.

The recommended operating policy is monthly month-end eligibility/assignment, quarterly model review after deployment, and evidence-triggered rather than automatic refitting. Monitoring must cover feature quantiles, eligible/ineligible share, semantic segment shares, aligned profile/centroid movement, assignment-distance distributions, and preservation of defining profile orderings. Thresholds remain open until a production baseline and business tolerances exist.

Step 3 establishes temporal credibility and a semantic/assignment contract; it does not authorize or complete productionization. Serialization, versioned mapping artifacts, post-September forward validation, monitoring baselines, and governance remain open. Customer Return Risk remains separate.

## Step 4 production engine

Model version `segmentation-kmeans3-2017-09-v1` implements the frozen methodology as a self-contained joblib bundle. It contains the fitted RobustScaler and KMeans-3 estimator, ordered feature and transformation schemas, eligibility policy, explicit raw-ID-to-semantic mapping, reference snapshot/profiles, parameters, and library versions. Training and assignment do not depend on notebook state.

The canonical CLI build must reproduce 2,247 eligible households, raw cluster counts 293/1,077/877, and the three frozen internal metrics within floating-point tolerance or fail. Semantic mapping is re-derived from reference profiles and must uniquely resolve all three approved codes.

Production assignment validates raw input, reconstructs point-in-time features and eligibility, calls only the fitted scaler's `transform` and KMeans `predict`, and returns the frozen seven-field assignment schema. Ineligible households retain null assignments with `insufficient_history`. No fourth cluster or confidence/probability surrogate is permitted.

The lightweight monitoring baseline freezes reference feature quartiles, segment shares/profiles, centroid-distance quantiles, and eligibility proportions without inventing alert thresholds. Refit remains review-controlled and evidence-triggered. The engine is ready for a later serving layer, but FastAPI and Customer Return Risk remain outside Phase 2 Step 4.
