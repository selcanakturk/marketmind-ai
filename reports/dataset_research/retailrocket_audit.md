# RetailRocket Recommendation Dataset Audit

## Dataset Identity

This audit uses the canonical [RetailRocket Recommender System Dataset](https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset), downloaded without substitution from Kaggle. It contains anonymized events from a real e-commerce site and was published for implicit-feedback recommendation research.

Files inspected under the Git-ignored `data/raw/retailrocket/` directory:

- `events.csv`
- `category_tree.csv`
- `item_properties_part1.csv`
- `item_properties_part2.csv`

The two item-property files are partitions of one logical timestamped change log. Property values other than documented category/availability fields are hashed. The Kaggle distribution lists CC BY-NC-SA 4.0; public-portfolio attribution, non-commercial, and share-alike obligations should be reviewed before publication.

## Dataset Integrity

| File | Rows | Columns | Disk | Deep Pandas memory | Exact duplicate rows |
|---|---:|---:|---:|---:|---:|
| `events.csv` | 2,756,101 | 5 | 89.87 MB | 86.74 MB | 460 |
| `category_tree.csv` | 1,669 | 2 | 0.014 MB | 0.026 MB | 0 |
| `item_properties_part1.csv` | 10,999,999 | 4 | 461.88 MB | 1,419.01 MB | 0 |
| `item_properties_part2.csv` | 9,275,903 | 4 | 389.99 MB | 1,197.10 MB | 0 |

The event table has no guaranteed event ID. The full event-field combination has 918 rows belonging to duplicate groups and 460 duplicate copies. Timestamp/item/property is unique within each item-property part. Category ID is unique in the category tree; 25 categories have no parent and represent roots.

Missingness is structurally concentrated:

- Event timestamp, visitor, event type, and item are complete.
- `transactionid` is absent on 2,733,644 events (99.185%) because it applies to transaction events; it is present on all 22,457 transaction events.
- Property-part fields are complete.
- Category-tree `parentid` is missing for 25 root nodes (1.498%), and every non-null parent exists as a category node.

Observed grain is one timestamped visitor-item event, one category-parent relation, and one timestamped item-property change-log row. Duplicate events should be investigated, not removed automatically.

## Temporal Coverage

- **Earliest event:** 2015-05-03 03:00:04.384 UTC
- **Latest event:** 2015-09-18 02:59:47.788 UTC
- **Duration:** 137.9998 days
- **Active calendar days:** 139
- **Zero-event days:** 0

The first and last UTC days are incomplete. The last day contains only 1,479 views, 34 cart additions, and 15 transactions; it should not be treated as a normal complete day. Weekly activity is continuous, but the first and last weekly buckets are partial.

Event distribution:

| Event | Count | Percentage |
|---|---:|---:|
| View | 2,664,312 | 96.6696% |
| Add to cart | 69,332 | 2.5156% |
| Transaction | 22,457 | 0.8148% |

These are behavior frequencies, not causal funnel conversion probabilities.

## Visitor Identity

The dataset contains **1,407,580 visitor IDs**, but it does not establish that they represent registered customers, individuals across devices, or identities persistent after browser-cookie changes.

| Activity measure | Result |
|---|---:|
| Median events per visitor | 1 |
| Mean events | 1.958 |
| 75th percentile | 2 |
| 90th percentile | 3 |
| Maximum | 7,757 |
| Exactly 1 event | 71.1548% |
| At least 2 events | 28.8453% |
| At least 5 events | 5.7986% |
| At least 10 events | 1.6511% |
| Active on multiple days | 10.2139% |

Median active span is zero days and median active-day count is one. The 90th-percentile span is still below one day (0.48 days); only at the 95th percentile does it reach 10.31 days. No explicit session ID exists, so the audit does not invent a session timeout. Repeat-day behavior is measurable; durable customer behavior is not established.

## Item Interaction Structure

There are **235,061 event items**.

- Median events per item: 3; mean: 11.73; maximum: 3,412.
- Median distinct visitors per item: 2.
- 31.3149% of items have one event.
- 65.8395% have five or fewer events.
- The most active 1% of items receive 22.9546% of all events.
- The top ten items receive 0.7451%.

This is a pronounced long tail. Items with little evidence should remain visible in evaluation and fallback analysis rather than being silently removed.

## Event Funnel

| Stage | Visitors | Items | Events |
|---|---:|---:|---:|
| View | 1,404,179 | 234,838 | 2,664,312 |
| Add to cart | 37,722 | 23,903 | 69,332 |
| Transaction | 11,719 | 12,025 | 22,457 |

