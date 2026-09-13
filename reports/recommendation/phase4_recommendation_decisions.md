# Phase 4 recommendation decisions

| Decision | Frozen outcome |
|---|---|
| Objective | rank the next-interaction item; high-intent targets deferred because eligible validation is sparse |
| Prediction unit | one visitor at explicit UTC time `T` |
| Instance | history through `T`; first item in `(T, window_end)` is the single target |
| Train | `[2015-05-03 03:00, 2015-08-17 03:00)` UTC |
| Validation | `[2015-08-17 03:00, 2015-09-01 03:00)`; 8,083 eligible instances |
| Lockbox | `[2015-09-01 03:00, 2015-09-18 03:00)`; 9,085 feasible instances; rankings untouched |
| Eligibility | at least two prior interactions; no unique-item minimum |
| Seen items | allowed; report repeat and novel slices |
| Candidates | full catalog observed at or before `T` |
| Cold start | new visitors outside personalized evaluation; new-item targets retained as misses and reported |
| Event semantics | no numeric weights; conceptual later order transaction > cart > view |
| Popularity baseline | all-event count through `T` descending; item ID ascending tie-break; no recency/weight tuning |
| Metrics | primary macro NDCG@10; Recall/HitRate, NDCG, MRR, Precision at K=5/10/20; coverage and target slices |
| Ranking scope | full catalog; no sampled-negative primary evaluation |
| Properties | latest state at or before `T`, never future final state |
| Sessions | no sessionization; longer-term preference first |
| Split | global chronology only; no random interaction split |

Unresolved: Step 2 baseline family, limited event-weight candidates, and full-catalog runtime; later property encoding, session-aware modeling, metadata cold start, visitor fallback implementation, and serving.

## Step 2 popularity baseline

| Decision/evidence | Outcome |
|---|---|
| Canonical validation pipeline | established with exactly 8,083 single-target instances |
| Frozen baseline | executed unchanged: cumulative all-event count through `T`, item-ID tie-break |
| Primary result | macro NDCG@10 = 0.003121 |
| Recall/HitRate | @5 0.004083; @10 0.005815; @20 0.010516 |
| Cold targets | 456/8,083 (5.6415%), retained as zero-result misses |
| Warm diagnostic | NDCG@10 0.003308; HitRate@10 0.006162 |
| Coverage | 5/10/20 unique items at K=5/10/20; 0.002360%/0.004719%/0.009438% |
| Full catalog | feasible without dense matrix; approximately 9.76 seconds and 1,085 MB peak process RSS |
| Lockbox | recommendation rankings and performance remain untouched |
| Next question | whether a simple personalized collaborative baseline improves validation ranking and coverage |

No collaborative model is selected, and event weighting remains unresolved.
