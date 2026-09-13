# Production anomaly artifacts

`model.joblib` is the generated, git-ignored bundle containing exact per-series OOS residual histories and frozen IF-3 secondary diagnostic. `robust_residual_state.csv` is its reviewable state summary; it is not sufficient for exact updates by itself. `metadata.json` freezes the scoring contract and `training_summary.json` contains operational build facts only.

Rebuild with `PYTHONPATH=src .venv/bin/python -m marketmind.anomalies.train`. This is production retraining, not evaluation. The anomaly lockbox is consumed.
