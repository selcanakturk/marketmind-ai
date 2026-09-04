# Phase 0 Dataset Feasibility Matrix

Status: research synthesis only. No dataset has been downloaded, audited locally, or selected. Ratings follow [`docs/dataset_requirements.md`](../../docs/dataset_requirements.md).

## Comparison Matrix

| Dataset | Forecasting | Segmentation | Churn | Recommendation | Inventory | Anomaly Detection | Data Scale | Temporal Depth | Key Strength | Key Limitation |
|---|---|---|---|---|---|---|---|---|---|---|
| M5 Forecasting — Accuracy | Strong | Unsupported | Unsupported | Unsupported | Weak | Strong | 30,490 item-store series; 3,049 items; 10 stores | ~5.4 years daily; 28-day competition horizons | Purpose-built hierarchical demand, prices and calendar | Retail, not e-commerce; no customers, interactions or stock |
| RetailRocket | Weak | Moderate | Weak | Strong | Weak | Weak | 2.76M events; 1.41M visitors; 417K items in property data | 4.5 months | View/cart/transaction implicit feedback | Short, sparse history; identity and usable price semantics unclear |
| Olist | Moderate | Strong | Weak | Moderate | Weak | Moderate | ~100K orders across nine files | 2016–2018; exact endpoints pending | Relational e-commerce orders and persistent customer key | Purchase-only, unknown repeat rate, no stock |
| Complete Journey 2.0 | Moderate | Strong | Moderate | Moderate | Weak | Moderate | 2,469 households; 1.47M transaction and 20.94M promotion rows | One year in authoritative package docs | Dense household purchases plus promotion/coupon context | Grocery retail, household identity, selected cohort, no web events/stock |

Inventory ratings are **Weak**, not evidence of inventory support: the sources contribute demand information, but none documents the full operational state required for inventory decisions.

## Candidate Dataset Architectures

These are alternatives for further investigation, not rankings or selections.

### A. M5 + RetailRocket

- **Methodological quality:** Clean separation between purpose-built forecasting and implicit-feedback recommendation. RetailRocket segmentation is behavioral/session-oriented rather than a durable lifecycle view.
- **Number of datasets:** Two.
- **Customer-module coherence:** Segmentation, return-risk exploration and recommendation share RetailRocket, but 4.5 months may not support a coherent long-term customer story.
- **Recommendation quality:** Strongest signal variety because views, carts and transactions are timestamped.
- **Churn feasibility:** Weak; short observation, unknown identifier durability, sparse purchases and censoring favor “visitor return risk.”
- **Project-story coherence:** Strong e-commerce recommendation plus rigorous retail forecasting, with an explicit domain boundary.
- **Complexity:** Two schemas and contexts; moderate documentation burden. They must not be presented as one merchant.

### B. M5 + Olist

- **Methodological quality:** Strong forecasting source plus a relational e-commerce source for customer/order analysis.
- **Number of datasets:** Two.
- **Customer-module coherence:** Olist can serve segmentation, customer-return research and purchase-only recommendation.
- **Recommendation quality:** Moderate; no documented view/cart signals.
- **Churn feasibility:** Weak until repeat rates and eligible temporal cohorts are established.
- **Project-story coherence:** High if forecasting is transparently labeled retail and customer modules e-commerce.
- **Complexity:** Two schemas; lower burden than a third recommendation source, with possible churn/recommendation compromises.

### C. M5 + Complete Journey

- **Methodological quality:** Strong temporal retail data on both sides. Complete Journey adds repeated households and promotions.
- **Number of datasets:** Two.
- **Customer-module coherence:** Segmentation, return risk and purchase-only recommendation share household histories.
- **Recommendation quality:** Moderate; repeated baskets help, but no views/carts and households may contain several shoppers.
- **Churn feasibility:** Moderate and preliminarily strongest of the customer candidates, while still requiring a non-contractual return-risk framing.
- **Project-story coherence:** Methodologically coherent commerce intelligence, but both sources are retail/grocery rather than e-commerce.
- **Complexity:** Two substantial schemas; full promotions are large and release/version provenance must be resolved.

### D. M5 + One Customer Dataset + RetailRocket for Recommendation

