# Phase 4 Step 5 — Final recommendation lockbox results

> **THE RECOMMENDATION LOCKBOX IS NOW PERMANENTLY CONSUMED.**

## Frozen system and pre-lockbox refit

The final research system is unchanged Item-CF: binary visitor-item pairs, exact sparse cosine, top 50 neighbors, summed similarities across distinct history items, retained self-similarity, seen items allowed, score descending/item-ID ascending, and time-safe all-event popularity fill. There are no weights, recency, metadata, categories, sessions, latent factors, or reranking.

After freezing that specification from validation, the similarity graph was rebuilt once from all events strictly before `2015-09-01 03:00 UTC`. This is a historical refit, not new validation or model selection.

| Pre-lockbox matrix | Value |
|---|---:|
| Visitors | 1,252,335 |
| Items | 223,121 |
| Binary nonzeros | 1,907,798 |
| Sparsity | 99.9993172% |
| Retained directed similarity edges | 3,182,149 |

## Ordering guarantee

The specification was frozen, the pre-lockbox graph was built, and 9,085 target-free rankings were generated. `lockbox_item_cf_top20_preoutcome.csv` was durably written with only visitor, timestamp, and rank fields. Only afterward were target item/event fields joined and metrics computed. The pre-outcome artifact remains separate and was not overwritten.

All instances share the frozen global `T = 2015-09-01 03:00 UTC`; therefore no lockbox event precedes `T` or enters visitor history. The general history-update allowance is inactive for this cohort. No lockbox event updates similarity.

## Lockbox cohort and primary results

- Instances: **9,085**
- Warm targets: **8,560**
- Cold targets: **525 (5.7788%)**, retained as misses
- Repeat targets: **2,047 (22.5316%)**
- Novel targets: **7,038 (77.4684%)**

| Item-CF metric | @5 | @10 | @20 |
|---|---:|---:|---:|
| HitRate / Recall | 0.205944 | 0.223996 | 0.235223 |
| NDCG | 0.165259 | **0.171158** | 0.173970 |
| MRR | 0.151585 | 0.154057 | 0.154814 |
| Precision | 0.041189 | 0.022400 | 0.011761 |

## Popularity context

Frozen popularity achieves NDCG@10 **0.003090**, HitRate@10 0.005834, and HitRate@20 0.010347. Item-CF's NDCG advantage is **+0.168068 absolute / +5,438.63% relative**; HitRate advantages are +0.218162 at 10 and +0.224876 at 20. Popularity coverage@20 is 0.008964%; Item-CF exceeds it by 24.2684 percentage points.

## Development-to-lockbox gap

| Metric | Development | Lockbox | Absolute gap | Relative gap |
|---|---:|---:|---:|---:|
| NDCG@10 | 0.191470 | 0.171158 | −0.020312 | −10.6086% |
| HitRate@10 | 0.250773 | 0.223996 | −0.026778 | −10.6780% |
| HitRate@20 | 0.263640 | 0.235223 | −0.028417 | −10.7787% |
| Coverage@20 | 23.6441% | 24.2774% | +0.6333 pp | +2.6786% |

The ranking metrics decline moderately while the large popularity advantage and broad coverage persist. No post-hoc acceptance threshold is applied.

## Repeat/novel and warm results

| Slice | Instances | Share | NDCG@10 | HitRate@10 | HitRate@20 |
|---|---:|---:|---:|---:|---:|
| Repeat | 2,047 | 22.5316% | 0.739078 | 0.943332 | 0.972643 |
| Novel | 7,038 | 77.4684% | 0.005979 | 0.014777 | 0.020745 |
| Warm | 8,560 | 94.2212% | 0.181655 | 0.237734 | 0.249650 |
| Cold | 525 | 5.7788% | 0 | 0 | 0 |

Validation repeat/novel NDCG@10 was 0.736489/0.006395. Repeat-heavy behavior generalizes almost unchanged; novel ranking remains weak and is modestly lower. Self-similarity remains unchanged.

## Target-event and history-depth slices

| Target event | Instances | NDCG@10 | HitRate@10 | HitRate@20 |
|---|---:|---:|---:|---:|
| view | 9,033 | 0.172040 | 0.225064 | 0.236356 |
| addtocart | 51 | 0.018249 | 0.039216 | 0.039216 |
| transaction | 1 | 0 | 0 | 0 |

High-intent slices remain too small for decisions.

| History | Instances | NDCG@10 | HitRate@10 | HitRate@20 |
|---|---:|---:|---:|---:|
| 2–3 | 4,487 | 0.164386 | 0.192556 | 0.198128 |
| 4–9 | 2,950 | 0.179442 | 0.240678 | 0.244407 |
| 10+ | 1,648 | 0.174767 | 0.279733 | 0.319782 |

Hit rate rises with history depth; NDCG peaks in the middle bucket.

## Personalization, discovery, and coverage

- Collaborative-score availability: 100%
- Complete popularity fallback: 0%
- Partial popularity fill: 12.0308%
- Mean collaboratively scored candidates: 164.22
- Mean top-20 overlap with popularity: 8.1079% (1.62 items)
- Lists differing from popularity: 100%
- Top-20 previously seen slot share: 20.5757%
- Top-20 novel slot share: 79.4243%

| K | Unique items | Catalog coverage |
|---|---:|---:|
| 5 | 27,876 | 12.4937% |
| 10 | 40,404 | 18.1086% |
| 20 | 54,168 | 24.2774% |

## Compute profile and artifacts

Similarity construction took 7.28 seconds, target-free lockbox ranking 1.82 seconds, and the complete run 42.85 seconds. Approximate peak process RSS was 1,722 MB. The pre-outcome ranking is 1,506,116 bytes; scored evaluation is 1,179,887 bytes; slices are 3,351 bytes. No dense similarity structure was serialized.

## Generalization assessment

**STRONG GENERALIZATION.** Primary ranking quality declines about 10.6% from development, but remains vastly above frozen popularity; repeat behavior, ranking sanity, zero complete fallback, and broad/slightly improved coverage persist. Novel discovery remains the principal limitation. This qualitative assessment does not alter the model.

## Permanent warning

Model search is closed. Neighborhood size, self-similarity, similarity, aggregation, eligibility, seen-item policy, target, K, and fallback remain unchanged. No post-lockbox tuning or model change occurred. These lockbox results can never again be presented as fresh evaluation evidence.
