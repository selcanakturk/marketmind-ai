# Controlled Feature Ablation and Strategy Results

> **NO LOCKBOX RESULTS:** Sales targets are read only from `sales_train_validation.csv` through `d_1913`. No `d_1914`–`d_1941` target was accessed or evaluated.

## Experiment questions

1. Are rolling summaries associated with incremental accuracy beyond lags?
2. Are known-in-advance calendar fields associated with incremental accuracy?
3. How much performance remains in a minimal global feature set?
4. Does a one-step recursive global strategy outperform the horizon-conditioned direct strategy, or does error propagate?
5. Is the evidence stable enough to justify a later limited tuning/model-family comparison?

## Frozen experimental design

All five variants use the same 70 department-store series, six development folds, 28-day validation horizons, fold-specific RMSSE scales, raw targets, fold-local ordinal encoding, and the exact Step 3 HGBR parameters. No series was removed and no configuration was tuned per variant.

Direct training uses the Step 3 weekly origins, aligned backward from `training_end − 28`. Recursive training uses every daily one-step origin from day 56 through `training_end − 1`; this deterministic rule was declared before results. Both keep every training label inside the fold training period.

## Reference model and feature ablations

- **Full Direct:** lags 1/7/14/28/56; rolling mean/std 7/28/56; horizon; store/department/state; target-date weekday/day/month/year/day index, primary event name/type, and applicable SNAP.
- **Lags Only Direct:** Full Direct without rolling means and standard deviations.
- **No-Calendar Direct:** lags, rolling summaries, horizon, store/department/state, and sequential day index; removes weekday, day of month, month, year, events, and SNAP.
- **Minimal Direct:** lags 1/7/28, horizon, store, and department only.

These are controlled feature-group comparisons, not causal feature-importance estimates.

## Recursive challenger

The global one-step model uses the Full model's lags, rolling summaries, identity, and target-date calendar/context for `t+1`, without forecast horizon. At issuance it predicts `T+1`, appends that prediction to a copy of observed history, recomputes features, and continues through `T+28`. Assertions verify history width at every step. Actual validation values are never appended.

## Fixed model configuration

Every fit uses:

```text
HistGradientBoostingRegressor(
    loss="squared_error",
    learning_rate=0.05,
    max_iter=120,
    max_leaf_nodes=31,
    max_depth=None,
    min_samples_leaf=100,
    l2_regularization=1.0,
    early_stopping=False,
    random_state=42,
)
```

Prices are excluded. No new model family or hyperparameter search was introduced.

## Core results

Difference versus Full Direct is challenger minus Full, so positive values are worse.

| Variant | Macro RMSSE | Macro MAE | Pooled WAPE | Pooled bias | RMSSE Δ vs Full | Relative Δ vs Full | Improvement vs historical mean |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Recursive Global** | **0.76957** | **57.88** | **10.38%** | **-0.48%** | **-0.00959** | **-1.23%** | 0.29733 |
| Full Direct | 0.77916 | 59.19 | 10.62% | -1.12% | — | — | 0.28774 |
| Lags Only Direct | 0.83636 | 63.37 | 11.37% | -2.71% | +0.05720 | +7.34% | 0.23055 |
| No-Calendar Direct | 0.88300 | 72.90 | 13.08% | -1.21% | +0.10384 | +13.33% | 0.18391 |
| Minimal Direct | 0.97578 | 80.23 | 14.39% | -4.67% | +0.19662 | +25.23% | 0.09113 |

All learned variants remain below the historical-mean RMSSE of 1.06690. Full Direct retains a material advantage over every simpler direct variant. Recursive is modestly better than Full Direct on every overall metric, but its 0.00959 RMSSE advantage is only 1.23%.

## Fold stability

| Fold | Full Direct | Lags Only | No Calendar | Minimal | Recursive |
|---:|---:|---:|---:|---:|---:|
| 1 | **0.86596** | 0.98857 | 0.96474 | 1.13484 | 0.86777 |
| 2 | **0.68110** | 0.74451 | 0.78706 | 0.84758 | 0.69476 |
| 3 | 0.67079 | 0.70280 | 0.77467 | 0.82047 | **0.64719** |
| 4 | 0.89968 | 0.94788 | 0.97614 | 1.07650 | **0.86424** |
| 5 | 0.81940 | 0.84431 | 0.95441 | 0.99118 | **0.81164** |
| 6 | 0.73803 | 0.79007 | 0.84095 | 0.98408 | **0.73181** |

- Full Direct beats every direct ablation in 6 of 6 folds.
- Against Recursive, Full wins Folds 1–2 and Recursive wins Folds 3–6.
- No fold shows substantial recursive degradation; its largest loss is 0.01367 in Fold 2 and largest gain 0.03544 in Fold 4.
- Fold RMSSE standard deviations: Recursive 0.09206, No Calendar 0.09291, Full 0.09668, Lags Only 0.11322, Minimal 0.12354.

Recursive has slightly better measured fold dispersion, but the advantage over Full is small relative to their common gains over the baselines.

## Series-level comparison

Counts compare six-fold mean RMSSE with Full Direct. “Improved” means the challenger is lower.

| Challenger | Improved | Regressed | Median RMSSE Δ | Largest improvement | Largest regression |
|---|---:|---:|---:|---:|---:|
| Lags Only | 16 | 54 | +0.04149 | -0.12255 | +0.26398 |
| No Calendar | 10 | 60 | +0.08832 | -0.08357 | +0.61342 |
| Minimal | 9 | 61 | +0.14102 | -0.20616 | +1.23001 |
| Recursive | 44 | 26 | **-0.01343** | -0.20767 | +0.13322 |

Notable ablation regressions include:

