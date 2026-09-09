# Segmentation artifacts

`model.joblib` is the generated frozen KMeans-3 bundle and remains Git-ignored. The reviewable `metadata.json`, `reference_profiles.csv`, and `monitoring_baseline.json` contain configuration and aggregated statistics only—no household transaction records.

Rebuild the reference artifacts with:

```bash
PYTHONPATH=src python -m marketmind.segmentation.train
```

The bundle is fitted at `2017-09-30 23:59:59` on 2,247 eligible Complete Journey grocery-retail households. Its assignments are descriptive, centroid distance is not confidence or probability, and the artifact is not automatically valid for unrelated retailers.
