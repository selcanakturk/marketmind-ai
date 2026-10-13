# MarketMind documentation index

This index separates current operational documentation from frozen research evidence and historical implementation records. Start with the root [project README](../README.md) for the product overview and verified headline results.

## Current architecture and operation

- [API architecture](api_architecture.md) — endpoint boundaries, artifact registry, contracts, errors, and statelessness
- [API usage](api_usage.md) — current local startup, request shapes, limits, and verification
- [Frontend architecture](frontend_architecture.md) — product workflows, UI state, responsive behavior, and accessibility contracts
- [Dataset requirements](dataset_requirements.md) — sources, access notes, and dataset-to-workflow fit
- [Methodology principles](methodology_principles.md) — leakage, temporal evaluation, baselines, metrics, and claim discipline
- [Deployment architecture](deployment_architecture.md) — frozen public-demo design; deployment is intentionally not implemented
- [Deployment runbook](deployment_runbook.md) — future deployment and rollback procedure, not evidence of a live service

## Workflow methods and production contracts

- **Forecasting:** [methodology](forecasting_methodology.md) · [productionization](../reports/forecasting/productionization.md) · [final lockbox evidence](../reports/forecasting/final_lockbox_results.md)
- **Segmentation:** [methodology](segmentation_methodology.md) · [productionization](../reports/segmentation/productionization.md) · [temporal stability](../reports/segmentation/temporal_stability_and_naming.md)
- **Customer re-engagement:** [methodology](return_risk_methodology.md) · [production contract](return_risk_production.md) · [final lockbox evidence](../reports/return_risk/final_lockbox_results.md)
- **Recommendations:** [methodology](recommendation_methodology.md) · [production contract](recommendation_production.md) · [final lockbox evidence](../reports/recommendation/final_lockbox_results.md)
- **Anomalies:** [methodology](anomaly_methodology.md) · [production contract](anomaly_production.md) · [final lockbox evidence](../reports/anomalies/final_lockbox_results.md)
- **Inventory:** [methodology](inventory_methodology.md) · [production contract](inventory_production.md) · [safety-stock assessment](../reports/inventory/safety_stock_assessment.md)

## Application and verification evidence

- [Frontend local guide](../frontend/README.md)
- [API production smoke](../reports/api/phase7_api_smoke_test.md)
- [Artifact manifest](../models/artifact_manifest.json)
- [Production hardening record](../reports/deployment/phase9_production_hardening.md)
- [Frontend implementation record](../reports/frontend/phase8_frontend_implementation.md)
- [Frontend QA record](../reports/frontend/phase8_frontend_final_qa.md)

## Historical research and decisions

Executed research notebooks are indexed in the [notebook guide](../notebooks/README.md). Module folders under `reports/` contain frozen experiment results, decision records, aggregated artifacts, and figures. Phase-specific status statements in those records describe the repository at that historical point; they should not be read as current application status.

Consumed-lockbox reports remain valid immutable evidence, but their evaluation intervals are permanently closed to further model or policy selection.