Among visitor-item pairs, using timestamps to require that at least one later-stage event follows an earlier-stage event:

- 45,810 pairs have a view followed by a cart event.
- 19,003 have a cart event followed by a transaction.
- 18,778 have a view followed by a transaction.

The counts use earliest source and latest destination timestamps so valid later transitions are not missed when several events occur. They describe observed sequences only. They do not demonstrate that a view or cart caused purchase.

## User-Item Sparsity

| Scope | Visitors | Items | Distinct pairs | Sparsity | Median pairs/visitor | Median visitors/item |
|---|---:|---:|---:|---:|---:|---:|
| All events | 1,407,580 | 235,061 | 2,145,179 | 99.999352% | 1 | 2 |
| Transactions only | 11,719 | 12,025 | 21,270 | 99.984906% | 1 | 1 |

All-event mean pairs are 1.524 per visitor and 9.126 per item. Transaction-only means are 1.815 per buyer and 1.769 buyers per purchased item. Rich event semantics do not eliminate matrix sparsity.

## Transaction Behavior

- Purchasing visitors: 11,719, only 0.833% of all visitor IDs.
- Median/mean transaction events per buyer: 1 / 1.916.
- 21.9814% of buyers have at least two transaction events.
- Median distinct purchased items: 1; 18.5511% buy at least two distinct items.
- Median observed purchasing span: 0 days; 17.9794% span more than one timestamp day.
- 1,187 transaction events repeat a visitor-product pair beyond its first occurrence.

Purchase-event intervals are mostly within a shopping occasion: median 0.0057 days (about 8.2 minutes), 90th percentile 0.796 days, 95th percentile 3.90 days, and 99th percentile 32.56 days. Transaction behavior alone is much thinner than Complete Journey and is poorly suited to long-term repeat-purchase personalization. RetailRocket’s value comes primarily from the full implicit-feedback stream.

## Temporal Evaluation Feasibility

Three fixed elapsed-time cutoffs were tested descriptively; none was optimized or selected.

| Cutoff | Eligible visitors: ≥2 history + future | ≥5 + future | ≥10 + future |
|---:|---:|---:|---:|
| 60% (2015-07-24) | 15,808 | 5,567 | 2,425 |
| 75% (2015-08-14) | 13,378 | 4,944 | 2,203 |
| 90% (2015-09-04) | 7,921 | 3,226 | 1,530 |

A warm-user temporal ranking evaluation is feasible for thousands of visitors, including stricter history cohorts. However, it represents a small selected fraction of the full visitor population. Any later protocol must preserve chronology, avoid random splitting, report eligibility and coverage, and prevent future item/property information from entering historical features.

## Cold Start

| Cutoff | Future visitors unseen | Future items unseen | Future events with unseen visitor | Future events with unseen item |
|---:|---:|---:|---:|---:|
| 60% | 94.2785% | 27.5659% | 88.9805% | 9.8391% |
| 75% | 92.4141% | 20.5792% | 86.4053% | 7.6046% |
| 90% | 89.5604% | 13.2038% | 82.8154% | 5.9233% |

Visitor cold start is the dominant system condition, while unseen items affect a smaller but still important event share. Collaborative filtering alone cannot serve most future visitor IDs. A later design would need:

- a popularity or trend baseline for anonymous/new visitors;
- warm-user collaborative or sequential methods only where history exists;
- category/property-aware fallbacks for new or low-support items;
- separate warm-start and cold-start metrics rather than excluding difficult cases.

## Item Metadata

The two property parts contain **20,275,902 rows**, **417,053 items**, and **1,104 property labels**. Metadata timestamps span 2015-05-10 to 2015-09-13 UTC, narrower than event coverage at both boundaries.

- 78.8076% of the 235,061 event items have any property record.
- The same 78.8076% have documented category and availability properties.
- `categoryid` has 788,214 change-log rows.
- `available` has 1,503,639 change-log rows.
- The category tree has 1,669 nodes and 25 roots.

Metadata can support category-aware and availability-aware fallbacks for covered items. Other property labels/values are hashed; their semantic meaning and numerical interpretation must not be invented. Properties change over time, so a future hybrid system must use the last value known before the evaluation cutoff rather than future snapshots. Roughly 21.19% of event items lack metadata coverage.

## Computational Feasibility

