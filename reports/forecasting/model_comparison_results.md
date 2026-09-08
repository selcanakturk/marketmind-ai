# Limited Tuning and Model-Family Comparison

> **NO LOCKBOX RESULTS:** This experiment uses sales targets only through `d_1913`. The `d_1914`–`d_1941` lockbox remains completely unevaluated.

## Objective

Use a deliberately small, predeclared comparison to select a deployable forecasting candidate without broad tuning. All candidates retain the selected Full feature scope, 70 department-store series, six frozen folds, 28-day horizon, raw targets, fold-local preprocessing, and fold-specific RMSSE scaling. No price features or new feature families were added.

## Predeclared candidate set

Six HGBR configurations were evaluated with both horizon-conditioned Direct and one-step Recursive strategies. One ExtraTrees Direct challenger used a pre-run resource-bounded configuration. Because ExtraTrees Direct fell within 3% of the best HGBR, Recursive ExtraTrees was triggered and evaluated as required. A single matched-weekly-origin Recursive HGBR-1 sensitivity check tested the known strategy-sampling difference.

## HGBR limited tuning

Common parameters: squared-error loss, `max_depth=None`, `early_stopping=False`, and `random_state=42`.

| Config | Learning rate | Iterations | Leaves | Min leaf | L2 |
|---|---:|---:|---:|---:|---:|
| HGBR-1 | 0.05 | 120 | 31 | 100 | 1.0 |
| HGBR-2 | 0.05 | 180 | 31 | 100 | 1.0 |
| HGBR-3 | 0.03 | 200 | 31 | 100 | 1.0 |
| HGBR-4 | 0.05 | 160 | 63 | 100 | 1.0 |
| HGBR-5 | 0.05 | 160 | 31 | 50 | 1.0 |
| HGBR-6 | 0.05 | 160 | 31 | 100 | 5.0 |

Results:

| Configuration | Direct RMSSE | Recursive RMSSE | Direct WAPE | Recursive WAPE | Direct bias | Recursive bias |
|---|---:|---:|---:|---:|---:|---:|
| HGBR-1 | 0.77916 | 0.76957 | 10.62% | 10.38% | -1.12% | -0.48% |
| HGBR-2 | 0.77232 | 0.81747 | 10.42% | 11.08% | -0.25% | +1.58% |
| HGBR-3 | 0.77661 | **0.76875** | 10.57% | 10.35% | -1.15% | -0.38% |
| **HGBR-4** | **0.74604** | 0.81405 | **10.29%** | 11.15% | -0.37% | +2.09% |
| HGBR-5 | 0.77207 | 0.79228 | 10.41% | 10.85% | -0.45% | +0.74% |
| HGBR-6 | 0.76605 | 0.78969 | 10.32% | 10.77% | **-0.32%** | +0.49% |

HGBR-4 Direct is the best HGBR candidate. It improves RMSSE by 0.03312, or 4.25%, over HGBR-1 Direct. Higher-capacity Recursive configurations are less stable, especially in Fold 6; limited tuning therefore changes the HGBR strategy ranking from Recursive to Direct.

## ExtraTrees challenger

The predeclared resource-bounded configuration was:

```text
ExtraTreesRegressor(
    n_estimators=200,
    max_depth=20,
    min_samples_leaf=5,
    max_features=0.8,
    n_jobs=-1,
    random_state=42,
)
```

The tree count and depth cap were fixed before results to constrain local memory and artifact size. ExtraTrees Direct achieved RMSSE **0.73317**, better than HGBR-4 Direct by 0.01286, or 1.72% relative to HGBR-4. It also achieved MAE 56.90, WAPE 10.21%, and bias -1.04%.

The 3% gate fired because 0.73317 was within 3% of—and better than—the best HGBR. Recursive ExtraTrees was therefore evaluated. It achieved RMSSE 0.74749, MAE 57.89, WAPE 10.38%, and bias -0.70%. Direct ExtraTrees is better overall by 0.01432 (1.92%) and wins four of their six head-to-head folds.

## Sampling sensitivity

Reference Recursive HGBR-1 trained on daily origins achieved 0.76957 RMSSE. When trained only on the exact weekly origin dates used by Direct, it fell to **1.32646**, a degradation of 0.55689 or 72.36%, with WAPE 19.31% and bias -11.76%.

