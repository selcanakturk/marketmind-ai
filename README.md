# MarketMind AI — E-Commerce Intelligence Platform

MarketMind AI is a production-oriented ML engineering portfolio project for turning retail and e-commerce data into predictive insights and operational decision support. Phase 0 established the empirical dataset-to-module architecture. Forecasting, segmentation, return risk, recommendation, and sales anomaly detection now have production engines.

## Current status

**Phase 0 — Dataset Research & Feasibility: Complete**

**Phase 1 — Demand Forecasting: Production engine complete**

**Phase 2 — Customer Segmentation: Production engine complete**

**Phase 3 — Customer Return Risk: Production engine complete**

**Phase 4 — Product Recommendation: Final Item-CF selected, strong lockbox generalization, production engine complete**

**Phase 5 — Sales Anomaly Detection: Research complete; strong one-time lockbox generalization; lockbox consumed; production engine complete**

**Phase 6 — Inventory Decision Support: Methodology complete; safety-stock method frozen; production engine complete**

**Phase 7 — FastAPI Backend: Architecture complete; V1 backend implemented; not deployed**

**Phase 8 — Frontend Dashboard: Step 1 contracts frozen; Step 2 working React/Vite dashboard implemented and tested; not deployed**

Demand Forecasting status:

- dataset research complete;
- methodology and temporal evaluation protocol complete;
- baseline and learned-model experiments complete;
- one-time final lockbox evaluation complete and consumed;
- frozen HGBR forecasting pipeline, serialized bundle, metadata, CLI, and inference contract complete.

M5 supports the productionized forecasting and sales-anomaly engines and forecast input to inventory decision support; Complete Journey 2.0 supports the productionized household-segmentation and return-risk engines; RetailRocket supports the productionized Item-CF recommendation engine. Olist remains documented rejection evidence. The FastAPI V1 backend and inventory engine are implemented; no frontend or deployment is claimed complete.

## Planned modules

### Core ML

- Demand Forecasting
- Customer Segmentation
- Customer Return Risk
- Recommendation Engine (frozen Item-CF production engine complete)

### Decision Support

- Inventory Decision Support (frozen robust-normal production engine complete; scenario-based business inputs required)
- Sales Anomaly Detection (frozen robust production engine complete; lockbox consumed)

Price Intelligence is a possible V2 capability and is outside the proposed V1 scope.

## Future architecture

The repository now includes reusable Python forecasting, segmentation, return-risk, recommendation, sales-anomaly, and inventory pipelines, versioned metadata, compact local model bundles, a FastAPI V1 backend, and an implemented React/TypeScript dashboard. The frontend architecture is in [`docs/frontend_architecture.md`](docs/frontend_architecture.md), with local setup in [`frontend/README.md`](frontend/README.md). Start the API with `PYTHONPATH=src .venv/bin/uvicorn marketmind.api.main:app --reload`, then run `npm install && npm run dev` inside `frontend/`. The applications are not deployed; persistence remains future work.

## Methodology

Future work will begin with explicit problem definitions and dataset audits. Time-dependent problems will preserve temporal ordering, prevent leakage, and maintain separate train, validation, and final test periods. Simple baselines will precede more complex approaches, metrics will match the decision problem, and error analysis will inform methodology choices. Outputs will not be described as probabilities, causal effects, or business impact unless the evidence and estimator semantics justify those claims.

See the [methodology principles](docs/methodology_principles.md), frozen [forecasting methodology](docs/forecasting_methodology.md), [segmentation methodology](docs/segmentation_methodology.md), [return-risk methodology](docs/return_risk_methodology.md), [recommendation methodology](docs/recommendation_methodology.md), [anomaly methodology](docs/anomaly_methodology.md), and [inventory methodology](docs/inventory_methodology.md) for the working standards.

## Deployment constraint

The intended system should remain lightweight enough to preserve options for free deployment without paid hosting, credit-card-required services, or billing-enabled cloud accounts. Dependencies and infrastructure will be added only when justified.

## Repository map

- `data/`: local raw, intermediate, and processed datasets (ignored by Git)
- `notebooks/`: dataset audits and future experiments
- `src/marketmind/`: reusable package code organized by capability; forecasting, segmentation, return-risk, recommendation, and anomaly engines are implemented
- `models/`: generated forecasting/segmentation bundles (ignored) and reviewable artifact metadata
- `reports/`: research notes, decision records, and generated figures
- `docs/`: scope, methodology, and dataset requirements
- `tests/`: automated forecasting, segmentation, return-risk, recommendation, and anomaly contract tests
- `frontend/`: React/TypeScript dashboard, typed API client, responsive UX, demo inputs, and isolated frontend tests
