# Inventory decision-support artifacts

`inventory_bundle.joblib` is the compact generated runtime artifact. It contains only frozen configuration, provenance, and 70 per-series robust uncertainty summaries—not raw residual history, the forecasting model, or anomaly IF. `uncertainty_state.csv`, `metadata.json`, and `build_summary.json` are reviewable.

Rebuild with `PYTHONPATH=src .venv/bin/python -m marketmind.inventory.train`. This constructs an uncertainty artifact; it does not fit an inventory model or calculate an inventory KPI.
