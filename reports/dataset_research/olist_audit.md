# Olist Dataset Audit

**Phase 0B status:** empirical data audit only. No model, cluster, recommendation algorithm, forecast, or churn/return-risk label was created. Raw files were downloaded from the [canonical Kaggle dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) and left unchanged under `data/raw/olist/`.

Unless stated otherwise, customer-behavior results treat orders whose status is neither `canceled` nor `unavailable` as valid purchases. Counts use distinct `order_id`, never order-item rows.

## Dataset Integrity

All nine expected CSV files loaded successfully.

| File | Rows × columns | Exact duplicate rows | Candidate key result |
|---|---:|---:|---|
| `olist_customers_dataset.csv` | 99,441 × 5 | 0 | `customer_id` unique |
| `olist_geolocation_dataset.csv` | 1,000,163 × 5 | 261,831 | no single-row key; repeated zip/geocode observations |
| `olist_order_items_dataset.csv` | 112,650 × 7 | 0 | (`order_id`, `order_item_id`) unique |
| `olist_order_payments_dataset.csv` | 103,886 × 5 | 0 | (`order_id`, `payment_sequential`) unique |
| `olist_order_reviews_dataset.csv` | 99,224 × 7 | 0 | (`review_id`, `order_id`) unique; `review_id` alone has 814 duplicates |
| `olist_orders_dataset.csv` | 99,441 × 8 | 0 | `order_id` unique |
| `olist_products_dataset.csv` | 32,951 × 9 | 0 | `product_id` unique |
| `olist_sellers_dataset.csv` | 3,095 × 4 | 0 | `seller_id` unique |
| `product_category_name_translation.csv` | 71 × 2 | 0 | Portuguese category unique |

Observed table grain is one order-specific customer identity, geocode observation, order item/sequence, order payment sequence, order-associated review, order, product, seller, and category translation respectively. The geolocation duplicates are not automatically errors because the table is not one-row-per-prefix.

For the audited core relationships, unmatched foreign keys were zero: orders→customers, items/payments/reviews→orders, items→products, and items→sellers. There are 9,803 orders with multiple item rows, 2,961 with multiple payment rows, and 547 with multiple review rows. These cardinalities make naïve joins inflation-prone.

Important missingness includes:

- 160 missing order approvals (0.161%)
- 1,783 missing carrier-delivery timestamps (1.793%)
- 2,965 missing customer-delivery timestamps (2.982%)
- 610 products missing category and related description/photo attributes (1.851%)
- 2 products missing physical dimensions/weight (0.006%)
- 87,656 missing review titles (88.342%) and 58,247 missing review messages (58.703%); review scores themselves are complete

Missing lifecycle timestamps can be expected for some non-delivered statuses and should be evaluated conditionally rather than automatically treated as errors.

## Temporal Coverage

Order purchases run from **2016-09-04 21:15:19** to **2018-10-17 17:30:18**, a 772-day endpoint span. The main continuous sales period is substantially narrower than those endpoints:

- 2016-09 has 4 orders, 2016-10 has 324, 2016-11 has none, and 2016-12 has 1.
- Monthly volume becomes material from 2017-01 through 2018-08.
- 2018-09 has 16 orders and 2018-10 has 4.
- There are 140 calendar days with zero purchases across the full endpoint range, heavily influenced by the sparse boundaries and the missing 2016-11 period.

The first and last months are plainly incomplete. They must not be treated as comparable full months or used blindly as normal training/evaluation periods.

Order timestamp missingness and ranges are:

| Timestamp | Earliest | Latest | Missing |
|---|---|---|---:|
| purchase | 2016-09-04 | 2018-10-17 | 0 |
| approved | 2016-09-15 | 2018-09-03 | 160 |
| delivered to carrier | 2016-10-08 | 2018-09-11 | 1,783 |
| delivered to customer | 2016-10-11 | 2018-10-17 | 2,965 |
| estimated delivery | 2016-09-30 | 2018-11-12 | 0 |

