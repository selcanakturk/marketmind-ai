# Complete Journey 2.0 Dataset Audit

## Dataset Identity

This audit uses **84.51° Complete Journey 2.0 as distributed by the `completejourney` R package, version 1.1.1**. It does not use the older/differently packaged 2,500-household, 102-week dunnhumby CSV release.

- **Canonical origin:** [84.51° Area 51](https://www.8451.com/area51/)
- **Distribution and schema:** [`bradleyboehmke/completejourney`](https://github.com/bradleyboehmke/completejourney) and [package user guide](https://bradleyboehmke.github.io/completejourney/articles/completejourney.html)
- **License:** CC0 for package version 1.1.1
- **Context:** one year of grocery-retail purchasing by 2,469 frequent-shopper households. It is not e-commerce behavior and must not be presented as such.

The package distribution introduces analysis-oriented transformations relative to 84.51° source files: normalized snake-case field/table names, categorical representations, parsed dates/timestamps, and normalized table objects. It embeds samples of the two largest tables but exposes their full normalized RDS files in the source repository. This audit downloaded and inspected the full tables, not the samples.

Files inspected under `data/raw/complete_journey/`:

- `campaign_descriptions.rda`
- `campaigns.rda`
- `coupon_redemptions.rda`
- `coupons.rda`
- `demographics.rda`
- `products.rda`
- `promotions.rds`
- `transactions.rds`

Raw compressed size is **37.16 MB**. Files remain unchanged and Git-ignored.

## Dataset Integrity

| Table | Rows | Columns | Deep Pandas memory | Exact duplicates | Key observation |
|---|---:|---:|---:|---:|---|
| campaign descriptions | 27 | 4 | 0.004 MB | 0 | `campaign_id` unique |
| campaigns | 6,589 | 2 | 0.65 MB | 0 | household-campaign pair unique |
| coupon redemptions | 2,102 | 4 | 0.41 MB | 0 | household/coupon/campaign/date unique |
| coupons | 116,204 | 3 | 18.47 MB | 4,872 | proposed coupon/product/campaign key has 6,495 duplicated rows |
| demographics | 801 | 8 | 0.05 MB | 0 | `household_id` unique |
| products | 92,331 | 7 | 30.23 MB | 0 | `product_id` unique |
| promotions | 20,940,529 | 5 | 2,275.58 MB | 0 | product/store/week alone has 25,570 duplicated rows with different placement states |
| transactions | 1,469,307 | 11 | 381.72 MB | 0 | basket/product pair unique |

All transaction fields are complete. Product metadata have 540 missing categories (0.585%), 528 missing product types (0.572%), and 30,586 missing package sizes (33.126%). Demographics cover only 801 households; within that table, home ownership is missing for 233 (29.089%) and marital status for 137 (17.104%).

Coupon duplicates should not be deleted automatically: they may reflect distribution-source duplication or business semantics not represented in the candidate key. Promotion records are uniquely described by the full placement state; product/store/week is not a unique grain.

## Relational Structure

Observed grains:

- transactions: one product line within a basket
- products: one product
- demographics: one household with available demographics
- campaigns: one household-campaign assignment
- campaign descriptions: one campaign
- coupons: coupon-product-campaign eligibility rows, including observed duplicates
- coupon redemptions: one household coupon-redemption record
- promotions: product-store-week placement state; multiple placement states can exist for one product/store/week

There are 155,848 unique baskets. No basket links to multiple households or multiple stores. Campaign households, demographic households, redemption households, campaign IDs, promotion products, and promotion stores all match their expected parent domains.

Data-quality exceptions:

- **4,836 transaction lines reference product IDs absent from the product table.** Product metadata joins therefore need a left join and an explicit unknown-product treatment.
- **16 coupon rows reference product IDs absent from the product table.**
- Coupon candidate-key duplication and multi-state promotion keys make direct joins capable of row multiplication.

A transaction→product join is many-to-one for matched products and should retain 1,469,307 rows. Promotions should be filtered/aggregated at the required product-store-week cutoff before joining. Coupons and redemptions similarly require purpose-specific aggregation; no giant denormalized frame is justified.

## Temporal Coverage

- **Earliest transaction:** 2017-01-01 11:53:26
- **Latest transaction:** 2018-01-01 04:01:20
- **Endpoint difference:** 364 days
- **Weeks present:** 53
- **Missing transaction timestamps:** 0
- **Weeks with zero baskets inside the observed range:** 0

Monthly baskets are stable through the twelve complete 2017 months, ranging from 11,787 in February to 13,754 in July. The 86 baskets dated 2018-01-01 form an incomplete terminal day/month, not a comparable January period. The opening timestamp also begins partway through 2017-01-01, so both exact boundary days are partial even though the 2017 monthly coverage is otherwise continuous.

Household entry is highly concentrated: 1,982 of 2,469 households (80.28%) first appear in January 2017. This is consistent with a selected frequent-shopper panel rather than ordinary customer acquisition data.

## Customer Purchase Depth

Purchase frequency is measured at distinct `basket_id`, not product-line level.

| Measure | Result |
|---|---:|
| Households | 2,469 |
| Distinct baskets | 155,848 |
| Exactly 1 basket | 1.2556% (31 households) |
| At least 2 baskets | 98.7444% |
| At least 5 baskets | 95.1397% |
| At least 10 baskets | 88.5379% |
| Median baskets per household | 43 |
| Mean baskets per household | 63.12 |
| Maximum baskets | 780 |

This is fundamentally different from Olist: Complete Journey contains substantial repeated purchase behavior for nearly the entire panel.

## Inter-Purchase Behavior

Across **153,379 consecutive household-basket intervals**:

| Statistic | Days |
|---|---:|
| Mean | 5.118 |
| 25th percentile | 0.879 |
| Median | 2.210 |
| 75th percentile | 5.813 |
| 90th percentile | 11.539 |
| 95th percentile | 18.069 |
| 99th percentile | 45.952 |
| Maximum | 330.763 |

There are 84 identical timestamps and 45,742 intervals under one day (29.823%). In grocery data, multiple same/near-day baskets may represent distinct store trips, split checkout occasions, or data conventions. They remain documented rather than automatically merged. The overall cadence is frequent, but no interval is used to define inactivity or churn.

## Observation Depth

| Household descriptor | Median | Mean | 10th percentile | 90th percentile |
|---|---:|---:|---:|---:|
| Baskets | 43 | 63.12 | 9 | 137 |
| Active span (days) | 348 | 317.45 | 227 | 362 |
| Active weeks | 28 | 28.20 | 7 | 49 |
| Active months | 11 | 9.90 | 5 | 12 |
| Baskets per active month | 4.0 | 5.68 | 1.56 | 11.58 |
| Follow-up from first purchase (days) | 358 | 338.96 | 293 | 364 |

Additional feasibility indicators:

- 96.7598% of households have an observed active span of at least 90 days.
- 88.8619% are active in at least six distinct months.
- 88.5379% have at least ten baskets.
- Demographics cover 32.4423% of purchasing households.

These depths can support repeated historical snapshots for many households, although the frequent-shopper selection means results would not generalize automatically to new or occasional customers.

## Right-Censoring

First-purchase cohorts show declining follow-up:

| Entry cohort | Households | Repeat observed | ≥5 baskets observed | Median follow-up |
|---|---:|---:|---:|---:|
| 2017-01 | 1,982 | 99.80% | 98.94% | 360 days |
| 2017-04 | 47 | 97.87% | 80.85% | 264 days |
| 2017-07 | 21 | 90.48% | 61.90% | 171 days |
| 2017-09 | 16 | 93.75% | 31.25% | 113 days |
| 2017-11 | 11 | 63.64% | 18.18% | 53 days |
| 2017-12 | 6 | 66.67% | 0% | 18 days |

Late cohorts are tiny and censored. They cannot support arbitrary future horizons. A later supervised design could use snapshots only where the complete chosen future horizon exists, and could obtain multiple temporal cohorts from established households. The horizon and eligibility rules remain deliberately undefined.

## Return-Risk Feasibility

A future supervised formulation of “features known at snapshot T → purchase again during future H” appears empirically feasible because:

- household identity is persistent;
- purchase cadence is frequent and deeply repeated;
- most households span much of the year;
- multiple historical snapshot dates could be constructed;
- basket/product/value/discount/store history is available before T.

Important constraints remain:

- the dataset contains no contractual closure/churn event;
- H must follow cadence and operational-purpose analysis, not an arbitrary threshold;
- only snapshots with a complete future window can be eligible;
- repeated snapshots from the same household are dependent and require household-aware/temporal evaluation;
- the source is a preselected frequent-shopper panel, so it underrepresents genuinely new, light, or already-lost customers;
- campaign/promotion information must be available by T and cannot be interpreted causally from observational associations.

The defensible term is **household/customer return risk**, not churn. Feasibility is strong for a future return-risk experiment, but target validity is not yet established and no label is created here.

## Segmentation Feasibility

The following are derivable with cutoff-safe aggregation: recency, basket frequency, monetary value, average basket value, basket size, unique products, categories/departments, brand diversity, discount and coupon usage, store diversity, purchase cadence, and active span.

- **Promotion sensitivity — Problematic:** placement exposure joins are product-store-week and observational. “Sensitivity” needs a careful descriptive definition and cannot be described causally.
- **Demographics — Problematic:** only 32.44% coverage, with further missing fields and sensitive/coarse categories. Their purpose and fairness implications need review.
- **Views/cart behavior — Unavailable.**
- **Inventory — Unavailable.**

Complete Journey offers unusually rich behavioral segmentation because the median household has 43 baskets, 277 distinct purchased products, and 11 active months. Every predictive or temporal use must compute features using data known by snapshot T; full-year recency or active span would leak future behavior into earlier snapshots.

### Empirical comparison with Olist

| Dimension | Complete Journey 2.0 | Olist |
|---|---:|---:|
| Customer/household count used | 2,469 | 94,990 valid-purchase customers |
| Transaction depth | 155,848 baskets; median 43/household | median 1 order/customer |
| Repeat prevalence | 98.74% have ≥2 baskets | 3.04% have ≥2 orders |
| Active temporal depth | median 348-day span; 11 active months | most customers have one order; cohort censoring severe |
| Product richness | 92,331 metadata rows; 68,509 purchased products | 32,729 purchased products |
| Monetary/behavioral breadth | value, quantity, basket, retailer/coupon discounts, stores, campaigns, promotions | price, freight, payment, fulfillment, reviews, seller/category |
| Context | Grocery retail frequent-shopper panel | Brazilian e-commerce marketplace |
| Interpretation strength | Strong repeated behavioral segments; household-level | Stronger e-commerce story and order experience; weaker lifecycle behavior |

Complete Journey is richer for longitudinal behavioral segmentation; Olist has far greater customer count and direct e-commerce relevance. This comparison does not choose a final customer source.

## Recommendation Feasibility

| Measure | Result |
|---|---:|
| Households | 2,469 |
| Purchased products | 68,509 |
| Distinct household-product interactions | 867,688 |
| Mean / median products per household | 351.43 / 277 |
| Mean / median households per product | 12.67 / 2 |
| Matrix sparsity | 99.4870% |
| Multi-product households | 99.7570% |
| Household-product pairs in multiple baskets | 213,604 (24.6176%) |

Despite numerical sparsity, household profiles are far denser than Olist and repeated product purchasing is common. Complete Journey can support purchase-only grocery recommendation or replenishment-oriented ranking. It lacks RetailRocket’s view/cart/transaction funnel, so it cannot model browsing intent and non-purchases are not negative feedback. Household identity may combine several shoppers. Recommendation feasibility is therefore **Moderate** relative to the intended broader e-commerce system.

## Computational Feasibility

Core local Pandas work is practical:

- transaction table: 1.47M rows, about 382 MB deep memory;
- products: 92K rows, about 30 MB;
- coupons: 116K rows, about 18 MB;
- all small/core tables are manageable on a normal development machine.

The exception is promotions: 20.94M rows and about **2.28 GB** in the current Pandas representation. Loading all tables simultaneously would require about **2.71 GB** before intermediates and joins. The notebook processes the large table separately and releases it.

No Spark, Dask, Polars, or database is empirically required. Full promotion analyses should first filter columns/weeks/products or aggregate placement states before joining. Efficient dtypes and staged processing are sufficient starting points; local resource profiling should precede any infrastructure change.

## Demand Forecasting and Anomaly Feasibility

Transactions include quantity, value, product, store, basket, week, and timestamp across one continuous year. Aggregate store/category/product series can be formed, with promotion context available. One year is short for annual-seasonality validation, and the dataset was not designed as a forecasting benchmark. It is **Moderate** for secondary demand/anomaly analysis, not a replacement for M5’s multi-year forecasting role.

## Limitations

- Grocery retail, not e-commerce or web behavior.
- Selected frequent-shopper household panel creates cohort/selection bias.
- Only one year; exact first/last days are partial.
- Household identity is not individual shopper identity.
- No contractual churn, account closure, views, carts, inventory, lead time, or replenishment.
- Demographics cover only 32.44% and contain further missingness.
- 4,836 transaction lines have no product metadata match.
- Coupon duplicates and promotion multi-state keys can inflate joins.
- Promotion table is memory-heavy.
- Marketing/promotion associations are observational and not causal effects.

## Complete Journey Feasibility Verdict

| MarketMind module | Rating | Empirical basis |
|---|---|---|
| Customer Segmentation | **Strong** | Median 43 baskets, 277 products and 11 active months; rich product/value/discount/store features. |
| Churn / Customer Return Risk | **Strong for return risk; unsupported as contractual churn** | 98.74% repeat and deep spans permit temporal snapshots, but no churn event exists and cohort selection limits scope. |
| Recommendation | **Moderate** | Dense household purchase histories and 24.62% repeated pairs, but purchase-only household data lacks view/cart intent. |
| Demand Forecasting | **Moderate** | Quantity/store/product time series and promotions exist, but only one year and no forecasting-specific holdouts. |
| Inventory Intelligence | **Unsupported** | No on-hand inventory, supplier lead time, or inbound replenishment. |
| Sales Anomaly Detection | **Moderate** | Continuous timestamped purchases and promotions support expected-versus-observed analysis, limited by one-year history. |

No final MarketMind dataset selection is made by this audit.
