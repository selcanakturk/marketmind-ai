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

## Step 4 controlled implicit ALS challenger

| Decision/evidence | Outcome |
|---|---|
| Dependency | `implicit==0.7.2`, CPU ALS, random seed 42, one thread |
| Representation | unchanged binary training-period visitor-item matrix; alpha 1.0 |
| Configurations | ALS-1 32/0.01/15; ALS-2 64/0.01/15; ALS-3 64/0.05/20 |
| Selected ALS | ALS-3 by macro NDCG@10 |
| ALS validation | NDCG@10 0.025085; HitRate@10 0.045899; HitRate@20 0.061487 |
| Versus popularity | +0.021964 absolute / +703.64% relative NDCG@10 |
| Versus Item-CF | −0.166385 absolute / −86.90% relative NDCG@10 |
| Repeat/novel | ALS NDCG@10 0.083166 / 0.005362, below Item-CF 0.736489 / 0.006395 |
| Coverage@20 | ALS 3,442 items / 1.6243%, below Item-CF 23.6441% |
| Fallback | 100% ALS scored; no complete or partial popularity fallback at frozen `T` |
| Compute | ALS-3 fit 86.06s; scoring 3.93s; temporary serialized estimator 323.2 MiB |
| Family decision | **ITEM-CF REMAINS PREFERRED** |
| Search policy | no further family search justified before explicit review |
| Lockbox | recommendation rankings and performance remain completely untouched |
| Next question | whether a simple personalized collaborative baseline improves validation ranking and coverage |

No collaborative model is selected, and event weighting remains unresolved.

## Step 3 Item-CF experiment

| Decision/evidence | Outcome |
|---|---|
| Representation | binary visitor-item interactions; repeat events collapsed; all events equal |
| Similarity | exact sparse item cosine from training events only; self-similarity retained under seen-item policy |
| Score | sum of retained similarities across distinct visitor history items |
| Configurations | predeclared top 50/100/200 item neighbors; no grid expansion |
| Selected | 50 neighbors by macro NDCG@10 |
| Validation | NDCG@10 0.191470; HitRate@10 0.250773; HitRate@20 0.263640 |
| Popularity comparison | +0.188349 absolute / +6,034.0% relative NDCG@10 |
| Repeat/novel | NDCG@10 0.736489 / 0.006395; aggregate gain strongly repeat-driven |
| Fallback | 0% complete fallback; 14.0047% partial popularity fill |
| Coverage@20 | 50,103 items / 23.6441%, versus popularity 0.009438% |
| Conclusion | **ITEM-CF CLEARLY JUSTIFIED** on validation, not final or production-ready |
| Next step | one controlled latent-factor challenger justified, especially for novel discovery |
| Lockbox | recommendation rankings and performance remain untouched |
