# Sales anomaly production engine

## Purpose and frozen specification

The engine surfaces unusual department × store daily forecast residuals for investigation. The unchanged primary score is `(actual_sales - expected_sales - historical_residual_median) / (1.4826 × historical_residual_MAD)`, independently for each of 70 series. `|score| >= 3` is the statistical alert policy. The five largest defined absolute scores per day are the separate review policy, with store then department ascending as deterministic ties.

Frozen evidence remains in `reports/anomalies/final_lockbox_results.md`: primary generalization was assessed strong and IF-3 confirmed as secondary. These are references only; productionization did not recalculate them. The anomaly lockbox is permanently consumed.

## Architecture and forecast dependency

The production forecast engine supplies forward-looking expected sales, observed sales supplies actuals, this engine creates residuals/scores from persisted earlier residual state, and policy adds alerts/ranks. Optional IF-3 adds a diagnostic. The anomaly code does not duplicate or retrain Phase 1 forecasting.

Expected sales must be a forecast issued from an appropriate earlier snapshot. The forecast artifact trained through `d_1941` must not retrospectively score historical dates because that would leak future sales.

## Input contract

Actual input requires `date`, `store_id`, `dept_id`, and finite nonnegative `actual_sales`. Forecast input requires the same keys and finite `expected_sales`. Dates must parse; keys must be known and unique; key sets must match exactly. Mismatches, duplicates, stale dates, and invalid values fail rather than silently joining.

Optional one-row-per-date context provides `event_name`, `event_type`, and `snap_CA`, `snap_TX`, `snap_WI`. These are output context and IF inputs, never causal explanations.

## Residual state and update semantics

Initial state contains all 13,720 legitimately constructed OOS research residuals: 70 series, 196 observed dates, from `d_1466` (2015-02-02) through `d_1941` (2016-05-22). This includes the consumed lockbox only as historical state after policy freeze, not fresh validation. No fitted/in-sample residual is included.

Exact residual vectors are persisted because median/MAD cannot be updated exactly from summaries alone. At T, the complete batch scores from state through T−1, output is frozen, and only then are all T residuals appended explicitly. Multi-day calls repeat chronologically. Live evolution differs from research block-freeze scoring and does not alter research evidence.

If history is insufficient, MAD is zero, or scale is non-finite, score is undefined, alert is false, direction is `undefined`, and `undefined_score_reason` records why. No epsilon is substituted. Defined direction is `spike`, `drop`, or `neutral`.

## API and output

`score_batch(actual_sales, forecast_predictions, residual_state, calendar_context=None, isolation_forest_bundle=None)` is pure and accepts one date. `update_state(state, scored)` returns a new state. `score_and_update(...)` processes multiple dates chronologically and returns `(scores, updated_state)`.

Output fields are `date`, `store_id`, `dept_id`, `actual_sales`, `expected_sales`, `residual`, `anomaly_score`, `direction`, `is_statistical_alert`, `daily_review_rank`, `is_review_priority`, `if_anomaly_score`, `event_name`, `event_type`, `snap_active`, and `undefined_score_reason`. Undefined scores are not ranked or review-priority.

## IF, serialization, determinism, and limitations

IF-3 uses 300 estimators, max samples 1024, automatic contamination, all features, no bootstrap, seed 42, and exact feature order: robust score, residual, absolute residual, expected sales, weekday sine/cosine, event presence, state SNAP. It was production-fit without outcome metrics on all 13,720 OOS rows. It cannot change robust score, alert, or rank; there is no hybrid.

`models/anomalies/model.joblib` contains exact state plus IF; JSON metadata and operational training summary are reviewable. Save/load validates types, versions, catalog, and histories. Identical artifact/state/inputs produce identical results, including under row reordering.

M5 has no authentic anomaly labels; score is not a probability; unusual residuals are not causal diagnoses or proof of failure; forecast bias/drift can change direction composition (the consumed lockbox had a positive, spike-heavy shift); behavior depends on forecast quality; threshold 3 is policy, not universal truth; high/low anomalies do not imply operational failure; IF is secondary; prices are excluded; grain is not SKU-level; and updates must be chronological.

The Python contract is ready for a later FastAPI adapter. No HTTP endpoint exists; a future layer must preserve validation and explicit state persistence/concurrency control.
