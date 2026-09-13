# Product Recommendation methodology

## Problem definition

At an explicit recommendation time `T`, rank products for a known RetailRocket visitor using only events and item state available at or before `T`. The frozen target is the **item in that visitor's next recorded interaction** during the observable evaluation window. It measures next-interaction relevance, not purchase probability, causal influence, or incremental sales.

## Dataset and event semantics

The authentic files in `data/raw/retailrocket/` contain views, add-to-cart events, transactions, timestamped item properties, and a static category tree. Events are implicit feedback. Step 1 assigns no numeric weights. Later weighted candidates may preserve `transaction > addtocart > view`, but weights remain unresolved. The target treats event types equally because high-intent and transaction-only targets were too sparse for the first evaluation.

## Prediction unit and evaluation instance

The unit is one `(visitor, recommendation timestamp T)` instance. History contains interactions at or before `T`. The single relevant target is the first chronological item in `(T, window_end)`, with item ID then event name as deterministic same-millisecond tie-breakers. A visitor contributes at most one instance per validation window. The target is never history.

## Temporal evaluation

All UTC windows are half-open:

| Partition | Interval |
|---|---|
| Training history | `[2015-05-03 03:00, 2015-08-17 03:00)` |
| Development validation | `[2015-08-17 03:00, 2015-09-01 03:00)` |
| Final untouched lockbox | `[2015-09-01 03:00, 2015-09-18 03:00)` |

These align to the dataset's 03:00 UTC source-day boundary and retain 106, 15, and 17 complete days. Development uses the global validation cutoff. Rolling windows may later be used inside training only. Random splits and unconstrained per-user leave-last-out are prohibited. Lockbox feasibility counts were audited; rankings and performance remain untouched.

## Eligibility, seen items, candidates, and cold start

Evaluation requires at least two prior interactions at or before `T`; no unique-item minimum is imposed. Visitors with zero history are new-visitor cold start; one event is insufficient for personalized evaluation.

Previously seen items remain rankable, with novel-target results as a diagnostic slice. The full candidate catalog at `T` is every item observed at or before `T`. Future-only items are not retroactively rankable and remain metric misses plus a separately reported new-item rate. No sampled negatives are used in the primary evaluation. New visitors will eventually need time-safe popularity; new items require metadata/content or explicit unavailability. Neither fallback is implemented here.

## Frozen popularity baseline

Step 2's first baseline ranks by **count of all interaction events at or before `T`**, descending, with numeric item ID ascending as tie-break. It uses full history, no event weights and no tuned recency window; seen items remain eligible.

## Metric policy

Primary: macro single-target `NDCG@10`. Secondary: Recall/HitRate at 5, 10, 20; NDCG at 5 and 20; MRR at 5, 10, 20; Precision at 5, 10, 20; catalog coverage; repeat/novel slices. For one target, Recall@K and HitRate@K are equal per instance. NDCG is `1/log2(rank+1)` on hit; MRR is `1/rank`; Precision is `hit/K`. Aggregates average eligible instances, including unrankable cold-item targets as misses.

## Property-time semantics and sessions

Properties are snapshots/updates at 18 timestamps. A lookup at `T` must select the latest item-property record at or before `T` with a deterministic tie rule; final-over-all-time state is forbidden. The untimestamped category tree is static under its observed hierarchy contract.

No session ID exists. The first recommender addresses longer-term visitor preference. No arbitrary inactivity gap or session-aware target is frozen.

## Leakage protections

| Risk | Protection |
|---|---|
| Random interaction split | global chronological windows only |
| Future event/target in history | history at or before `T`; target strictly after `T` |
| Future popularity/availability | counts and candidates only through `T` |
| Future/final property state | as-of lookup at or before `T` |
| Duplicate target/history event | explicit boundary and deterministic ordering |
| Lockbox tuning | lockbox rankings/outcomes unopened for decisions |
| Per-user but global leakage | global cutoff remains mandatory |

## Open decisions

Step 2 may compare time-safe popularity and simple collaborative baselines, predeclare limited event-weight candidates, and verify full-catalog runtime. Property encoding, session extensions, metadata-based item cold start, new-visitor fallback implementation, and serving remain open.
