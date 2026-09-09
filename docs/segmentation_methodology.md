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

- final subset among core and secondary candidates;
- transformations, scaler, and weighting/balancing of feature families;
- whether exposure-adjusted rates or multiple history windows improve comparability;
- treatment of household tenure/active span in the modeling matrix;
- whether coupon sparsity is informative enough for the primary set;
- whether store concentration is behavioral or geographic/collection structure;
- clustering algorithm, number of clusters (if applicable), random-state protocol, and model-selection evidence;
- stability protocol across resamples, seeds, feature variants, and later snapshots;
- interpretability criteria, cluster naming rules, minimum viable segment size, and business-use review;
- future return-risk horizon, target, eligibility, and evaluation—explicitly outside this phase.

No clustering may begin until the preprocessing variants, redundancy decisions, stability criteria, and interpretation rubric are reviewed.
