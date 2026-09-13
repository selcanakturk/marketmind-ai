# Return-risk artifact

`model.joblib` is the generated, ignored production bundle. `metadata.json` and `training_summary.json` are reviewable manifests. Rebuild with the command in `docs/return_risk_production.md`.

The bundle is frozen ET-2 on 16 features, retrained on 17,074 fully labeled April–November 2017 household snapshots. Scores are uncalibrated ranking values, not probabilities. The default policy flags the top 10% of eligible households with deterministic ties. The November lockbox is permanently consumed.
