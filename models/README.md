# Model Artifacts

This directory contains generated model artifacts and their associated metadata. The production-retrained forecasting artifact lives under `models/forecasting/`; its binary bundle is ignored while its README and metadata remain reviewable.

Each artifact should be traceable through metadata that includes, where relevant:

- model or module name
- version
- training timestamp
- dataset and dataset version
- feature schema
- validation strategy
- evaluation metrics
- decision threshold, if relevant
- library versions

Generated artifacts are excluded from version control; this README preserves the directory guidance.