This shows that dense one-step sampling is essential to Recursive performance and that Step 4's small recursive advantage cannot be attributed purely to multi-step strategy. The weekly sensitivity also has only 15,960 mean rows versus 113,330 for daily Recursive. It does not prove Direct is intrinsically superior, but it explains why strategy and sampling density cannot be fully separated. Direct training already obtains 28 horizon labels per weekly origin.

## Core metrics

Selection-leading candidates:

| Candidate | RMSSE | MAE | WAPE | Bias |
|---|---:|---:|---:|---:|
| ExtraTrees Direct | **0.73317** | **56.90** | **10.21%** | -1.04% |
| HGBR-4 Direct | 0.74604 | 57.35 | 10.29% | **-0.37%** |
| ExtraTrees Recursive | 0.74749 | 57.89 | 10.38% | -0.70% |
| HGBR-3 Recursive | 0.76875 | 57.69 | 10.35% | -0.38% |
| HGBR-1 Recursive | 0.76957 | 57.88 | 10.38% | -0.48% |
| HGBR-1 Direct reference | 0.77916 | 59.19 | 10.62% | -1.12% |

## Fold stability

| Fold | ExtraTrees Direct | HGBR-4 Direct | ExtraTrees Recursive | HGBR-1 Direct |
|---:|---:|---:|---:|---:|
| 1 | 0.84270 | **0.80432** | 0.82491 | 0.86596 |
| 2 | 0.67138 | **0.66425** | 0.68968 | 0.68110 |
| 3 | 0.64352 | 0.65096 | **0.63222** | 0.67079 |
| 4 | **0.82511** | 0.87316 | 0.84641 | 0.89968 |
| 5 | **0.74150** | 0.77976 | 0.77608 | 0.81940 |
| 6 | **0.67484** | 0.70378 | 0.71567 | 0.73803 |

Across all selection-eligible candidates, ExtraTrees Direct wins three folds, HGBR-4 Direct two, and ExtraTrees Recursive one. Fold RMSSE standard deviations are 0.08459, 0.08742, and 0.08275, respectively. ExtraTrees therefore has a small stability advantage, but no candidate dominates every period.

## Series-level comparison

Against the current HGBR-1 Full Direct reference:

| Candidate | Improved series | Regressed | Median RMSSE delta | Largest gain | Largest regression |
|---|---:|---:|---:|---:|---:|
| HGBR-4 Direct | 55 | 15 | -0.02358 | -0.27906 | +0.04348 |
| HGBR-1 Recursive | 44 | 26 | -0.01343 | -0.20767 | +0.13322 |
| ExtraTrees Direct | 54 | 16 | -0.03062 | -0.49222 | +0.08833 |

HGBR-4's largest gains occur for `CA_2/FOODS_2` (-0.2791), `CA_4/HOBBIES_2` (-0.2561), and `WI_2/HOUSEHOLD_1` (-0.1333). Its largest regression is only +0.0435 for `WI_3/HOBBIES_2`.

ExtraTrees Direct's largest gains include `CA_4/HOBBIES_2` (-0.4922), `WI_2/HOBBIES_2` (-0.2818), and `TX_1/HOBBIES_2` (-0.1921). Its largest regressions are `CA_3/HOUSEHOLD_1` (+0.0883), `WI_1/FOODS_2` (+0.0733), and `CA_2/FOODS_3` (+0.0560).

Previously difficult series:

| Series | HGBR-1 Direct | HGBR-4 Direct | ExtraTrees Direct |
|---|---:|---:|---:|
| `CA_4/HOBBIES_2` | 1.6238 | 1.3677 | **1.1316** |
| `CA_2/FOODS_2` | 1.4878 | **1.2087** | 1.3280 |
| `TX_1/HOBBIES_2` | 1.3803 | 1.3861 | **1.1882** |

No difficult series was removed or specifically optimized.

## Horizon behavior

| Horizons | HGBR-4 Direct MAE | HGBR-4 bias | ExtraTrees Direct MAE | ExtraTrees bias | HGBR-1 Recursive MAE | Recursive bias |
|---|---:|---:|---:|---:|---:|---:|
| 1–7 | 53.66 | -0.93% | **53.22** | -1.55% | 53.68 | -1.12% |
| 8–14 | **56.81** | -1.47% | 58.51 | -1.88% | 58.05 | -1.25% |
| 15–21 | 57.26 | +0.35% | **56.90** | -0.81% | 59.11 | -0.68% |
| 22–28 | 61.66 | +0.62% | **58.99** | +0.12% | 60.70 | +1.19% |

