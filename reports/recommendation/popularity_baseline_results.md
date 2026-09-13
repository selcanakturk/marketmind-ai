# Phase 4 Step 2 — Popularity baseline results

> **LOCKBOX RECOMMENDATION PERFORMANCE NOT INSPECTED**

## Frozen contract and validation cohort

At `T = 2015-08-17 03:00 UTC`, the baseline ranks all 211,905 items observed through `T` by cumulative all-event count descending, with numeric item ID ascending for ties. It uses no personalization, event/recency weights, properties, categories, sessions, or sampled negatives. Seen items remain candidates.

The validation window ends at `2015-09-01 03:00 UTC`. Its canonical cohort contains exactly 8,083 visitors with at least two history interactions and one next-interaction target strictly after `T`. Each visitor is macro-weighted once.

## Implementation

The evaluator computes one top-20 list per distinct recommendation timestamp and reuses it across visitors because the baseline is global. It never materializes an 8,083 × 211,905 matrix. The generic implementation can process different timestamps independently; counts and item availability always end at that instance's `T`.

## Primary and secondary results

| Metric | @5 | @10 | @20 |
|---|---:|---:|---:|
| HitRate / Recall | 0.004083 | 0.005815 | 0.010516 |
| NDCG | 0.002557 | **0.003121** | 0.004302 |
| MRR | 0.002033 | 0.002269 | 0.002589 |
| Precision | 0.000817 | 0.000581 | 0.000526 |

Macro NDCG@10 is the primary result. Recall and HitRate are identical for one target. Precision@K is `1/K` on a hit and zero otherwise and should not be read as multi-relevance precision.

## Cold and warm targets

| Slice | Instances | NDCG@10 | HitRate@10 | HitRate@20 |
|---|---:|---:|---:|---:|
| All | 8,083 | 0.003121 | 0.005815 | 0.010516 |
| Warm | 7,627 | 0.003308 | 0.006162 | 0.011145 |
| Cold | 456 (5.6415%) | 0 | 0 | 0 |

Cold targets remain in primary metrics. Warm-only results are diagnostic, not a replacement score.

## Repeat versus novel targets

| Slice | Instances | NDCG@10 | HitRate@10 | HitRate@20 |
|---|---:|---:|---:|---:|
| Previously seen | 2,049 | 0.006462 | 0.013177 | 0.020986 |
| Novel to visitor | 6,034 | 0.001987 | 0.003315 | 0.006961 |

Global popularity performs better on repeat behavior but remains weak on both slices. This is descriptive and does not change the frozen seen-item policy.

## Target-event slices

| Target event | Instances | NDCG@10 | HitRate@10 | HitRate@20 |
|---|---:|---:|---:|---:|
| view | 8,047 | 0.003135 | 0.005841 | 0.010439 |
| addtocart | 32 | 0 | 0 | 0.031250 |
| transaction | 4 | 0 | 0 | 0 |

High-intent slices are too small for model selection claims.

## History-depth slices

| Prior interactions | Instances | NDCG@10 | HitRate@10 | HitRate@20 |
|---|---:|---:|---:|---:|
| 2–3 | 4,071 | 0.003599 | 0.006632 | 0.010563 |
| 4–9 | 2,514 | 0.002822 | 0.005171 | 0.011138 |
| 10+ | 1,498 | 0.002326 | 0.004673 | 0.009346 |

The non-personalized baseline does not improve with deeper visitor history, reinforcing—but not proving—the motivation for personalization.

## Catalog coverage and concentration

| K | Unique recommended | Coverage of 211,905-item catalog |
|---|---:|---:|
| 5 | 5 | 0.002360% |
| 10 | 10 | 0.004719% |
| 20 | 20 | 0.009438% |

Item 5,411 is first for all 8,083 visitors. The globally top-ten items occupy 50% of all top-20 slots; the top twenty occupy 100%. This concentration is expected from the frozen global baseline, not an implementation error.

## Compute profile and artifacts

On the audit machine, canonical instance construction took 3.23 seconds, ranking plus metrics 2.58 seconds, and the complete run 9.76 seconds. Peak process RSS was approximately 1,085 MB, dominated by loading and validating the 2.76-million-row event table rather than ranking. Compact artifacts total about 2.8 MB: instances 753 KB, top-20 1.34 MB, per-instance metrics 707 KB, and summary 8.4 KB. Full-catalog popularity evaluation is operationally feasible without a dense score matrix.

## Leakage and sanity checks

- exactly 8,083 unique visitors and one target per instance;
- target timestamp strictly after `T` and before lockbox start;
- history and popularity counts end at or before `T`;
- the lockbox is removed before validation construction/evaluation;
- candidate availability follows first observation through `T`;
- top-20 has unique items and deterministic numeric-ID tie ordering;
- cold targets remain misses;
- future events cannot change an earlier ranking;
- no lockbox recommendation list or performance metric exists.

## Limitations and Step 3 decision

The baseline is deliberately non-personalized, heavily popularity-concentrated, view-dominated, and unable to rank new items. It establishes the canonical validation pipeline and a low but valid reference point. Step 3 may now evaluate a simple collaborative approach under the unchanged temporal, full-catalog, eligibility, seen-item, and metric contract. No collaborative family is selected here.