- **Methodological quality:** Optimizes independently: M5 forecasting, a longitudinal customer source for segmentation/return risk, RetailRocket for implicit feedback.
- **Number of datasets:** Three, unless RetailRocket is also the customer source (then this collapses toward A).
- **Customer-module coherence:** Segmentation and churn can share Olist or Complete Journey; recommendation intentionally uses another domain.
- **Recommendation quality:** Strong because RetailRocket supplies views, carts and transactions.
- **Churn feasibility:** Preliminary Weak with Olist and Moderate with Complete Journey; EDA remains decisive.
- **Project-story coherence:** Honest and problem-specific, but best framed as a suite of capabilities rather than one unified merchant dataset.
- **Complexity:** Highest: three schemas, feature meanings, evaluations and licensing/provenance tracks.

## Churn Feasibility: RetailRocket vs Olist vs Complete Journey

No candidate contains a documented contractual churn event. The actual target must be derived after EDA; no inactivity threshold is defined here.

| Consideration | RetailRocket | Olist | Complete Journey 2.0 |
|---|---|---|---|
| Observation period | 4.5 months | Approximately 2016–2018 | One year in package docs |
| Repeat identity | Repeat `visitorid`; durable customer meaning unknown | `customer_unique_id` explicitly links repurchases | Persistent household ID for frequent shoppers |
| Purchase frequency | Only 22,457 transaction events; cadence needs EDA | Marketplace purchases may be infrequent; repeat rate unknown | Grocery purchases plausibly frequent; cadence still needs EDA |
| Meaning of inactivity | Could mean non-return, identity loss or no tracked visit | No return is not proven relationship termination | Better fit for future inactivity, still not contractual churn |
| Right-censoring | Severe due to short fixed window | Material near dataset end | Material near dataset end despite repeat behavior |
| Observation/prediction windows | Possible, likely small eligible cohort | Possible if enough early repeat customers exist | Most promising for repeated snapshots, limited by one year |
| Preliminary rating | Weak | Weak | Moderate |
| Safer label | Visitor return risk | Customer return risk | Household return/future inactivity risk |

EDA must quantify first/last activity, interpurchase times, eligible cohorts at multiple cutoffs, repeat counts, outcome coverage and censoring before deciding whether “churn” is defensible.

## Recommendation Feasibility: RetailRocket vs Olist vs Complete Journey

| Consideration | RetailRocket | Olist | Complete Journey 2.0 |
|---|---|---|---|
| Feedback | Views, cart additions, transactions | Purchases only | Purchases plus marketing context; no views/carts |
| User identity | Anonymous visitor; persistence unknown | Persistent unique customer | Persistent household, not individual |
| Item identity | Item plus hashed properties/category tree | Product plus category/physical metadata | Product plus metadata |
| Sparsity | Very high; views add useful weak signal | Likely sparse customer-product purchases; measure in EDA | Repeated grocery baskets may be denser; measure in EDA |
| Temporal evaluation | Strong timestamps, short total horizon | Purchase timestamps permit chronological splits | Transaction timestamps permit chronological splits |
| Cold start | Many visitors/items require popularity/content/session fallbacks | New/one-time customers and products likely material | Household/product cold start remains; cohort underrepresents new shoppers |
| Preliminary rating | Strong | Moderate | Moderate |

RetailRocket alone documents a view/cart/purchase funnel and thus richer implicit feedback. Olist and Complete Journey support purchase-only preference learning; Complete Journey marketing exposure must not be mislabeled as organic interaction. All require leakage-safe temporal evaluation and cold-start reporting.

## Forecasting Feasibility: M5

M5 is **Strong** for demand forecasting: daily item/store unit sales, about five years of history, weekly prices, calendar/events, SNAP indicators and a 12-level hierarchy. Its two 28-day competition periods offer a reproducible reference, while the longer history permits rolling or expanding-origin backtests.

Scale is the main risk: 30,490 bottom series, wide daily data, price joins, lag features and hierarchical evaluation can consume substantial memory and compute. Initial work should profile local resources and consider aggregation, scoped subsets, efficient dtypes and reusable cutoff-safe features before adding infrastructure.

M5 is Walmart retail data, not an e-commerce transaction dataset. MarketMind must not imply that it contains customers, web behavior, orders or inventory.

## Inventory Limitation

