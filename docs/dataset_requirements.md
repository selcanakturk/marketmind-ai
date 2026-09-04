# Dataset Requirements and Phase 0 Candidate Audit

This document separates ideal requirements from facts verified in public documentation. It is not a substitute for file-level EDA. **Not yet verified** means the reviewed canonical or authoritative documentation did not establish the detail.

## Ideal Data Requirements

- **Demand Forecasting:** item identifier, date, quantity sold, price/category and promotion/calendar context where available, plus enough history for temporal backtesting.
- **Customer Segmentation:** persistent customer, dated order, product/category, quantity and value, with enough repeat behavior for stable profiles.
- **Churn Prediction:** persistent customer, long repeat history, defensible observation/prediction windows, pre-outcome feature snapshots, and enough follow-up to address censoring.
- **Recommendations:** persistent user, item, timestamp, interaction type, and chronology for temporal evaluation; views/cart/purchases are preferable to purchases alone.
- **Inventory Intelligence:** forecast-compatible sales plus genuine on-hand stock, supplier lead time, and inbound replenishment.
- **Sales Anomaly Detection:** product/category time series long enough to estimate expected behavior, with known calendar/promotion effects where available.

Sales quantity is not inventory. If operational inventory fields are absent, MarketMind may later accept current stock, lead time, and inbound replenishment as user-provided inputs and combine them with forecasts. It must not fabricate inventory history.

## Rating Interpretation

- **Strong:** main data elements and temporal depth are documented.
- **Moderate:** useful implementation appears possible, with important limitations.
- **Weak:** only a constrained or exploratory implementation appears defensible.
- **Unsupported:** core data are absent.

Ratings are preliminary feasibility assessments, not dataset decisions.

## Candidate Public Datasets To Investigate

### 1. M5 Forecasting — Accuracy

