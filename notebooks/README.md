# Research notebook workflow

Status: **completed research and historical evaluation evidence**.

The notebooks document MarketMind's dataset audits and controlled experiments. Reusable methodology and production inference live in `src/marketmind/`; the finished application loads frozen artifacts from `models/` and does not execute notebooks at runtime.

## Organization

| Range | Purpose |
|---|---|
| `00_*` | Olist, M5, RetailRocket, and Complete Journey dataset feasibility audits |
| `01_*`–`05_*` | Forecast baselines, learned models, controlled comparison, and final lockbox evaluation |
| `06_*`–`08_*` | Segmentation features, clustering, temporal stability, and semantic naming |
| `09_*`–`13_*` | Re-engagement target design, model selection, calibration policy, and final lockbox evaluation |
| `14_*`–`17_*` | Popularity, Item-CF, ALS comparison, and final recommendation lockbox evaluation |
| `18_*`–`20_*` | Robust residual anomalies, Isolation Forest diagnostic, and final lockbox evaluation |
| `21_*` | Inventory safety-stock assessment and decision-policy evidence |

Each experiment is paired with reviewable results or decision records under `reports/`. Production contracts, artifacts, and limitations are documented under `docs/`, `models/`, and the module-specific production reports.

## Reproduction boundary

Running the production/demo application does **not** require raw datasets. Re-running these notebooks does: datasets must be acquired separately from the sources documented in [`docs/dataset_requirements.md`](../docs/dataset_requirements.md), stored in ignored local data directories, and used according to their source terms.

Final evaluation intervals marked **consumed** are immutable historical evidence. Re-execution may confirm recorded results, but those targets must never be treated as fresh validation data or used to change features, models, hyperparameters, thresholds, ranking policies, or business semantics.

For current project navigation, see the root [`README.md`](../README.md) and [`docs/README.md`](../docs/README.md).