None of the candidates should be assumed to contain operational inventory. RetailRocket’s binary availability property is not on-hand quantity; the others document sales/purchases, not stock ledgers.

If current stock, supplier lead time and inbound replenishment are absent, the eventual Inventory Intelligence module should accept them as operational/user-provided inputs and combine them with forecasts and transparent rules. It must not fabricate inventory history or infer stock solely from sales.

## Empirical Audit Update — Phase 0B/0C/0D

The matrix and comparisons above preserve the documentation-based preliminary assessment. Three candidates have now been inspected directly:

| Dataset | Audit status | Key empirical correction or confirmation |
|---|---|---|
| Olist | Phase 0B complete | Segmentation remains useful but is **Moderate** after observing 96.96% single-order customers. Return risk and recommendation are **Weak**: only 3.04% repeat, 94.28% purchase one distinct product, and the interaction matrix is 99.9967% sparse. |
| Complete Journey 2.0 | Phase 0C complete | Longitudinal depth is confirmed and stronger than the preliminary rating suggested: 98.74% have ≥2 baskets, median 43 baskets, median 348-day active span, and 88.86% are active in ≥6 months. Segmentation and future return-risk feasibility are **Strong**, subject to frequent-shopper selection and non-contractual terminology. |
| RetailRocket | Phase 0D complete | Recommendation is empirically **Strong** for implicit-feedback and cold-start methodology: 2.15M distinct event pairs and thousands of warm temporal candidates. Identity remains shallow—71.15% have one event—and 94.28% of future visitors are unseen at the 60% cutoff. |

The audited Complete Journey release is specifically the CC0 `completejourney` package 1.1.1 representation of **Complete Journey 2.0**: 2,469 frequent-shopper households over one year. It must not be mixed with or described as the legacy 2,500-household/102-week CSV release.

## Customer Dataset Decision Status

No final customer dataset has been selected.

| Dataset | Segmentation | Churn / Return Risk | Recommendation | Current evidence status | Central tradeoff |
|---|---|---|---|---|---|
| Olist | **Moderate (empirical)** | **Weak (empirical)** | **Weak (empirical)** | Full Phase 0B audit | Large, directly e-commerce, and operationally rich, but almost all customers have one order. |
| Complete Journey 2.0 | **Strong (empirical)** | **Strong for return risk (empirical); no contractual churn** | **Moderate (empirical)** | Full Phase 0C audit | Deep household histories and rich grocery behavior, but only 2,469 selected frequent-shopper households and no e-commerce interactions. |
| RetailRocket | **Weak (empirical)** | **Unsupported (empirical)** | **Strong (empirical)** | Full Phase 0D audit | Rich e-commerce implicit feedback and realistic cold start, but only 138 days and extremely shallow anonymous visitor identity. |

## Recommendation Dataset Decision

No recommendation dataset has been selected automatically.

| Decision question | Empirical answer |
|---|---|
| Which offers the strongest recommendation methodology? | **RetailRocket** for implicit-feedback, event-sequence, temporal-ranking, and cold-start-aware evaluation. **Complete Journey** is stronger for repeated purchase/replenishment personalization. Olist is weakest for personalized recommendation. |
| Which offers the cleanest project architecture? | **Complete Journey alone** for customer segmentation, return risk, and purchase-only recommendation minimizes datasets and shares one household/product domain. |
| Is RetailRocket sufficiently better to justify a third training dataset? | **Potentially yes, if MarketMind explicitly wants a distinct e-commerce intent recommender.** Its view/cart/purchase stream and severe real cold-start condition are not available in Complete Journey. The justification is methodological breadth, not higher purchase density. |

### Empirical recommendation comparison

