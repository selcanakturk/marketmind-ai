# Phase 4 Step 1 — RetailRocket recommendation audit

All figures use the authentic local files. No recommender or ranking was produced.

## Files, properties, and categories

| File | Rows | Schema | Missing |
|---|---:|---|---|
| `events.csv` | 2,756,101 | timestamp, visitorid, event, itemid, transactionid | 2,733,644 transaction IDs; zero mandatory |
| `item_properties_part1.csv` | 10,999,999 | timestamp, itemid, property, value | none |
| `item_properties_part2.csv` | 9,275,903 | timestamp, itemid, property, value | none |
| `category_tree.csv` | 1,669 | categoryid, parentid | 25 root parents |

Events have 460 exact duplicates: 94 views and 366 carts, none transactions. Properties total 20,275,902 rows, 417,053 items, 1,104 keys, and 18 timestamps from 2015-05-10 03:00 to 2015-09-13 03:00 UTC. There are 12,003,814 item-property pairs; 514,679 (4.2876%) repeat and account for 8,786,767 rows, with at most 18 records per pair. Values are opaque: 7,331,908 contain space-separated tokens and 5,175,116 contain `n...` numeric encodings. `available` has 1,503,639 rows/two values and `categoryid` 788,214 rows/1,242 values; both cover all property items and repeat up to 18 times.

The category tree contains 1,669 unique categories, 362 parent IDs, 25 roots, no missing referenced parents, self-links, or cycles, and maximum depth five. Depth 0–5 counts are 25, 174, 702, 665, 90, 13.

## Events

| Event | Events | Share | Visitors | Items | Per-visitor median/p95/max | Per-item median/p95/max |
|---|---:|---:|---:|---:|---:|---:|
| view | 2,664,312 | 96.6696% | 1,404,179 | 234,838 | 1/5/6,479 | 3/46/3,410 |
| addtocart | 69,332 | 2.5156% | 37,722 | 23,903 | 1/4/719 | 2/9/306 |
| transaction | 22,457 | 0.8148% | 11,719 | 12,025 | 1/4/559 | 1/5/133 |

Only transactions have transaction IDs: 17,672 distinct IDs. Each ID maps to one visitor; 2,710 IDs have multiple rows, 2,643 multiple items, and 134 repeat the same visitor-item. Rows do not safely imply quantity.

## Time

The event range is 2015-05-03 03:00:04.384–2015-09-18 02:59:47.788 UTC (137 days 23:59:43.404). At the source's 03:00 boundary there are 138 complete days.

| Daily | Min | Median | Mean | Max |
|---|---:|---:|---:|---:|
| events | 10,140 | 20,261 | 19,971.75 | 33,937 |
| visitors | 6,270 | 12,288 | 11,948.64 | 18,072 |
| items | 6,926 | 12,489 | 12,113.14 | 15,983 |
| transactions | 51 | 162 | 162.73 | 278 |

Weekly variation is visible; no empty day or major internal gap exists. Activity supports chronological evaluation.

## Visitors

There are 1,407,580 visitors. Total-event p25/p50/p75/p90/p95/p99/max are 1/1/2/3/5/13/7,757; unique-item values are 1/1/1/2/3/8/3,814; active-day values are 1/1/1/2/2/4/131. Active-span p50/p90/p95/p99/max days are 0/0.480/10.310/69.089/137.973.

| Activity | Visitors | Share |
|---|---:|---:|
| exactly 1 event | 1,001,560 | 71.1547% |
| ≥2 / ≥3 / ≥5 / ≥10 | 406,020 / 200,028 / 81,620 / 23,241 | 28.8453% / 14.2108% / 5.7986% / 1.6511% |
| ≥1 transaction | 11,719 | 0.8326% |
| ≥2 transaction events | 2,576 | 0.1830% |

Personalization is feasible for a meaningful minority; cold start is unavoidable.

## Items and long tail

There are 235,061 items. Median activity is three events/two visitors; 73,609 (31.3149%) have one event. Event p75/p95/p99/max are 9/47/143/3,412; visitor values are 7/36/105/2,912.

| Top share | Views | Transactions |
|---|---:|---:|
| 1% | 22.7170% | 48.1943% |
| 5% | 48.9056% | 98.7932% |
| 10% | 63.5737% | 100.0000% |

Only 12,025 items transact. Popularity bias and catalog coverage therefore require reporting.

## Repeats and descriptive progression

Of 2,145,179 visitor-item pairs, 333,038 (15.5250%) repeat and 306,592 (14.2921%) have repeated views. View/cart, cart/transaction, view/transaction co-occurrence counts are 49,500, 19,045, 19,051. An earlier source precedes a later target in 45,804/49,500 (92.5333%), 19,003/19,045 (99.7795%), and 18,778/19,051 (98.5670%), respectively. These are descriptive sequences, not causal funnels.

## Objectives and temporal feasibility

| Objective | Later events after prior event | Visitors | Validation raw/eligible ≥2 | Lockbox raw/eligible ≥2 |
|---|---:|---:|---:|---:|
| next item | 1,348,417 | 405,966 | 155,213/8,083 | 172,159/9,085 |
| next high-intent item | 86,218 | 35,189 | 4,367/365 | 4,449/396 |
| next transaction item | 22,335 | 11,616 | 1,335/156 | 1,284/160 |

High-intent targets are valuable but too sparse for the first global-cutoff evaluation. Next-item is selected despite view dominance; event-type slices remain visible.

| Partition | UTC half-open interval | Days | Events | Visitors | Items | Views | Carts | Tx |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| train | May 3 03:00–Aug 17 03:00 | 106 | 2,182,090 | 1,112,110 | 211,905 | 2,110,079 | 54,350 | 17,661 |
| validation | Aug 17 03:00–Sep 1 03:00 | 15 | 272,934 | 155,213 | 77,186 | 263,143 | 7,342 | 2,449 |
| lockbox | Sep 1 03:00–Sep 18 03:00 | 17 | 301,077 | 172,159 | 81,766 | 291,090 | 7,640 | 2,347 |

Training contains 751,563 sequential next-event examples across 157,640 visitors after two prior events. Validation retention for ≥1/2/3/5 prior events is 14,988/8,083/5,479/3,180; lockbox is 16,914/9,085/6,127/3,609. A two-event minimum is frozen; a two-unique-item rule would unnecessarily reduce validation to 6,610.

At validation `T`, the time-safe catalog has 211,905 items. Targets are 2,049 (25.3495%) previously seen and 6,034 novel; 456 (5.6415%) are globally new/unrankable. At lockbox `T`, the catalog has 223,121 items; permitted feasibility counts show 2,047/9,085 (22.5316%) repeat and 525 (5.7788%) globally new targets. No lockbox ranking or metric was computed.