Status distribution: 96,478 delivered, 1,107 shipped, 625 canceled, 609 unavailable, 314 invoiced, 301 processing, 5 created, and 2 approved.

## Customer Identity

`customer_id` and `customer_unique_id` are not interchangeable:

- `customer_id`: 99,441 unique values across 99,441 customer rows; it represents an order-specific customer identity and joins to orders.
- `customer_unique_id`: 96,096 unique values; it links order-specific identities believed to represent the same customer.

The difference is empirically visible: unique-customer count is lower than order-specific customer count. Repeat behavior was therefore calculated by joining orders to customers and grouping distinct orders on `customer_unique_id`.

## Repeat Purchase Behavior

Among **94,990 customers with valid purchases**:

| Measure | Result |
|---|---:|
| Exactly 1 distinct order | 96.9597% (92,102 customers) |
| At least 2 distinct orders | 3.0403% (2,888 customers) |
| At least 3 distinct orders | 0.2484% (236 customers) |
| Median orders per customer | 1 |
| Maximum orders for one customer | 16 |

Order-count distribution after one order: 2,652 customers had 2 orders; 188 had 3; 29 had 4; 9 had 5; 5 had 6; 3 had 7; 1 had 9; and 1 had 16.

There were 3,217 consecutive-order intervals among repeat customers:

| Statistic | Days |
|---|---:|
| Count | 3,217 |
| Mean | 78.89 |
| 25th percentile | 0.005 |
| Median | 29.02 |
| 75th percentile | 120.75 |
| 90th percentile | 241.83 |

Notably, 965 intervals (29.997%) are under one day and 283 are exactly zero days at the available precision. This suggests that some linked “repeat orders” are near-simultaneous split purchases rather than independent return occasions. That observation further weakens any churn interpretation until same-session/order-splitting behavior is investigated.

## Right-Censoring Risk

First-purchase cohorts have sharply unequal follow-up. Examples:

| First-purchase cohort | Customers | Observed repeat % | Maximum follow-up days |
|---|---:|---:|---:|
| 2017-01 | 752 | 7.31% | 605 |
| 2017-06 | 3,102 | 5.38% | 459 |
| 2017-12 | 5,439 | 2.70% | 276 |
| 2018-04 | 6,698 | 1.97% | 155 |
| 2018-06 | 5,920 | 1.20% | 94 |
| 2018-08 | 6,209 | 0.56% | 33 |

The declining late-cohort repeat rate is confounded by declining opportunity to return. A customer first seen in August 2018 has at most 33 days of valid-purchase follow-up, versus hundreds of days for 2017 cohorts. Later cohorts therefore cannot be assigned the same outcome logic as earlier cohorts. Any future target needs explicit observation and outcome windows, eligibility rules, and censoring controls derived after deeper EDA.

## Segmentation Feasibility

Potentially useful customer descriptors are available, but most are **derivable**, not ready-made. Recency, distinct-order frequency, monetary value, average order value, purchased-item count, unique products/categories, freight spending, and payment behavior can be constructed with grain-safe aggregation. Review score is **problematic** for predictive use because it occurs after purchase and may not exist at the prediction snapshot. Operational inventory is unavailable.

Temporal segmentation or downstream prediction must freeze all features at a historical cutoff. Payments must first aggregate payment rows to order level; order items must first aggregate line items to order level; price/freight and payment value must not be double-counted as the same spend.

Olist supports descriptive customer profiling well, but 96.96% single-order prevalence limits behavior-rich lifecycle segmentation. Overall feasibility is therefore **Moderate**, not Strong, after empirical inspection.

## Churn / Return-Risk Feasibility

Olist can technically link customers and form temporal cohorts, but a defensible churn target is not established:

- only 3.04% of valid-purchase customers have at least two distinct orders;
- almost 30% of observed repeat intervals are under one day;
- marketplace purchase cadence has a long tail (90th percentile interval 241.83 days);
- late cohorts are heavily right-censored;
- there is no contractual churn/closure event.

The safer concept remains **customer return risk**. Even that should use eligible early cohorts and a target definition selected only after cadence and censoring sensitivity analysis. Feasibility is **Weak**.

