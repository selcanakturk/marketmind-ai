# Recommendation production artifacts

`model.joblib` is the generated compact Item-CF bundle and is intentionally ignored because of its size. Run `python -m marketmind.recommendations.train` from the configured project environment to reproduce it from the local RetailRocket `events.csv`.

`metadata.json` and `training_summary.json` are reviewable manifests. They contain the frozen contract and operational training counts, but no newly calculated recommendation-quality outcomes.