All candidates are modestly harder at later horizons. ExtraTrees Direct has the best final-block MAE. HGBR-4 Direct has no recursive error accumulation because it predicts horizons directly; its final-block degradation remains a general horizon difficulty. HGBR-1 Recursive does not show operationally severe accumulation, but later bias becomes more positive.

## Computational cost

Fold means include the analytical table and target array before encoded-matrix allocation.

| Candidate | Rows | Memory | Build | Fit | 28-day generation | Serialized model |
|---|---:|---:|---:|---:|---:|---:|
| HGBR-1 Direct | 446,880 | 138.8 MB | 2.75 s | 2.72 s | 0.0067 s | 0.50 MB |
| **HGBR-4 Direct** | 446,880 | 138.8 MB | 2.75 s | 4.93 s | **0.0086 s** | **1.28 MB** |
| HGBR-1 Recursive | 113,330 | 35.1 MB | 1.43 s | 1.25 s | 0.212 s | 0.48 MB |
| ExtraTrees Direct | 446,880 | 138.8 MB | 2.78 s | 28.18 s | 0.042 s | **1,050.44 MB** |
| ExtraTrees Recursive | 113,330 | 35.1 MB | 1.42 s | 5.04 s | 0.481 s | 373.83 MB |

ExtraTrees Direct's model is approximately 819 times larger than HGBR-4 Direct, fits about 5.7 times slower, and predicts about 4.9 times slower. Its absolute prediction time remains small locally, but a roughly 1 GB artifact conflicts with MarketMind's lightweight/free-deployment constraint. HGBR-4 provides a compact single artifact with batch 28-horizon generation.

## Operational tradeoffs and selection decision

The predeclared primary criterion gives ExtraTrees Direct the best raw RMSSE. Its 1.72% advantage over HGBR-4 exceeds the automatic “within 1%, prefer simpler” band, so the difference is reported as real rather than declared equivalent. However, selection also requires operational complexity, bias, folds, series regressions, and cost:

- ExtraTrees leads RMSSE by 0.01286 and wins four of six head-to-head folds.
- HGBR-4 has materially smaller bias magnitude, improves 55 series versus the original reference, and has tightly bounded regressions.
- ExtraTrees costs roughly 1.05 GB per fold artifact versus 1.28 MB for HGBR-4, a deployment-critical difference rather than a marginal optimization.
- HGBR-4 retains a 30.08% RMSSE improvement over the historical-mean baseline and 30.26% over seasonal naïve.
- Direct strategy is favored within both families: tuned HGBR Direct leads tuned HGBR Recursive, and ExtraTrees Direct leads ExtraTrees Recursive.
- The sampling sensitivity demonstrates that Recursive performance depends strongly on daily one-step training density.

Therefore the selected operational candidate is:

## CURRENT FORECASTING MODEL CANDIDATE — FROZEN BEFORE LOCKBOX

- **Family:** `HistGradientBoostingRegressor`
- **Strategy:** horizon-conditioned Full Direct global model
- **Feature scope:** Full selected feature set, with no prices
- **Parameters:** HGBR-4 exactly as declared above
- **Post-processing:** clip predictions to zero if negative
- **Training sampling:** frozen weekly origins aligned backward from `training_end − 28`, minimum origin 56

The choice deliberately accepts a measured 1.72% development RMSSE cost versus ExtraTrees Direct to reduce serialized size by roughly three orders of magnitude and preserve lightweight deployment. This is a model-selection decision, not a claim that ExtraTrees lacks predictive value.

## Remaining risks

- ExtraTrees Direct's better development RMSSE may represent genuine generalization that the operational selection gives up.
- Only six folds and a small HGBR grid were used.
- Direct/recursive training examples have structurally different weighting.
- Ordinal categorical encoding and raw sales targets remain design compromises.
- The frozen candidate has not been evaluated on the lockbox; its generalization is unknown.
- Publication/deployment must package preprocessing categories and feature definitions exactly with the model.
- Uncertainty, anomaly detection, inventory logic, and price scenarios remain outside this step.
