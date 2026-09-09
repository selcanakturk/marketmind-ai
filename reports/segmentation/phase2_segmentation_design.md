# Phase 2 Customer Segmentation — Step 1 Design and Empirical Audit

## Objective and dataset context

This step defines a leakage-safe, interpretable household segmentation design. It does not train a clustering model, select a cluster count, assign labels, or create a return-risk target.

Complete Journey 2.0 is a longitudinal **grocery-retail household panel**, not an e-commerce customer dataset. The authentic files contain 2,469 households, 155,848 distinct baskets, 1,469,307 transaction lines, and 68,509 transacted product IDs. Of the transaction lines, 4,836 (0.329%) have no matching row in the 92,331-row product table; left joins and an explicit `UNKNOWN` department preserve those purchases.

## Household grain

One future segmentation row represents one `household_id`. All 155,848 basket IDs map to exactly one household and one store. There are no duplicate `(basket_id, product_id)` rows, so the transaction table is a basket-product line table and not a household or basket table. Frequency is therefore the number of distinct baskets, never line count.

## Snapshot design

| Candidate T | Observed households | Excluded: <90 history days | Additional excluded: <5 baskets | Additional excluded: <30 active-span days | Eligible | Complete later months |
|---|---:|---:|---:|---:|---:|---:|
| 2017-08-31 23:59:59 | 2,430 | 56 | 152 | 3 | 2,219 | 4 |
| **2017-09-30 23:59:59** | **2,446** | **52** | **144** | **3** | **2,247** | **3** |
| 2017-10-31 23:59:59 | 2,452 | 35 | 133 | 2 | 2,282 | 2 |

The recommended T is **2017-09-30 23:59:59**. The data starts at 2017-01-01 11:53:26, so the feature history spans 273 represented calendar dates (about 272.5 elapsed days). September month-end balances depth and population coverage while reserving October–December as three complete, untouched months. That reserved period is useful for later methodology but does not freeze a return-risk window.

At T, eligible households have basket-count quartiles 18/36/66 (median 36; range 5–730), observed-history-day quartiles 257/267/270, and active-span-day quartiles 237/259/267. This is enough repeated behavior for descriptive profiling without aggressively excluding lighter shoppers.

## Eligibility

Apply sequentially: at least 90 days from first observed basket to T, at least 5 distinct baskets, and at least 30 days from first to last basket. No monetary threshold is necessary. Of 2,446 households observed by T, 2,247 are eligible and 199 are excluded: 52 for insufficient history, 144 additional for insufficient baskets, and 3 additional for insufficient span. The 23 of 2,469 full-panel households that have not appeared by T are not in the snapshot population. Raw records remain unchanged.

## RFM and behavioral definitions

- Recency: calendar days between T and the last pre-T basket date.
- Frequency: distinct pre-T basket IDs.
- Monetary value: total pre-T `sales_value` (observed net sales).
- Average basket value: mean of basket-level net sales.
- Shopping intensity: active days and active span are audited; median gap uses distinct shopping dates so two same-day baskets do not create an artificial zero gap.
- Product diversity: distinct products, distinct departments, and spend-based department HHI distinguish breadth from concentration.
- Promotion/discount behavior: discount share of reconstructed gross, discounted-basket rate, and coupon-basket rate are descriptive utilization/proxy measures. They are not evidence that promotions caused purchases.
- Brand/store: private-label spend share is reliable from product `brand`; dominant-store basket share is retained only as a secondary feature because it may encode geography or collection structure.

The detailed definitions, source columns, units, candidate transforms, and decisions are frozen in [`docs/segmentation_methodology.md`](../../docs/segmentation_methodology.md).

## Empirical distribution findings

All 15 audited candidates have 2,247 observations and zero missing values after documented construction. Selected statistics follow; ratios are proportions.

| Feature | Mean | SD | Min | P05 | P25 | Median | P75 | P95 | Max | Skew | Zero share |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| recency_days | 13.56 | 23.60 | 0 | 0 | 1 | 5 | 14 | 59 | 219 | 3.45 | 17.09% |
| basket_frequency | 51.62 | 55.38 | 5 | 7 | 18 | 36 | 66 | 145 | 730 | 3.81 | 0% |
| monetary_value | 1,504.97 | 1,540.55 | 19.13 | 133.70 | 443.56 | 1,010.84 | 2,036.62 | 4,463.62 | 17,939.63 | 2.42 | 0% |
| avg_basket_value | 31.90 | 20.52 | 2.46 | 9.36 | 17.89 | 26.99 | 40.53 | 70.59 | 196.09 | 1.91 | 0% |
| active_days | 41.84 | 34.83 | 4 | 7 | 16 | 32 | 56 | 110 | 243 | 1.79 | 0% |
| active_span_days | 243.84 | 36.38 | 42 | 164.3 | 237 | 259 | 267 | 271 | 272 | -2.18 | 0% |
| median_days_between_shops | 8.27 | 7.84 | 1 | 2 | 3.5 | 6 | 10 | 24 | 75 | 2.70 | 0% |
| unique_products | 298.66 | 237.16 | 2 | 36 | 118 | 237 | 417 | 746.4 | 1,661 | 1.41 | 0% |
| unique_departments | 10.73 | 3.42 | 2 | 5 | 8 | 11 | 13 | 16 | 20 | 0.08 | 0% |
| department_spend_hhi | 0.353 | 0.105 | 0.147 | 0.219 | 0.279 | 0.337 | 0.409 | 0.549 | 0.932 | 1.17 | 0% |
| discount_share_of_gross | 0.157 | 0.059 | 0.0003 | 0.076 | 0.116 | 0.150 | 0.190 | 0.265 | 0.480 | 0.82 | 0% |
| discounted_basket_rate | 0.843 | 0.122 | 0.154 | 0.624 | 0.784 | 0.866 | 0.927 | 1.000 | 1.000 | -1.36 | 0% |
| coupon_basket_rate | 0.061 | 0.091 | 0 | 0 | 0 | 0.027 | 0.083 | 0.241 | 0.900 | 2.77 | 38.05% |
| private_label_spend_share | 0.277 | 0.129 | 0 | 0.093 | 0.184 | 0.264 | 0.355 | 0.501 | 0.982 | 0.76 | 0.04% |
| dominant_store_basket_share | 0.739 | 0.210 | 0.111 | 0.368 | 0.571 | 0.769 | 0.933 | 1.000 | 1.000 | -0.43 | 0% |