- Lags Only: `CA_4/HOUSEHOLD_1` +0.2640 and `CA_3/HOBBIES_2` +0.2629.
- No Calendar: `WI_2/FOODS_2` +0.6134 and `WI_3/FOODS_2` +0.3967.
- Minimal: `WI_2/FOODS_2` +1.2300 and `WI_3/FOODS_2` +0.5964.

Recursive's largest improvements are `WI_2/FOODS_2` (-0.2077), `CA_2/FOODS_2` (-0.1293), and `TX_2/HOBBIES_2` (-0.1222). Its largest regressions are `WI_1/HOUSEHOLD_2` (+0.1332), `CA_4/HOBBIES_2` (+0.1132), and `CA_3/FOODS_1` (+0.1119).

Previously difficult series:

| Series | Full | Lags Only | No Calendar | Minimal | Recursive |
|---|---:|---:|---:|---:|---:|
| `CA_4/HOBBIES_2` | 1.6238 | 1.6752 | 1.6334 | **1.4177** | 1.7370 |
| `CA_2/FOODS_2` | 1.4878 | 1.4531 | 1.7037 | 1.8204 | **1.3585** |
| `TX_1/HOBBIES_2` | **1.3803** | 1.4256 | 1.3732 | 1.4603 | 1.4524 |

No variant is uniformly best for difficult series, and none was tuned specifically for them.

## Feature-group interpretation

- Removing rolling means/std while retaining lags and context was associated with a **0.05720 / 7.34% RMSSE degradation**, regressions in 54 of 70 series, and worse performance in every fold. Rolling summaries provide meaningful incremental evidence under this design.
- Removing rich target-date calendar fields while retaining history, identities, horizon, and trend was associated with a **0.10384 / 13.33% degradation**, regressions in 60 series, and worse performance in every fold. Known calendar structure appears useful in this backtest.
- Minimal Direct preserves substantial learned-model value: RMSSE 0.97578 still improves on historical mean by 0.09113 (8.54%). However, its 25.23% degradation versus Full, worse result in all folds, regressions in 61 series, and only about 77.7 MB mean memory savings do not support treating it as effectively comparable.

These are associations under controlled removal, not evidence that any feature group causes sales changes.

## Horizon analysis

| Horizons | Full MAE | Full bias | Recursive MAE | Recursive bias |
|---|---:|---:|---:|---:|
| 1–7 | 55.91 | -1.52% | **53.68** | -1.12% |
| 8–14 | 60.19 | -2.29% | **58.05** | -1.25% |
| 15–21 | 59.52 | -0.63% | **59.11** | -0.68% |
| 22–28 | 61.15 | +0.03% | **60.70** | +1.19% |

Both strategies become modestly harder at later horizons, but neither curve rises monotonically. Recursive remains slightly better in every block; there is no observed accumulation that makes its late-horizon MAE worse than Full Direct. Its advantage narrows from 2.23 MAE units in horizons 1–7 to 0.45 in horizons 22–28, while late-horizon positive bias is larger. This does not support an error-propagation rejection of recursion on the current folds.

## Computational cost

Values are fold means. Direct build time is for one shared Full table reused by all direct variants and should not be summed four times.

| Variant | Mean training rows | Mean memory | Build | Fit | 28-day generation | Negative predictions |
|---|---:|---:|---:|---:|---:|---:|
| Full Direct | 446,880 | 138.8 MB | 2.470 s | 2.313 s | **0.006 s** | 0 |
| Lags Only Direct | 446,880 | 128.6 MB | shared | 1.843 s | 0.006 s | 0 |
| No Calendar Direct | 446,880 | 90.7 MB | shared | 1.657 s | **0.005 s** | 0 |
| Minimal Direct | 446,880 | 54.4 MB | shared | 1.173 s | 0.006 s | 0 |
| Recursive | 113,330 | 35.1 MB | **1.343 s** | **0.866 s** | 0.137 s | 0 |

Recursive training is smaller and faster under its one-step formulation, but 28-step generation is sequential and approximately 22 times slower than Full Direct in this local experiment. Both are operationally lightweight at 70 series, so accuracy/stability—not raw runtime alone—should decide the strategy.

## Methodological limitations

- Direct and recursive targets require structurally different training tables: weekly 28-horizon rows versus daily one-step rows. This is a predeclared fair-density comparison, but sampling/weighting and strategy cannot be completely separated.
- Only one fixed HGBR configuration is tested; parameters may favor neither strategy equally.
- Ordinal categorical encoding remains a lightweight compromise.
- Calendar ablation removes a group of fields and cannot isolate individual calendar variables.
- Feature ablation associations are not causal importance.
- Development results do not establish lockbox or deployment performance.
- No price, inventory, uncertainty, anomaly, or item-level learned modeling is included.

## Decision

**Feature scope:** Proceed with the **Full feature set**. Each simpler direct variant has a quantified, nontrivial overall loss, loses all six folds, and regresses most series. None meets an evidence-based “effectively comparable” standard. The minimal model remains a useful lower-complexity reference, not the lead candidate.

**Multi-step strategy:** Do **not select Full Direct as superior**. Recursive is the current numerical leader: 1.23% lower RMSSE, better secondary metrics, four fold wins, and 44 series wins. However, the advantage is modest, 26 series regress, inference is sequential, and training-table construction differs structurally. This is not strong enough to freeze Recursive either. Carry Full Direct and Recursive forward as the two strategy finalists; resolve sampling sensitivity and operational tradeoffs in a predeclared limited comparison before any final strategy freeze.

The architecture is stable enough to justify a later limited tuning/model-family comparison, but HGBR parameters and the final model family remain unfrozen. The lockbox remains untouched.
