# Methodology Principles

All future data and ML work will follow these principles:

1. Establish the problem definition before modeling.
2. Audit the dataset before defining targets.
3. Preserve temporal ordering whenever time is involved.
4. Avoid random splits for temporal prediction problems unless explicitly justified.
5. Prevent target leakage and feature leakage.
6. Do not repeatedly use the final test set for model selection.
7. Build simple baselines before complex models.
8. Compare models using metrics appropriate to the problem.
9. Perform error analysis before methodology freeze.
10. Treat anomaly scores as scores, not probabilities.
11. Call model outputs probabilities only when the estimator semantics justify it.
12. Discuss calibration when risk probabilities are exposed.
13. Do not imply causal relationships from observational correlations.
14. Do not fabricate business impact.
15. Do not create unavailable business variables just to make the dashboard look realistic.
16. Prefer interpretable and lightweight solutions when performance differences do not justify complexity.