Basket frequency, monetary value, recency, average basket value, and cadence are substantially right-skewed, supporting a future `log1p` experiment. Active span is compressed near the upper boundary because of eligibility and early panel entry. Discounted-basket rate and store concentration have ceiling mass. Coupon rate is meaningful but zero-inflated: 38.05% of households have no coupon-associated basket. No feature has near-zero variance, but bounded and zero-heavy ratios should not be blindly log transformed.

Analytical outputs:

- [Candidate feature distributions](figures/candidate_feature_distributions.png)
- [Spearman correlation heatmap](figures/candidate_feature_spearman.png)

## Redundancy findings

The strongest absolute Spearman relationships are:

| Pair | Spearman rho | Recommendation |
|---|---:|---|
| basket frequency / active days | 0.994 | Do not use both in the primary variant |
| monetary value / unique products | 0.948 | Keep as distinct constructs initially; test one-at-a-time sensitivity |
| basket frequency / median shopping gap | -0.924 | Cadence is a secondary alternative to frequency |
| active days / median shopping gap | -0.923 | Do not combine all activity proxies without weighting review |
| basket frequency / monetary value | 0.827 | Expected size/value overlap; retain initially, inspect weighting |
| unique products / unique departments | 0.827 | Test whether department breadth adds interpretation beyond products |
| monetary value / unique departments | 0.813 | Review scale-driven breadth |
| basket frequency / unique products | 0.791 | Review exposure adjustment or feature-family balancing |

There is no automatic hard-threshold removal. Next-step variants should explicitly compare a compact primary set with cadence/activity and breadth alternatives.

## Proposed core, secondary, and rejected features

Core candidates are recency, basket frequency, monetary value, average basket value, active span, unique products, unique departments, department spend HHI, discount share of gross, coupon-basket rate, and private-label spend share.

Secondary candidates are active days, median days between shops, discounted-basket rate, dominant-store basket share, and median basket value (not yet computed in the compact audit). These offer alternatives or sensitivity checks rather than extra dimensions by default.

Rejected/deferred features include raw units/items-per-basket (maximum raw quantity 89,638), active weeks/months, average gap and cadence variability, top-department share, expanded brand/manufacturer diversity, raw total/average discount, promotion exposure/response from the 20.9M-row promotion table, unique-store/diversity measures, demographics, and high-dimensional product profiles.

## Transformations and outliers

Heavy-tailed nonnegative variables should compare raw versus `log1p`; preprocessing should compare robust and standard scaling. Bounded ratios remain on interpretable scales unless diagnostics justify another treatment. Transform/scaler parameters must be fit without future snapshot information.

Extremes may be valuable heavy households. The maximum frequency (730 baskets), monetary value (17,939.63), recency (219 days), and product breadth (1,661) require case-level validation, not automatic deletion. Raw quantity extremes make unit-based features unsuitable now. Any later cap/winsorization requires a documented data-quality or leverage rationale and sensitivity analysis—not a better clustering score alone.

## Leakage protections and return-risk separation

Construction filters transactions at T before eligibility or aggregation. Frequency is distinct baskets. Full-year values, later baskets/spend/discounts/promotions, later metadata state, future-fitted normalization, and future outcomes are prohibited.

Segmentation describes historical household behavior without a target. Return Risk will predict a separately defined future outcome. It may reuse historical feature logic, but its future labels cannot influence feature selection, preprocessing, cluster selection, stability evaluation, or segment naming. The three untouched future months do not yet constitute a frozen label window.

## Open decisions before clustering

1. Approve core versus secondary variants and how to prevent correlated feature families from receiving excess weight.
2. Choose raw/`log1p` transformations and robust/standard scaling from explicit empirical variants.
3. Decide whether active span belongs in modeling or only eligibility/diagnostics.
4. Decide whether coupon sparsity and store concentration improve interpretation and stability.
5. Define resampling, seed, feature-variant, and repeated-snapshot stability criteria.
6. Define interpretability, minimum segment-size, naming, and business-use review rules.
7. Only then compare clustering families and cluster counts without forcing K.

Step 1 stops here. No clustering, K selection, supervised target, API, or application infrastructure was created.
