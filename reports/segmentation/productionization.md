# Phase 2 Customer Segmentation — Productionization

## Frozen research methodology

The production engine implements the reviewed Complete Journey grocery-household methodology without modification:

- reference snapshot: `2017-09-30 23:59:59`;
- eligibility: ≥90 observed-history days, ≥5 distinct baskets, and ≥30 active-span days;
- ordered features: recency days, basket frequency, monetary value, average basket value, unique departments, department-spend HHI, discount share of gross, coupon-basket rate, and private-label spend share;
- `log1p`: recency, frequency, monetary value, and average basket value;
- unchanged: unique departments and the four bounded ratios;
- scaler: `RobustScaler`;
- estimator: `KMeans(n_clusters=3, init="k-means++", n_init=20, max_iter=300, tol=0.0001, algorithm="lloyd", random_state=42)`.

No alternative model, tuning, future outcome, or return-risk target was introduced.

## Temporal evidence and semantic segments

The historical June–September snapshots contained 2,085, 2,172, 2,219, and 2,247 eligible households. Consecutive aligned ARIs were 0.7133, 0.7001, and 0.7175, with approximately 90–91% unchanged monthly assignments and no segment collapse. This is descriptive temporal evidence, not supervised performance.

| Raw ID in version `segmentation-kmeans3-2017-09-v1` | Segment code | Display name | Behavioral description |
|---:|---|---|---|
| 0 | `PROMOTION_BASKET_BUILDERS` | Promotion-Oriented Basket Builders | Moderate-frequency households with larger baskets and stronger observed discount/coupon use |
| 1 | `HIGH_ENGAGEMENT_BROAD` | High-Engagement Broad Shoppers | Recent, frequent, high-spend households purchasing across a broad assortment |
| 2 | `LOWER_ENGAGEMENT_FOCUSED` | Lower-Engagement Focused Shoppers | Less-recent, lower-frequency and lower-spend households with narrower assortments |

Raw IDs are version-specific implementation details. The semantic mapping is deterministically derived from reference profiles during training, validated for unique assignment, and persisted in both bundle and metadata.

## Training pipeline

Run without Jupyter:

```bash
PYTHONPATH=src python -m marketmind.segmentation.train
```

Optional `--data-dir`, `--output-dir`, and `--snapshot-date` arguments are supported; the default uses the frozen reference snapshot. The pipeline loads authentic RDS/RDA sources, validates schemas and basket relationships, constructs point-in-time eligibility/features, transforms and scales the frozen feature order, fits only frozen KMeans-3, resolves semantic identities, checks canonical invariants, and exports artifacts.

Canonical builds fail loudly unless the reference data reproduce 2,247 eligible households, cluster counts 293/1,077/877, and all three internal metrics within floating-point tolerance.

## Artifact bundle

| File | Purpose | Size |
|---|---|---:|
| `model.joblib` | Compressed scaler, KMeans, schemas, policies, semantics, profiles, and library versions | 3,492 bytes |
| `metadata.json` | Human-readable frozen configuration, evidence, policies, and limitations | 4,366 bytes |
| `reference_profiles.csv` | Three aggregated original-unit median segment profiles | 1,086 bytes |
| `monitoring_baseline.json` | Aggregated feature, segment, distance, and eligibility baselines | 4,399 bytes |
| **Total** | Complete segmentation artifact footprint | **13,343 bytes (13.0 KiB)** |

The binary remains Git-ignored; the small metadata/profile/baseline files contain no raw household transactions and are reviewable. The footprint is negligible for later local or free-tier API packaging.

## Assignment contract

Two clean entry points are available:

- household feature input: `assign_eligible_households(...)`;
- raw transactions plus products: `assign_from_transactions(...)`, which validates, constructs the snapshot, evaluates eligibility, and assigns eligible households.

Required raw transaction fields are household, store, basket, product, sales value, three discount fields, and timestamp. Required product metadata fields are product ID, department, and brand. Missing mandatory values, non-finite/negative monetary fields, duplicate basket-product rows, basket identity conflicts, duplicate product IDs, and absent columns are rejected. Authentic unmatched product IDs/missing descriptive metadata retain the previously documented `UNKNOWN` category behavior.

Output schema:

1. `household_id`
2. `snapshot_date`
3. `eligibility_status`
4. `cluster_id`
5. `segment_code`
6. `segment_name`
7. `distance_to_centroid`

Inference calls only `transform` and `predict`; neither scaler nor KMeans is refitted.

## Insufficient-history policy

Observed households failing any eligibility rule receive `eligibility_status="insufficient_history"` and null cluster ID, semantic code/name, and centroid distance. This is not a fourth segment. Reference assignment returns 199 such households among 2,446 observed by the snapshot.

## Centroid-distance semantics

`distance_to_centroid` is Euclidean distance to the assigned centroid in the frozen transformed and robust-scaled nine-feature space. It is only a geometric atypicality diagnostic. It is not probability, confidence, certainty, membership likelihood, or risk.

## Reference reproducibility and smoke test

The production CLI reproduced:

- 2,247 eligible households;
- cluster counts `{0: 293, 1: 1077, 2: 877}`;
- silhouette `0.2031284439`;
- Davies–Bouldin `1.5647334449`;
- Calinski–Harabasz `559.6854955`;
- semantic mapping 0→promotion, 1→high engagement, 2→lower engagement.

The independent smoke workflow is:

```bash
PYTHONPATH=src python -m marketmind.segmentation.smoke_test
```

It reloads `model.joblib`, reconstructs the canonical snapshot, checks all counts/codes, verifies null ineligible assignments, and validates finite nonnegative distances. The completed run passed with 2,446 output rows, 2,247 eligible, 199 insufficient-history, and median centroid distance 1.688055.

## Assignment cadence, monitoring, and refit governance

- eligibility and household assignment: monthly at calendar month-end;
- model review: quarterly;
- model refit: not automatic and not hard-coded to the review cadence.

The monitoring baseline stores original-unit Q25/median/Q75 per feature; per-segment counts, percentages, descriptions, and median profiles; overall and per-cluster centroid-distance median/Q75/Q90/Q95; and eligible/insufficient-history counts and percentages. It intentionally defines no alert thresholds.

A future refit requires review of sustained, corroborating evidence such as feature-distribution shift, segment-share movement, centroid/profile drift, semantic-ordering breakdown, growing assignment distances, or a material retailer/domain/process change. No single metric automatically forces retraining.

## Testing

The full 41-test suite passes. Production-focused coverage includes bundle round-trip/type validation, deterministic feature order and transformation persistence, exactly three persisted semantic codes, profile-derived mapping, eligibility and null ineligible assignments (including an all-new population), finite nonnegative distances, malformed-input rejection, inference object immutability, output schema, and the canonical 2,247-household invariant.

## Known limitations

- Complete Journey represents grocery-retail households, not individual e-commerce customers.
- Segments are descriptive and non-causal.
- Assignment is not a probability; distance is not confidence.
- Temporal review covers four snapshots and no second-year seasonal replication.
- Cumulative behavior features depend on observation history.
- Monitoring thresholds need operational baseline history and business review.
- The engine is not automatically valid for unrelated retailers, domains, or data-generating processes.

## FastAPI readiness

The engine is ready for later FastAPI integration: training is notebook-independent, the bundle is self-contained, inference has explicit validation/output contracts, and artifacts are compact. No API or application infrastructure was created in this step.