## Recommendation Feasibility

Valid purchases yield:

| Measure | Result |
|---|---:|
| Customers | 94,983 |
| Products | 32,729 |
| Distinct customer-product interactions | 101,521 |
| Mean / median distinct products per customer | 1.069 / 1 |
| Mean / median customers per product | 3.102 / 1 |
| User-item matrix sparsity | 99.996734% |
| Customers with one distinct product | 94.2821% |
| Customers with multiple distinct products | 5.7179% |
| Customer-product pairs bought in multiple orders | 413 |

There are 10,580 order-item occurrences beyond the distinct customer-product pair count, but many arise from same-order quantity/line repetition and should not be confused with repeated preference events. Only 413 customer-product pairs occur across multiple distinct orders.

Olist records purchases, not product views or cart additions. It therefore lacks the richer implicit-feedback funnel available in RetailRocket, and non-purchase cannot be treated as dislike. Extreme sparsity, one-product users, one-customer products, and cold start dominate. A constrained purchase-cooccurrence or popularity study may be possible, but personalized recommendation feasibility is **Weak** on the full population.

## Forecasting Feasibility

Across the valid-order item data, the purchase range used for sales feasibility contains 730 calendar days:

- total sales occur on 614 days; total-day zero density is 15.89%, driven largely by incomplete early/late coverage;
- 73 categories form 18,461 observed category-days, a 34.64% category-day density; median category has 180 active days;
- 32,729 products form 94,142 observed product-days, only 0.394% density; median product has one active day.

Total or selected-category secondary analysis may be feasible after trimming incomplete boundaries and checking category history. Product-day forecasting is generally not credible for most products. Olist is **Weak** as a general demand-forecasting source; it may support limited aggregate secondary analysis, while M5 remains the specialized candidate.

## Cancellations / Returns

The dataset explicitly contains **625 canceled orders**. It also contains 609 `unavailable` orders, which is a separate status and should not be silently relabeled cancellation.

No order-status value explicitly names a refund or product return. Delivery, payment, or review records do not by themselves establish a returns process. Olist can support cancellation analysis, but this audit found no evidence for a distinct product-return/refund history; returns must not be inferred.

## Known Dataset Limitations

- Incomplete and anomalously sparse beginning/end periods, including no purchases in 2016-11.
- Very low true repeat-customer prevalence and many near-simultaneous repeat orders.
- Strong right-censoring differences between customer cohorts.
- Purchase-only interactions and an extremely sparse customer-product matrix.
- Product-day sales are overwhelmingly intermittent.
- Duplicate `review_id` values prevent treating it as a global primary key; review joins require order-aware grain.
- Geolocation has many repeated/duplicate observations and cannot be joined as one row per zip prefix without aggregation decisions.
- Missing product categories and lifecycle timestamps require context-aware handling.
- No verified refunds/product returns, inventory levels, supplier lead time, inbound replenishment, views, or carts.
- Dataset outcomes describe an historical marketplace sample and do not prove current behavior or causal business effects.

## Olist Feasibility Verdict

| MarketMind module | Rating | Empirical basis |
|---|---|---|
| Customer Segmentation | **Moderate** | Rich order/value/product/payment features, but 96.96% have one order and features require grain-safe construction. |
| Churn / Return Risk | **Weak** | Only 3.04% repeat, near-simultaneous repeats are common, and cohorts are heavily censored. |
| Recommendation | **Weak** | Purchase-only matrix is 99.9967% sparse; 94.28% of customers bought one distinct product. |
| Demand Forecasting | **Weak** | Aggregate/category secondary series may work, but product-day density is 0.394% and boundaries are incomplete. |
| Inventory Intelligence | **Unsupported** | No on-hand stock, supplier lead time, or inbound replenishment. Sales and `unavailable` status are not inventory. |
| Sales Anomaly Detection | **Moderate** | Total/category time series exist for the main period, but boundary gaps and absent inventory/promotion context limit interpretation. |

These ratings describe Olist alone and do not select MarketMind’s final dataset architecture.
