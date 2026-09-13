# Phase 4 Step 3 — Item-CF results

> **LOCKBOX RECOMMENDATION PERFORMANCE NOT INSPECTED**

## Frozen contract and method

The experiment preserves the next-interaction target, 8,083-instance validation cohort, two-event eligibility, seen-item allowance, full 211,905-item catalog, cold-target misses, and established metrics. No event/recency weights, properties, sessions, negative sampling, or lockbox data are used.

Item-CF builds a binary visitor-item CSR matrix from events strictly before `2015-08-17 03:00 UTC`; repeated events collapse to one. Exact item cosine similarities are derived from sparse co-occurrence. For visitor `u`, candidate `j` receives the sum of its retained cosine similarities to distinct history items. Self-similarity is retained because seen-item recommendations are explicitly allowed. Scores sort descending with item ID ascending; time-safe popularity fills missing slots only.

Validation events never update the matrix or similarities. At this global `T`, visitor history is the same training-only history. Future-training-unknown candidates receive no invented collaborative similarity.

## Matrix and configurations

| Measure | Value |
|---|---:|
| Visitors × items | 1,112,110 × 211,905 |
| Binary nonzeros | 1,695,358 |
| Sparsity | 99.9992806% |
| Retained top-200 directed similarity edges | 7,666,394 |

Exactly three configurations were predeclared: top 50, 100, and 200 neighbors per history item. Selection uses macro NDCG@10 only.

| Neighbors | NDCG@10 | HitRate@10 | HitRate@20 | Coverage@20 |
|---:|---:|---:|---:|---:|
| **50** | **0.191470** | 0.250773 | 0.263640 | 23.6441% |
| 100 | 0.191155 | 0.251516 | 0.263887 | 23.6658% |
| 200 | 0.191037 | 0.250773 | 0.264135 | 23.7191% |

Top 50 is selected; the differences are small, and the grid was not expanded.

## Overall results and popularity comparison

| Metric | @5 | @10 | @20 |
|---|---:|---:|---:|
| HitRate / Recall | 0.229741 | 0.250773 | 0.263640 |
| NDCG | 0.184602 | **0.191470** | 0.194703 |
| MRR | 0.169411 | 0.172285 | 0.173162 |
| Precision | 0.045948 | 0.025077 | 0.013182 |

Versus popularity, NDCG@10 improves by **0.188349 absolute**, or **6,034.0% relative**. HitRate@10 improves by 0.244959 and HitRate@20 by 0.253124. Coverage@20 rises from 0.009438% to 23.6441% (+23.6346 percentage points). This is a clear validation improvement, but it is strongly driven by allowed repeat behavior and does not establish temporal stability.

## Cold/warm and repeat/novel

| Slice | Instances | NDCG@10 | HitRate@10 | HitRate@20 | Popularity NDCG@10 |
|---|---:|---:|---:|---:|---:|
| Warm | 7,627 | 0.202918 | 0.265766 | 0.279402 | 0.003308 |
| Cold | 456 | 0 | 0 | 0 | 0 |
| Previously seen | 2,049 | 0.736489 | 0.940947 | 0.969741 | 0.006462 |
| Novel | 6,034 | 0.006395 | 0.016407 | 0.023865 | 0.001987 |

The aggregate gain is dominated by repeat targets: self-similarity makes previously interacted candidates strong. Novel-target ranking also improves, but remains weak. Cold targets stay in primary metrics as unavoidable misses.

## Target-event and history-depth slices

| Target event | Instances | NDCG@10 | HitRate@10 | HitRate@20 |
|---|---:|---:|---:|---:|
| view | 8,047 | 0.191539 | 0.250777 | 0.263452 |
| addtocart | 32 | 0.147133 | 0.218750 | 0.281250 |
| transaction | 4 | 0.407732 | 0.500000 | 0.500000 |

High-intent slices are descriptive only.

| History | Instances | NDCG@10 | HitRate@10 | HitRate@20 |
|---|---:|---:|---:|---:|
| 2–3 | 4,071 | 0.187902 | 0.217883 | 0.222795 |
| 4–9 | 2,514 | 0.199523 | 0.270485 | 0.278043 |
| 10+ | 1,498 | 0.187653 | 0.307076 | 0.350467 |

Deeper history increases hit rate, although NDCG@10 does not improve monotonically.

## Personalization, fallback, and coverage

- 100% of instances receive at least one nonzero collaborative score.
- 0% require complete popularity fallback.
- 14.0047% require popularity to fill part of the top 20.
- Mean collaboratively scored candidates: 163.04.
- Mean collaborative items in top 20: 18.16.
- Mean top-20 overlap with popularity: 9.4340% (1.89 items).
- 100% of top-20 lists differ from pure popularity.

| K | Unique recommended items | Catalog coverage |
|---|---:|---:|
| 5 | 25,725 | 12.1399% |
| 10 | 37,435 | 17.6659% |
| 20 | 50,103 | 23.6441% |

## Compute profile

Exact sparse similarity construction took approximately 6.39 seconds. Selected-configuration evaluation took 1.33 seconds; the full run including loading, all three configurations, metrics, and artifacts took 31.17 seconds. Approximate peak process RSS was 1,735 MB. No dense item-item or visitor-item score matrix and no large serialized similarity artifact were saved.

## Deterministic error sample

At K=20 there are 2,087 popularity-miss/CF-hit cases, 41 popularity-hit/CF-miss cases, 5,911 both-miss cases, and 44 both-hit cases. The first five visitor IDs in each category were saved without cherry-picking. CF-only hits in that sample are repeat targets, while popularity-only misses are novel targets. Both-miss examples are mostly novel views. These mechanisms are descriptive, not causal.

## Limitations and decision

**Decision: ITEM-CF CLEARLY JUSTIFIED on this validation window.** It materially improves the frozen primary metric and coverage. However, repeat/self-similarity drives much of the result, novel discovery remains difficult, and one window cannot establish temporal stability. Item-CF is not frozen as a final or production model.

One controlled latent-factor challenger is justified next to test whether discovery and representation improve under the unchanged contract. ALS/BPR is not implemented in Step 3.
