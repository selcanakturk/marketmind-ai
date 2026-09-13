# Recommendation production engine

## Purpose

This module packages the frozen RetailRocket Item-CF research winner as a deterministic, notebook-independent engine suitable for later API integration. This is production retraining, not a new experiment, and it calculates no outcome-based quality metrics.

## Frozen research specification

The engine uses binary visitor-item interactions, collapses repeated pairs, treats views, carts, and transactions equally, builds exact sparse cosine similarity, and retains the best 50 neighbors per item. It sums similarities across distinct history items. Self-similarity is retained, previously seen items are allowed, and ranking uses score descending then numeric item ID ascending. There is no event or recency weighting, metadata, category, session, latent-factor, hybrid, novelty, or reranking component.

## Production retraining policy

After selection and the one-time lockbox evaluation were complete, the unchanged specification was fitted once to every historical event in `events.csv`, including the former development and lockbox periods. No setting was changed from post-lockbox information. `python -m marketmind.recommendations.train` regenerates the bundle from local data.

## Input contract

Training and scoring require `timestamp`, `visitorid`, `itemid`, and `event`; `transactionid` is optional and unused. Timestamp is nonnegative integer Unix milliseconds. Visitor and item IDs are nonnegative integers. Event must be `view`, `addtocart`, or `transaction`. Input is sorted canonically. CF collapses visitor-item duplicates, while popularity counts every chronological event.

## Artifact structure

`models/recommendations/model.joblib` contains an ascending item-ID array, CSR-style row pointers, 32-bit neighbor indices, 32-bit cosine weights, full-history item popularity/counts, item first-seen milliseconds, cutoff/configuration metadata, and provenance. It contains neither the visitor-item training matrix nor a dense item-item matrix. The large binary is ignored; its metadata and training summary are reviewable.

## Scoring logic

`recommend_visitor(events, visitorid, snapshot_timestamp, bundle, k=20)` uses only rows at or before explicit `T`. It takes distinct visitor history, ignores unknown history items, sums the stored neighbors of known items, orders candidates deterministically, and fills unoccupied positions with current-snapshot popularity. Results are unique. `k` is caller-selectable from 1 through 1,000; this is an operational request size, not a retuned model parameter.

Because this bundle learned its graph from all available history, it rejects snapshots before its training cutoff. That prevents the graph itself from leaking future relationships. Rows later than a valid snapshot are ignored. A future rolling/retraining system would need a bundle whose training cutoff is no later than its serving timestamp.

Historical research evaluation computed popularity independently at every past `T`. Current production scoring instead computes popularity from the supplied event table restricted through the current `T`. Both rules exclude future events.

## Seen-item and self-similarity policy

Seen items are deliberately not filtered. Self-similarity is deliberately retained, matching research and supporting repeat-interaction behavior. Regression tests protect both choices.

## Popularity fallback and cold start

Visitors with no history return deterministic popularity recommendations with `fallback_reason=no_history`. Visitors whose history contains no graph-known item receive `no_collaborative_history`. Partially known histories use known items and ignore unknown ones. Popularity fills remaining slots without duplicates.

A new item receives no fabricated similarity. Once observed at or before `T`, it becomes a legitimate current candidate and can enter through popularity. Future-only items cannot appear.

## Output contract

Each row has `visitorid`, UTC `snapshot_timestamp`, contiguous one-based `rank`, `itemid`, `recommendation_score`, `score_source`, and `was_previously_seen`. Diagnostic columns report collaborative candidate count, whether popularity fill was used, known history count, and fallback reason. Collaborative scores are summed cosine values; popularity-fill scores are current event counts and must not be compared across source types as a common calibrated scale.

## Determinism and serialization

Collaborative ties and popularity ties use numeric item ID ascending. Distinct-history aggregation, stable sorting, validation, and unique-item enforcement make identical logical input order-invariant. Training saves and reloads a validated bundle; tests compare pre/post-serialization output.

## Operational limits

The graph is exact and sparse but batch training still temporarily builds a sparse visitor-item matrix and sparse co-occurrence matrix. Inference needs the supplied event snapshot to reconstruct history and current popularity. The current Python API is ready to sit behind a later service, but no FastAPI endpoint exists. Production monitoring, incremental graph updates, and a persistent event/catalog store are future integration work.

## Known model limitations

- The objective is next interaction and is dominated by views.
- Strong research performance is heavily driven by repeat targets; novel-item discovery remains weak.
- The model has no metadata/content understanding, and cold items lack collaborative representation.
- It does not differentiate event value.
- RetailRocket visitor history is sparse.
- There is no session modeling.

## Lockbox status

The final recommendation lockbox is permanently **consumed**. Existing values in artifact metadata are historical references copied from prior reports only. They were not recalculated and cannot be treated as fresh validation, tuning, calibration, selection, or policy evidence.

## Future API integration

The stable Python input/output contract and loadable bundle are FastAPI-ready later. HTTP endpoints, authentication, storage, monitoring, and deployment are explicitly outside this step.
