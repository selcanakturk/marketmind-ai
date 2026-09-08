# Forecasting artifacts

`model.joblib` is the generated production-retrained forecasting bundle and remains Git-ignored. `metadata.json` is a small, reviewable description of the frozen configuration, research evidence, production cutoff, software versions, and limitations.

Generate both with:

```bash
PYTHONPATH=src python -m marketmind.forecasting.train
```

The production artifact is trained through `d_1941` after model development and the one-time lockbox evaluation closed. It has no new unbiased test metric. Validated metrics belong to the frozen research candidate trained through `d_1913` and evaluated once on the now-consumed `d_1914`–`d_1941` lockbox.
