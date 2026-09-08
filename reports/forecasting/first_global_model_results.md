# First Global Forecasting Model Results

> **NO LOCKBOX RESULTS:** This experiment reads sales targets only from `sales_train_validation.csv` (`d_1`–`d_1913`). It neither reads nor evaluates `d_1914`–`d_1941` targets.

## Experiment objective

Determine whether one lightweight learned global model adds predictive value beyond the frozen simple baselines for all 70 department-store daily sales series. The predeclared promising criterion is overall macro RMSSE below the official historical-mean benchmark of 1.06690, accompanied by fold, seasonal-baseline, WAPE, bias, horizon, and series-regression analysis.

## Frozen methodology

- Grain: department × store × day, all 70 series.
- Horizon: 28 daily steps.
- Development: `d_1`–`d_1913`.
- Six unchanged expanding-window folds.
- Primary metric: macro per-series RMSSE with fold-training-only scales.
- Baseline benchmark: 28-day historical mean; seasonal naïve retained as co-reference.
- No series exclusion, lockbox evaluation, price feature, broad tuning, anomaly work, or inventory logic.

## Modeling strategy

One `sklearn.ensemble.HistGradientBoostingRegressor` is fitted per fold across all series. Training rows follow a horizon-conditioned direct formulation:

`series identity + origin-known history + target-date calendar + horizon → y(T+h)`

The model emits all 28 horizons from information available at origin `T`. It is not recursive and never consumes actual values from inside the forecast horizon.

Training origins are deterministically sampled every seven days, aligned backward from `training_end − 28`, with minimum origin 56. This sampling rule was declared before results were inspected. Every training label therefore ends by the fold training cutoff.

## Feature set

Historical features, anchored at and ending on origin `T`:

- `lag_1`, `lag_7`, `lag_14`, `lag_28`, `lag_56`, where `lag_1 = y_T`;
- rolling mean and population standard deviation over 7, 28, and 56 days.

Known target-date/horizon features:

- `forecast_horizon` 1–28;
- target day of week, day of month, month, year, and sequential day index;
- primary calendar event name and event type;
- the target day's SNAP indicator applicable to the series state.

Identity features:

- store, department, and state.

Store, department, state, event name, and event type use a fold-locally fitted `OrdinalEncoder` with unknown categories encoded as `-1`; no target encoding is used. Historical and realized future prices are entirely excluded.

## Leakage controls

- The notebook loads only `sales_train_validation.csv` target values.
- Supervised origins satisfy `origin + 28 ≤ training_end`.
- Validation features receive sales truncated exactly at `training_end`.
- Lag and rolling code is independently tested against future-value mutation.
- Rolling windows include at most `T`; none is centered.
- Calendar rows correspond to `T+h`, and only scheduled fields are used.
- Preprocessing is newly fitted on each fold's training rows.
- Validation targets are kept separate from feature construction.
- RMSSE denominators use only the current fold's training sales history.
- Seasonal baseline repeats the final training-week template.
- No performance-based series exclusion occurs.

## Model configuration

One fixed, untuned configuration was used:

```text
loss="squared_error"
learning_rate=0.05
max_iter=120
max_leaf_nodes=31
max_depth=None
min_samples_leaf=100
l2_regularization=1.0
early_stopping=False
random_state=42
```

Categorical columns are explicitly identified to the estimator. Raw nonnegative unit sales are the target. Predictions would be clipped at zero, but clipping was not activated for any prediction.

## Training dataset size

Memory below includes the pandas feature table and target array before encoded-matrix allocation. Timings are local measurements and not portable benchmarks.

| Fold | Weekly origins | Training rows | Approx. memory | Build time | Fit time |
|---:|---:|---:|---:|---:|---:|
| 1 | 198 | 388,080 | 120.5 MB | 3.45 s | 3.27 s |
| 2 | 210 | 411,600 | 127.8 MB | 3.65 s | 3.17 s |
| 3 | 222 | 435,120 | 135.1 MB | 3.83 s | 3.34 s |
| 4 | 234 | 458,640 | 142.4 MB | 4.18 s | 3.51 s |
| 5 | 246 | 482,160 | 149.7 MB | 4.32 s | 3.58 s |
| 6 | 258 | 505,680 | 157.1 MB | 4.41 s | 3.77 s |

Average table footprint was 138.8 MB. Total measured table-build and fit time across folds was approximately 23.86 and 20.64 seconds, respectively.

## Core results and baseline comparison

| Model | Macro RMSSE | Macro MAE | Pooled WAPE | Pooled bias |
|---|---:|---:|---:|---:|
| **Global HGBR** | **0.77916** | **59.19** | **10.62%** | -1.12% |
| Historical mean (28) | 1.06690 | 99.42 | 17.83% | -1.81% |
| Seasonal naïve (7) | 1.06967 | 91.48 | 16.41% | **-1.09%** |
| Last value | 1.53223 | 162.15 | 29.09% | +16.15% |