- **Source / canonical page:** [Kaggle competition data](https://www.kaggle.com/competitions/m5-forecasting-accuracy/data); [M5 Accuracy competition paper](https://doi.org/10.1016/j.ijforecast.2021.11.013)
- **Data origin:** Hierarchical daily unit sales of Walmart retail goods in California, Texas, and Wisconsin. This is retail, not e-commerce transaction, data.
- **Time coverage:** Sales begin 2011-01-29. The competition design spans 1,969 days through 2016-06-19; the published evaluation training file exposes `d_1`–`d_1941`, with a final 28-day competition test horizon.
- **Approximate size / known records:** 30,490 item-store series (3,049 items, 10 stores, 3 states); 42,840 series across 12 hierarchy levels; up to 1,941 published daily values per bottom-level series.
- **Main entities:** item, department, category, store, state, date/week, event, SNAP indicator, sell price.
- **Main files:** `calendar.csv`, `sales_train_validation.csv`, `sales_train_evaluation.csv`, `sell_prices.csv`, `sample_submission.csv`.
- **Timestamp granularity:** Daily sales; weekly store-item prices.
- **Customer identifier / repeat customers:** None / no.
- **Product identifier:** Yes, `item_id`.
- **Order identifier:** No.
- **Quantity:** Yes, daily unit sales.
- **Price:** Yes, store-item sell price by week.
- **Category metadata:** Category, department, store and geography hierarchy.
- **Promotion/calendar/events:** Named calendar events, event types, date fields, and state SNAP indicators. A direct promotion flag is not documented.
- **Behavioral interactions:** None.
- **Inventory / on-hand stock:** None documented.
- **Lead time:** None documented.
- **Returns/cancellations:** Not yet verified; there is no documented order-level entity.
- **License / restrictions:** Kaggle states “subject to Competition Rules.” Portfolio use and redistribution must be checked against those rules.
- **Major limitations:** No customers, baskets, sessions, or web behavior; zero sales cannot be assumed to mean zero demand because stock availability is absent; wide hierarchical data can be computationally demanding.

#### Module feasibility

- **Demand Forecasting — Strong.** Long daily item-store histories, prices, calendar variables, and hierarchy directly support forecasting. The 28-day competition horizon is a useful benchmark; rolling/expanding backtests are also feasible if features are cutoff-safe.
- **Customer Segmentation — Unsupported.** No customer data.
- **Churn Prediction — Unsupported.** No longitudinal customer identity or behavior.
- **Recommendation — Unsupported.** No user-item interactions.
- **Inventory Intelligence — Weak.** Forecast outputs could support decisions, but sales are not stock and no on-hand inventory, lead time, or replenishment is documented.
- **Sales Anomaly Detection — Strong.** About five years of daily series and calendar covariates support expected-versus-observed/residual analysis, subject to stockout ambiguity.

M5 is appropriate for a forecasting engine because it supplies daily item/store sales, historical depth, calendar/event information, weekly prices, a 12-level hierarchy, and a 28-day reference horizon. It supports multiple rolling or expanding origins rather than a single reused test set. Local processing may need memory-aware reshaping, efficient dtypes, aggregation scoping, or representative subsets before scaling. If selected, documentation must state that M5 is Walmart retail data, not an e-commerce transaction dataset.

### 2. RetailRocket Recommender System Dataset

- **Source / canonical page:** [RetailRocket dataset on Kaggle](https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset)
- **Data origin:** Raw anonymized interactions from a real e-commerce site, published for implicit-feedback recommendation research.
- **Time coverage:** 4.5 months.
- **Approximate size / known events:** 2,756,101 events from 1,407,580 visitors: 2,664,312 views, 69,332 cart additions, 22,457 transactions. Item properties contain 20,275,902 change-log rows for 417,053 items; category tree has 1,669 rows. Distinct transaction count is not stated.
- **Main entities:** visitor, item, event, transaction, time-varying item property, category.
- **Main files:** `events.csv`, two `item_properties.csv` parts, `category_tree.csv`.
- **Timestamp granularity:** Unix event timestamps; time-stamped roughly weekly property snapshots compressed into a change log.
- **Customer identifier:** `visitorid`; cross-device/authenticated durability is not documented.
- **Repeat customers:** Repeat events can be linked, but durable customer identity is not yet verified.
- **Product identifier:** Yes, `itemid`.
- **Order identifier:** `transactionid` on transaction events.
- **Quantity:** No quantity field documented.
- **Price:** Time-varying properties may include price, but values other than `categoryid` and `available` are hashed; usable monetary price is not established.
- **Category metadata:** Category IDs and parent-child tree.
- **Promotion/calendar/events:** No explicit promotions or named calendar events documented.
- **Behavioral interactions:** View, add-to-cart, transaction.
- **Inventory / on-hand stock:** Binary `available` property only; it is not a stock quantity or ledger.
- **Lead time:** None documented.
- **Returns/cancellations:** None documented.
- **License / restrictions:** Kaggle lists CC BY-NC-SA 4.0; attribution, non-commercial, and share-alike implications need review.
- **Major limitations:** Short period, extreme sparsity, few purchases relative to views, unclear visitor persistence, hashed properties, no quantities or operational stock.

#### Module feasibility

- **Demand Forecasting — Weak.** Transaction counts exist, but 4.5 months, absent quantities, hashed price, and sparse purchases limit seasonal forecasting.
- **Customer Segmentation — Moderate.** Funnel behavior supports behavioral/session segments; short history and identity ambiguity weaken lifecycle segmentation.
- **Churn Prediction — Weak.** The short window, uncertain identity durability, sparse purchases, and right-censoring make “visitor return risk” safer than churn until EDA proves viable repeat cohorts and windows.
- **Recommendation — Strong.** Timestamped views, carts, and transactions provide richer implicit feedback than purchase-only sources and permit chronological evaluation. Sparsity and cold start remain central.
- **Inventory Intelligence — Weak.** Availability is contextual but not on-hand inventory; no lead time or replenishment exists.
- **Sales Anomaly Detection — Weak.** Transaction counts can be monitored, but sparse purchases over 4.5 months give limited expected-sales history.

### 3. Brazilian E-Commerce Public Dataset by Olist

- **Source / canonical page:** [Olist dataset on Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
- **Data origin:** Anonymized real commercial Olist Store marketplace orders in Brazil.
- **Time coverage:** Approximately 100,000 orders from 2016–2018; exact endpoints require file inspection.
- **Approximate size / known orders:** About 100,000 orders, nine files, 52 columns, approximately 126 MB on the current page. Exact table row counts are not yet verified.
- **Main entities:** order, order item, customer/unique customer, product, seller, payment, review, geolocation.
- **Main files:** orders, order items, customers, products, sellers, payments, reviews, geolocation, and product-category translation CSVs.
- **Timestamp granularity:** Purchase, approval, carrier handoff, delivery and estimated-delivery timestamps; stored precision requires inspection.
- **Customer identifier:** Per-order `customer_id` and cross-order `customer_unique_id`.
- **Repeat customers:** Supported in principle by `customer_unique_id`; actual repeat prevalence requires EDA.
- **Product identifier:** Yes, `product_id`.
- **Order identifier:** Yes, `order_id`.
- **Quantity:** Multiple items per order are documented, but no standalone quantity field is established. Unit counts from line rows require grain/duplicate audit.
- **Price:** Order-item price; payment and freight values are also represented.
- **Category metadata:** Product category and translation table.
- **Promotion/calendar/events:** No explicit promotion/marketing event fields. Calendar features could be derived but are not supplied event metadata.
- **Behavioral interactions:** Purchases, payments, fulfillment statuses, delivery and reviews; no views/carts documented.
- **Inventory / on-hand stock:** None documented.
- **Lead time:** Supplier replenishment lead time is absent; delivery intervals are fulfillment outcomes, not supplier lead time.
- **Returns/cancellations:** Order status is documented and may include cancellation; exact statuses and return representation require inspection.
- **License / restrictions:** Exact current terms are **Not yet verified** from the canonical page extract and must be rechecked at selection time; secondary references report CC BY-NC-SA 4.0.
- **Major limitations:** Purchase-only behavior, unknown repeat rate, roughly two years, no stock/lead-time/replenishment or promotions, marketplace fulfillment complicates demand interpretation.

#### Module feasibility

- **Demand Forecasting — Moderate.** Dated product orders, categories and prices support aggregated sales-count forecasting, but quantity grain needs validation and inventory/promotion context is absent.
- **Customer Segmentation — Strong.** Persistent customers, orders, values, products/categories, locations, reviews and fulfillment outcomes support interpretable segmentation.
- **Churn Prediction — Weak.** Repurchase linkage exists, but sufficient longitudinal repeats are unproven. Low-frequency purchasing and censoring may require “customer return risk”; no threshold should precede EDA.
- **Recommendation — Moderate.** Timestamped customer-product purchases support purchase-only recommendation and temporal evaluation, without view/cart feedback.
- **Inventory Intelligence — Weak.** Sales and fulfillment can feed forecasts, but operational stock, supplier lead time and replenishment are absent.
- **Sales Anomaly Detection — Moderate.** About two years can support suitable aggregate series, limited by sparse products and missing stock/promotion context.

### 4. Complete Journey / dunnhumby 84.51°

- **Dataset name:** Complete Journey 2.0 as represented by `completejourney`
- **Source / canonical page:** [84.51° Area 51](https://www.8451.com/area51/); authoritative [`completejourney` repository](https://github.com/bradleyboehmke/completejourney) and [CRAN page](https://cran.r-project.org/package=completejourney)
- **Data origin:** Grocery-store transactions for frequent-shopper households, with selected demographics and direct-marketing history.
- **Time coverage:** Authoritative package documentation says one year. Other public material describes older/differently packaged Complete Journey releases as about 102 weeks and 2,500 households; these must not be mixed without selecting the exact release.
- **Approximate size / known records:** 2,469 households; 1,469,307 transaction lines; 20,940,529 promotion rows. Unique basket count is not stated in the overview.
- **Main entities:** household, basket, product, store, transaction, campaign, coupon/redemption, promotion, demographics.
- **Main files/tables:** transactions, products, demographics, campaigns, campaign descriptions, coupons, redemptions and promotions. Package includes samples and functions for full large tables.
- **Timestamp granularity:** Transaction datetimes; transaction/marketing data also expose week/day concepts.
- **Customer identifier / repeats:** Persistent `household_id`; repeated purchases are documented for frequent-shopper households.
- **Product identifier:** Yes, `product_id`.
- **Order identifier:** `basket_id`.
- **Quantity:** Yes.
- **Price:** `sales_value` and retail/coupon discounts; separate undiscounted unit price is not established.
- **Category metadata:** Product metadata documented; exact hierarchy fields require inspection.
- **Promotion/calendar/events:** Campaigns, coupons/redemptions, and store/mailer placement; holiday calendar metadata not yet verified.
- **Behavioral interactions:** Purchases and marketing exposure/redemption; no views/carts.
- **Inventory / on-hand stock:** None documented.
- **Lead time:** None documented.
- **Returns/cancellations:** Not yet verified.
- **License / restrictions:** The R package is CC0. Separately obtained 84.51° files or alternate releases require their own terms check.
- **Major limitations:** Grocery retail, not e-commerce; household rather than individual; selected frequent shoppers create cohort bias; one documented year; partial demographics; no web behavior or inventory.

#### Module feasibility

- **Demand Forecasting — Moderate.** Dated basket quantities, stores, values/discounts and promotion context support aggregation/backtesting, but one year is much shorter than M5.
- **Customer Segmentation — Strong.** Persistent households, repeated category/value/quantity behavior, promotions and partial demographics provide rich inputs, with careful cohort framing.
- **Churn Prediction — Moderate.** Repeated grocery shopping best supports temporal snapshots among the customer candidates, but fixed-window censoring and no closure event favor “household return/future inactivity risk.” Target design must follow EDA.
- **Recommendation — Moderate.** Repeated timestamped household-product purchases support purchase-only recommendation; no views/carts and household identity limit interpretation.
- **Inventory Intelligence — Weak.** Demand and promotion data are not inventory; stock, lead time and replenishment are absent.
- **Sales Anomaly Detection — Moderate.** Detailed transactions/promotions allow expected-versus-observed analysis at suitable aggregates, constrained by one-year depth and missing inventory.

## Phase 0 Inventory Conclusion

None of the candidates has verified operational history containing current stock, supplier lead time, and inbound replenishment. RetailRocket availability is binary, and sales quantities in other datasets are not stock. If these fields remain absent, Inventory Intelligence should accept them later as operational/user inputs and combine them with forecasts and transparent rules. Inventory history must not be fabricated.

No data was downloaded for this audit. Exact distributions, nulls, grains, duplicates, endpoints, repeat rates, sparsity, censoring, and viable series counts remain subject to EDA.
