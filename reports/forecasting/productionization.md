# Forecasting Engine Productionization

## Frozen research candidate

MarketMind's frozen forecasting candidate is one global, horizon-conditioned Full Direct `HistGradientBoostingRegressor` at department × store × day grain. It forecasts 28 raw daily unit-sales values for each of 70 series, using the frozen lags, rolling summaries, identity, horizon, and known target-date calendar context. Predictions below zero are clipped to zero. Prices remain excluded.

Frozen HGBR parameters are `learning_rate=0.05`, `max_iter=160`, `max_leaf_nodes=63`, `max_depth=None`, `min_samples_leaf=100`, `l2_regularization=1.0`, squared-error loss, `early_stopping=False`, and `random_state=42`.

## Final lockbox evidence and consumption

The research candidate trained through `d_1913` and was evaluated once on `d_1914`–`d_1941`: macro RMSSE 0.80073, macro MAE 60.13, pooled WAPE 9.57%, and bias -4.76%. It beat seasonal naïve by 22.06% and historical mean by 30.58% in RMSSE.

**`d_1914`–`d_1941` is consumed.** Those results are immutable research evidence, not reusable validation. Productionization contains no model comparison, tuning, or new metric derived from that interval.

## Research versus production training boundary

- **Validated research candidate:** trained through `d_1913`, evaluated once on the consumed `d_1914`–`d_1941` lockbox.
- **Production-retrained artifact:** trained with the identical frozen configuration on all observed history through `d_1941`.

Production may incorporate `d_1914`–`d_1941` because model development and selection are closed and those observations are now historical. This does **not** constitute a new unbiased model evaluation. The production artifact has no fresh test metric; published metrics belong only to the research candidate.

## Centralized frozen configuration

`src/marketmind/forecasting/config.py` is the single production source for the 28-day horizon, lags 1/7/14/28/56, rolling windows 7/28/56, minimum 56-day history, model/schema versions, grain, feature ordering, categorical/numeric features, parameters, target definition, and post-processing.

## Training pipeline

`src/marketmind/forecasting/train.py`:

1. loads authentic M5 sales and calendar files from a configurable directory;
2. selects the validation or evaluation training matrix according to a configurable cutoff no later than `d_1941`;
3. aggregates item-store sales into exactly 70 department-store series;
4. applies weekly origins aligned backward from `training_end − 28`, minimum origin 56;
5. constructs the frozen Full Direct table;
6. fits a deterministic ordinal encoder and the exact frozen HGBR;
7. exports a compressed bundle and metadata.

The final production run through `d_1941` used 266 origins and 521,360 supervised rows. The analytical table and target occupied approximately 161.92 MB; local build and fit times were 4.50 and 6.53 seconds. No performance metric was calculated.

## Model bundle

`ForecastModelBundle` includes:

- fitted estimator and categorical encoder;
- exact feature column order and categorical/numeric partitions;
- frozen parameters and feature dtype schema;
- training cutoff, forecast horizon, and required history;
- all 70 series identities;
- model/schema versions and post-processing policy.

The joblib bundle reloads independently of notebook state.

## Inference contract

`forecast(bundle, history, future_calendar)` accepts long-form historical department-store sales and known future calendar context.

History requires:

```text
d, date, store_id, dept_id, state_id, sales
```

Future calendar requires exactly 28 consecutive dates and columns:

```text
d, date, event_name, event_type, snap_CA, snap_TX, snap_WI
```

Use the literal string `none` when no event applies; missing mandatory values are rejected. Inference requires no future actual sales, prices, inventory values, or hidden notebook objects.

Output schema:

```text
store_id, dept_id, state_id, forecast_date, forecast_horizon, predicted_sales
```

Full-platform inference produces 1,960 rows. Clean subset-series inference is also supported when identities occur in bundle metadata.

## Input validation

The inference layer rejects missing columns/values, unknown or inconsistent series identity, negative/non-finite sales, duplicate series-date rows, unequal or nonconsecutive series histories, fewer than 56 observations, a future calendar other than 28 unique consecutive dates, and a future start not immediately after the historical cutoff. Historical sales are never silently imputed.

## Metadata

`models/forecasting/metadata.json` records module and artifact roles, model/schema versions, family, strategy, grain, cutoffs, training timestamp, ordered feature schema, category/history/calendar definitions, target and post-processing, exact hyperparameters, Python/library versions, development protocol and metrics, final lockbox metrics, `lockbox_status: consumed`, production training statistics, and known limitations. It contains no raw M5 observations.

## Artifact structure and size

```text
models/forecasting/
├── model.joblib     535,711 bytes (Git-ignored)
├── metadata.json      3,734 bytes
└── README.md             672 bytes
```

Total footprint is 540,117 bytes, approximately 527.5 KiB or 0.515 MiB. The production bundle is approximately 2,000 times smaller than the roughly 1,050 MB ExtraTrees Direct development artifact. Artifact measurement did not change the frozen model.

## CLI usage

From the repository root:

```bash
PYTHONPATH=src python -m marketmind.forecasting.train
```

Optional arguments:

```bash
PYTHONPATH=src python -m marketmind.forecasting.train \
  --data-dir data/raw/m5 \
  --output-dir models/forecasting \
  --training-cutoff 1941
```

The CLI prints a concise summary and explicitly states that no production-retraining evaluation metric was calculated.

## Smoke test

The exported bundle was reloaded from `models/forecasting/model.joblib`. Using the final 56 observed days through `d_1941` and calendar-only `d_1942`–`d_1969`, it generated:

- exactly 70 series and 1,960 rows;
- horizons 1–28;
- dates 2016-05-23 through 2016-06-19;
- the exact six-column output schema;
- finite, nonnegative predictions ranging from 23.83 to 3,748.26.

This is functionality testing only. No future outcome was loaded and no performance metric was calculated.

## Tests

Twenty-three tests pass. Production-focused coverage includes configuration consistency, joblib round-trip, feature ordering, minimum history, mandatory columns, duplicate history, future-calendar length and chronology, deterministic 28-step shape, clipping, output schema, and subset-capable identity validation. Existing feature, metric, and recursive-leakage tests remain passing.

## Requirements

`joblib` was added explicitly because production code imports it directly for persistence. It is lightweight and already a scikit-learn dependency. No external modeling, serving, orchestration, or infrastructure dependency was added.

## Deployment considerations

The small compressed artifact, centralized schema, deterministic preprocessing, Python inference function, and strict input/output contract are suitable foundations for a later FastAPI adapter. Serving, authentication, storage, monitoring, and concurrency remain separate phases. The engine should load the bundle once per process rather than deserialize it for every request.

## Known limitations

- Observed sales are not unconstrained latent demand.
- The model operates at department-store grain, not item level.
- Prices are excluded and future realized prices are never assumed available.
- Late-horizon underforecast bias was observed in the consumed lockbox and was not corrected after evaluation.
- Operational inventory state is unavailable.
- Production retraining through `d_1941` has no new unbiased test estimate.
- Known calendar and SNAP inputs must be supplied correctly for the future horizon.
- Prediction intervals and uncertainty estimates are not implemented.