Against the official historical-mean benchmark, the learned model improves macro RMSSE by **0.28774 absolute** and **26.97% relative**. Against seasonal naïve it improves by 0.29051, or 27.16% relative. It also materially improves MAE and pooled WAPE. Its pooled bias is small and similar in magnitude to seasonal naïve.

The predeclared promising criterion is met. This is evidence for further controlled experimentation, not proof that this algorithm is final or that lockbox performance will match development results.

## Fold stability

| Fold | Global HGBR RMSSE | Historical mean | Seasonal naïve | HGBR WAPE | HGBR bias |
|---:|---:|---:|---:|---:|---:|
| 1 | 0.86596 | 1.13487 | 1.21504 | 12.10% | -2.87% |
| 2 | **0.68110** | 0.91486 | 0.92854 | 9.49% | -0.97% |
| 3 | 0.67079 | 0.94506 | 0.86270 | **8.96%** | +0.01% |
| 4 | **0.89968** | 1.17895 | 1.12144 | 10.87% | +2.25% |
| 5 | 0.81940 | 1.16838 | 1.16165 | 12.72% | -6.50% |
| 6 | 0.73803 | 1.05930 | 1.12866 | 9.71% | +1.09% |

The learned model beats historical mean in **6 of 6 folds** and seasonal naïve in **6 of 6 folds**. By RMSSE, Fold 3 is easiest (0.67079) and Fold 4 hardest (0.89968); the fold RMSSE standard deviation is 0.09668. Fold 5 has the worst pooled WAPE and the largest bias magnitude, so the aggregate win does not eliminate temporal variation.

## Series-level analysis

Best six-fold learned-model RMSSE:

- `TX_2/FOODS_3`: 0.3718
- `WI_3/FOODS_3`: 0.4138
- `TX_1/FOODS_3`: 0.4310
- `CA_1/FOODS_3`: 0.4352
- `TX_3/FOODS_3`: 0.4774

Hardest series:

- `CA_4/HOBBIES_2`: 1.6238
- `CA_2/FOODS_2`: 1.4878
- `TX_1/HOBBIES_2`: 1.3803
- `WI_2/HOBBIES_2`: 1.2333
- `TX_3/HOBBIES_2`: 1.2196

Largest improvements over historical mean include `CA_2/FOODS_2` (+0.7212 RMSSE), `CA_3/HOUSEHOLD_1` (+0.6926), `CA_1/HOUSEHOLD_1` (+0.6707), and `CA_2/FOODS_3` (+0.6652).

The largest regressions are `CA_4/HOBBIES_2` (-0.5370), `WI_2/HOBBIES_2` (-0.0835), `CA_3/HOBBIES_2` (-0.0717), `TX_3/FOODS_1` (-0.0543), `CA_4/HOBBIES_1` (-0.0213), and `TX_1/HOBBIES_2` (-0.0044). Thus 64 of 70 series improve and six regress; difficult series remain visible and included.

Department macro RMSSE ranges from `FOODS_3` at 0.5173 to `HOBBIES_2` at 1.1703. Store averages range from `TX_2` at 0.6473 to `WI_2` at 0.9405. State averages are TX 0.7408, CA 0.7943, and WI 0.7973. These are descriptive patterns only.

## Horizon analysis

Average MAE by horizon block:

| Horizons | Mean daily MAE |
|---|---:|
| 1–7 | 55.91 |
| 8–14 | 60.19 |
| 15–21 | 59.52 |
| 22–28 | 61.15 |

Later horizons are modestly harder on average, but degradation is not monotonic. The lowest individual-horizon MAE is at horizon 2 (45.25); the highest is horizon 28 (78.80), followed by horizon 27 (76.18) and horizon 20 (74.49). Horizon bias ranges from approximately -4.26% at horizon 8 to +3.67% at horizon 3, with no monotonic directional drift. Day-of-week composition and varying sales scale can affect these pooled descriptive metrics; no causal interpretation is made.

## Prediction clipping

Across 11,760 validation predictions (70 series × 28 horizons × 6 folds), **zero raw predictions were negative**. The declared nonnegative clipping operation therefore changed 0 predictions (0%). This is reported explicitly rather than assumed.

## Known limitations

- This is one fixed configuration, not a hyperparameter study.
- Weekly origin sampling reduces computation and changes the weighting of historical periods.
- Ordinal category coding is lightweight but may impose artificial numeric ordering despite categorical splits.
- The model uses raw sales with no transformation and limited calendar context.
- It excludes all price information and does not represent inventory availability or latent demand.
- Horizon metrics are pooled and scale-dependent; series-level RMSSE remains primary.
- Development-fold improvement does not guarantee lockbox or deployment performance.

## Decision for next experiment

The first global model is sufficiently promising to justify a subsequent, separately reviewed experiment. Any next step should remain controlled: investigate the six regressing series, especially `HOBBIES_2`; examine whether encoding or a small justified feature refinement improves stability; and predeclare the next comparison before training. The final model family is **not frozen**, and the lockbox must remain untouched.