| Dimension | RetailRocket | Complete Journey 2.0 | Olist |
|---|---:|---:|---:|
| Identity units | 1,407,580 visitors | 2,469 households | 94,983 purchasing customers |
| Products in audited interactions | 235,061 | 68,509 | 32,729 |
| Distinct pairs | 2,145,179 all-event; 21,270 purchase-only | 867,688 purchase-only | 101,521 purchase-only |
| Sparsity | 99.99935% all-event; 99.98491% purchase-only | 99.48703% | 99.99673% |
| Median products/pairs per identity | 1 all-event pair | 277 products | 1 product |
| Event richness | View, add-to-cart, transaction | Purchase plus coupon/promotion context | Purchase/order only |
| Temporal depth | 138 days | 364-day endpoint span | ~2 years overall, but mostly one order/customer |
| Repeat-purchase evidence | Thin: median 1 purchased item; most buyer spans are same-day | Deep: median 43 baskets; 98.74% repeat | Thin: 3.04% repeat orders |
| Cold-start profile | Dominant: 88.98% of future events have unseen visitors at 60% cutoff | Established frequent-shopper panel underrepresents cold start | Many one-order customers; weak warm-user evaluation |
| Domain fit | Direct e-commerce behavior | Grocery retail household behavior | Direct e-commerce marketplace orders |
| Local data cost | ~942 MB raw; metadata parts ~2.62 GB in memory | ~37 MB compressed; full promotions ~2.28 GB | ~120 MB extracted |

RetailRocket adds a recommendation problem that Complete Journey cannot reproduce: anonymous short-term intent across views, carts, and purchases. Conversely, it cannot replace Complete Journey for longitudinal customer behavior. A three-dataset architecture is therefore methodologically coherent if each source has a sharply bounded role, but it carries additional provenance, processing, explanation, and maintenance cost. Final selection remains pending.

### Empirical Olist vs Complete Journey comparison

- **Scale:** Olist covers 94,990 valid-purchase customers; Complete Journey covers 2,469 households.
- **Repeat depth:** Olist median is 1 order and 3.04% repeat; Complete Journey median is 43 baskets and 98.74% repeat.
- **Observation depth:** Olist’s customer history is mostly a point observation; Complete Journey’s median active span is 348 days with 11 active months.
- **Recommendation:** Olist has 101,521 distinct pairs and 99.9967% sparsity; Complete Journey has 867,688 pairs, 99.4870% sparsity, median 277 products per household, and 24.62% of pairs recur across baskets.
- **Feature richness:** Both provide product and monetary behavior. Complete Journey adds quantities, cadence, stores, discounts, coupons, campaigns and promotion placement; Olist adds e-commerce fulfillment, freight, payments, reviews, sellers and geographic context.
- **Narrative:** Olist directly represents e-commerce marketplace orders. Complete Journey represents grocery-retail household purchases and must remain transparently labeled.
- **Return-risk support:** Complete Journey empirically supports potential cutoff-based observation and future windows. Olist’s sparse repeats and censoring make a general supervised return-risk design substantially weaker.

This evidence narrows the remaining decision but does not resolve whether customer segmentation and return risk should share Complete Journey, whether Olist should remain for e-commerce-specific descriptive/segmentation work, or whether recommendation should be optimized independently with RetailRocket.

## Questions To Resolve Before Dataset Selection

- Given Olist's audited 3.04% repeat rate, is a narrow eligible-cohort return-risk study valuable enough to retain, or should it remain segmentation/descriptive only?
- Is Complete Journey’s grocery-retail context acceptable for the MarketMind product narrative?
- Is the audited Complete Journey 2.0 package release (one year, 2,469 households, CC0) the appropriate canonical customer source despite frequent-shopper selection?
- Should RetailRocket be framed strictly as anonymous/session-like intent rather than durable customer personalization?
- Is the methodological value of RetailRocket's implicit-feedback and cold-start problem worth the third dataset's processing and narrative complexity?
- Should recommendation share the segmentation/churn source, or should each problem use its strongest source?
- Is M5 computationally manageable locally at the intended hierarchy without unnecessary infrastructure?
- Which datasets and derived artifacts can be published comfortably under their licenses in a public GitHub portfolio?
- What are the exact repeat-customer, sparsity, cancellation/return, missingness and temporal-coverage statistics after inspection?
- At which aggregation levels do Olist and Complete Journey support stable forecasting/anomaly baselines?

## Sources Reviewed

- [M5 competition data documentation](https://www.kaggle.com/competitions/m5-forecasting-accuracy/data)
- [M5 Accuracy competition paper](https://doi.org/10.1016/j.ijforecast.2021.11.013)
- [RetailRocket dataset](https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset)
- [Olist dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
- [84.51° Area 51](https://www.8451.com/area51/)
- [`completejourney` repository](https://github.com/bradleyboehmke/completejourney)
- [`completejourney` CRAN page](https://cran.r-project.org/package=completejourney)
