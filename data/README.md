# Data Directory

- `raw/`: original, immutable dataset files.
- `interim/`: intermediate transformed outputs used during exploration.
- `processed/`: final, reproducible analysis- or model-ready datasets.

Raw data should never be manually edited. Transformations should be reproducible and write their outputs to the appropriate downstream directory. Dataset files are excluded from version control; this README preserves the directory guidance.