- Total raw disk footprint: **941.75 MB** (approximately 960 MB filesystem usage).
- Event table: 89.87 MB on disk and 86.74 MB in the selected Pandas dtypes.
- Property part 1: 461.88 MB on disk, approximately 1.42 GB in memory.
- Property part 2: 389.99 MB on disk, approximately 1.20 GB in memory.
- Retaining all four tables would require approximately 2.70 GB before intermediates.

Local Pandas processing is practical for events and category data. Metadata should be scanned sequentially or in chunks and filtered by relevant items, properties, and temporal cutoffs. No distributed technology is empirically required.

## Empirical Comparison with Complete Journey 2.0

| Dimension | RetailRocket | Complete Journey 2.0 |
|---|---:|---:|
| Users/households | 1,407,580 visitors | 2,469 households |
| Products in interactions | 235,061 | 68,509 |
| Distinct all/purchase pairs | 2,145,179 all; 21,270 transaction-only | 867,688 purchase pairs |
| Sparsity | 99.99935% all; 99.98491% purchases | 99.48703% purchases |
| Temporal depth | 138 days | 364-day endpoint span |
| Median interaction depth | 1 pair/visitor | 277 products/household |
| Behavioral events | View, cart, transaction | Purchases plus coupon/promotion context |
| Repeat purchasing | 21.98% of buyers have ≥2 transaction events; spans usually same-day | 98.74% of households have ≥2 baskets; median 43 baskets |
| Item metadata | Hashed time-varying properties, category tree, availability; 78.81% event-item coverage | Interpretable product hierarchy/brand plus store, discount, campaign context |
| Cold start | Extremely high visitor cold start | Selected established household panel; weak representation of new users |
| Temporal ranking potential | Strong for event/sequential and cold-start methodology on eligible cohorts | Strong for repeated purchase/replenishment ranking |
| Local cost | ~942 MB raw; property scan ~2.6 GB memory | 37 MB compressed; promotions ~2.28 GB memory |
| Domain fit | Direct e-commerce behavior | Grocery retail, household purchases |

RetailRocket teaches a materially different recommendation problem: anonymous, short-lived e-commerce intent with multi-stage implicit feedback and severe cold start. Complete Journey teaches repeated purchase preference and replenishment behavior for known households. RetailRocket is not automatically superior in every recommendation setting; transaction-only evidence is far weaker than Complete Journey.

## Known Limitations

- Only about 4.5 months of events.
- Visitor identity is anonymous and may not be durable across browsers/devices.
- 71.15% of visitors appear once; only 10.21% appear on multiple days.
- Only 0.815% of events are transactions.
- Extreme user-item sparsity and visitor cold start.
- Metadata are hashed, incomplete for event items, and do not cover temporal boundaries fully.
- 460 exact duplicate event rows.
- No explicit session ID, quantities, recoverable monetary price, returns, customer demographics, on-hand inventory, lead time, or replenishment.
- Binary availability is not an inventory ledger.
- Funnel relationships are observational, not causal.

## RetailRocket Recommendation Verdict

**Recommendation suitability: Strong**, specifically for implicit-feedback, session/sequence-oriented, temporal, and cold-start-aware recommendation methodology. This rating does not apply to long-term customer purchase personalization.

| MarketMind module | Rating | Empirical basis |
|---|---|---|
| Recommendation | **Strong** | 2.15M distinct event pairs, view/cart/purchase stages, chronology, and thousands of eligible warm visitors; severe cold start creates a realistic evaluation requirement. |
| Customer Segmentation | **Weak** | Behavioral segments are possible, but median one event and uncertain visitor persistence prevent robust customer-lifecycle profiles. |
| Customer Return Risk | **Unsupported** | Short observation, anonymous identity, 71.15% one-event visitors, and no durable customer/closure definition. |
| Demand Forecasting | **Weak** | Short period, only 22,457 purchase events, and no quantities or interpretable price. |
| Inventory Intelligence | **Unsupported** | Availability is binary; no on-hand quantity, lead time, or replenishment. |
| Sales Anomaly Detection | **Weak** | Event traffic anomalies may be explored, but sparse transactions and 138-day depth are weak for sales anomalies. |

RetailRocket appears to provide enough additional methodological value to justify consideration as a separate recommendation dataset: it uniquely supplies e-commerce views, carts, purchases, timestamped item properties, and an empirically severe cold-start setting. The cost is a third domain/schema, about 942 MB of raw data, and a recommendation population mostly unsuitable for warm personalization. Whether that tradeoff belongs in the final architecture remains a deliberate project decision, not an automatic selection made by this audit.
