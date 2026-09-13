# Phase 4 Step 4 — Controlled implicit ALS results

> **LOCKBOX RECOMMENDATION PERFORMANCE NOT INSPECTED**

## Frozen contract and ALS method

The three ALS models use only binary visitor-item pairs from events strictly before `2015-08-17 03:00 UTC`. Repeated events collapse to one; all event types have equal weight and confidence scale 1.0. Validation events never refit user or item factors. Seen items remain eligible, cold targets remain misses, and primary evaluation ranks the full trained catalog without sampled negatives, metadata, recency, or sessions.

The implementation uses `implicit==0.7.2` CPU Alternating Least Squares with random seed 42 and one thread. Known visitors use their training-period factors. Unknown visitors would receive deterministic point-in-time popularity; items without trained factors can only enter through popularity fill. At the frozen global validation timestamp, all eligible visitors and candidate items are training-known, so no fallback is needed. Later validation interactions do not arise before this single global `T`; future deployments would retain the training factor rather than refit from validation activity.

## Training matrix and configurations

| Measure | Value |
|---|---:|
| Shape | 1,112,110 visitors × 211,905 items |
| Binary nonzeros | 1,695,358 |
| Sparsity | 99.9992806% |

| Config | Factors | Regularization | Iterations | Alpha | NDCG@10 | Coverage@20 |
|---|---:|---:|---:|---:|---:|---:|
| ALS-1 | 32 | 0.01 | 15 | 1.0 | 0.019326 | 1.2067% |
| ALS-2 | 64 | 0.01 | 15 | 1.0 | 0.025014 | 1.5936% |
| **ALS-3** | **64** | **0.05** | **20** | **1.0** | **0.025085** | **1.6243%** |

ALS-3 is selected by macro NDCG@10. No parameter search was added.

## Overall results and three-way comparison

| Metric | @5 | @10 | @20 |
|---|---:|---:|---:|
| HitRate / Recall | 0.030063 | 0.045899 | 0.061487 |
| NDCG | 0.020003 | **0.025085** | 0.029017 |
| MRR | 0.016724 | 0.018798 | 0.019873 |
| Precision | 0.006013 | 0.004590 | 0.003074 |

| Model | NDCG@10 | HitRate@10 | HitRate@20 | Coverage@20 |
|---|---:|---:|---:|---:|
| Popularity | 0.003121 | 0.005815 | 0.010516 | 0.009438% |
| **Item-CF** | **0.191470** | **0.250773** | **0.263640** | **23.6441%** |
| ALS-3 | 0.025085 | 0.045899 | 0.061487 | 1.6243% |

ALS improves over popularity by 0.021964 absolute and 703.64% relative NDCG@10. It trails Item-CF by 0.166385 absolute and 86.90% relative. The magnitude clearly favors Item-CF.

## Cold/warm, repeat/novel, and event slices

| Slice | Instances | NDCG@10 | HitRate@10 | HitRate@20 | Item-CF NDCG@10 |
|---|---:|---:|---:|---:|---:|
| Warm | 7,627 | 0.026585 | 0.048643 | 0.065163 | 0.202918 |
| Cold | 456 | 0 | 0 | 0 | 0 |
| Repeat target | 2,049 | 0.083166 | 0.150805 | 0.196193 | 0.736489 |
| Novel target | 6,034 | 0.005362 | 0.010275 | 0.015744 | 0.006395 |

ALS sharply reduces repeat performance and also falls below Item-CF on novel-target NDCG@10. It therefore does not achieve the desired ranking balance.

| Target event | Instances | NDCG@10 | HitRate@10 | HitRate@20 |
|---|---:|---:|---:|---:|
| view | 8,047 | 0.024902 | 0.045607 | 0.061265 |
| addtocart | 32 | 0.064425 | 0.093750 | 0.093750 |
| transaction | 4 | 0.078866 | 0.250000 | 0.250000 |

High-intent slices are descriptive only.

## History depth

| Prior interactions | Instances | NDCG@10 | HitRate@10 | HitRate@20 |
|---|---:|---:|---:|---:|
| 2–3 | 4,071 | 0.022379 | 0.039302 | 0.052076 |
| 4–9 | 2,514 | 0.024607 | 0.046937 | 0.063246 |
| 10+ | 1,498 | 0.033240 | 0.062083 | 0.084112 |

ALS improves with deeper history but remains below Item-CF in every history bucket.

## Fallback, discovery, overlap, and coverage

- 100% receive ALS recommendations.
- Complete popularity fallback: 0%.
- Partial popularity fill: 0%.
- The evaluator retrieves exactly 20 latent-ranked candidates per known visitor; total finite candidate-score counts are deliberately not materialized.
- ALS top-20 slots: 2.8269% previously seen and 97.1731% novel.
- Item-CF top-20 slots: 20.8227% previously seen and 79.1773% novel.
- Mean top-20 overlap with Item-CF: 5.8691% (1.17 items).
- Mean overlap with popularity: 10.6248% (2.12 items).
- 99.9876% of lists differ from Item-CF; 100% differ from popularity.

| K | Unique ALS items | Coverage |
|---|---:|---:|
| 5 | 905 | 0.4271% |
| 10 | 1,800 | 0.8494% |
| 20 | 3,442 | 1.6243% |

ALS creates a more novel recommendation mix than Item-CF, but substantially narrower catalog coverage and weaker novel-target retrieval.

## Compute profile

ALS-3 fit took 86.06 seconds and validation scoring 3.93 seconds. The complete three-configuration run took 207.19 seconds with approximately 1,554 MB peak RSS. User factors are 1,112,110 × 64 and item factors 211,905 × 64. The serialized ALS-3 estimator is 338,951,235 bytes (about 323.2 MiB). Only compact experiment outputs are retained; the measured temporary model was not added to the repository.

## Error analysis

At K=20, ALS hits 80 targets missed by Item-CF, while Item-CF hits 1,714 missed by ALS; both hit 417 and both miss 5,872. The first five visitor IDs in each category were saved deterministically, with repeat/novel labels, rather than selected to favor a model. The imbalance is consistent with the aggregate preference for Item-CF; individual ALS-only successes do not offset its much larger loss set.

## Decision and limitations

**Final family decision: ITEM-CF REMAINS PREFERRED.** ALS-3 beats popularity but is substantially worse than Item-CF on overall, repeat, novel-target, hit-rate, and coverage evidence while requiring a much larger factor artifact. One validation window still cannot establish temporal stability, and Item-CF's repeat/self-similarity dependence remains a limitation.

Further recommender-family search is not justified at this stage. The controlled popularity → Item-CF → ALS comparison answers the family question sufficiently for review. No BPR, LightFM, neural, embedding, or metadata model should be introduced before the next explicit decision step.
