# MarketMind AI — E-Commerce Intelligence Platform

MarketMind AI is a production-oriented ML engineering portfolio project for turning retail and e-commerce data into predictive insights and operational decision support. Phase 0 established the empirical dataset-to-module architecture. The Demand Forecasting research lifecycle and reusable forecasting engine are now complete; other MarketMind modules remain future work.

## Current status

**Phase 0 — Dataset Research & Feasibility: Complete**

**Phase 1 — Demand Forecasting: Production engine complete**

Demand Forecasting status:

- dataset research complete;
- methodology and temporal evaluation protocol complete;
- baseline and learned-model experiments complete;
- one-time final lockbox evaluation complete and consumed;
- frozen HGBR forecasting pipeline, serialized bundle, metadata, CLI, and inference contract complete.

M5 supports forecasting, later sales-anomaly work, and forecast input to inventory decision support; Complete Journey 2.0 supports future customer segmentation and return-risk work; RetailRocket supports future recommendation work. Olist remains documented rejection evidence. No API, frontend, anomaly, inventory, segmentation, return-risk, or recommendation implementation is claimed complete.

## Planned modules

### Core ML

- Demand Forecasting
- Customer Segmentation
- Churn Prediction
- Recommendation Engine

### Decision Support

- Inventory Intelligence
- Sales Anomaly Detection

Price Intelligence is a possible V2 capability and is outside the proposed V1 scope.

## Future architecture

The repository now includes a reusable Python forecasting pipeline, versioned metadata, a compact local model bundle, and validated inference. Future phases may add API-based inference through FastAPI, relational storage using PostgreSQL or Supabase, and a React/TypeScript interface. Docker may support reproducible packaging. None of those application components are initialized yet.

## Methodology

Future work will begin with explicit problem definitions and dataset audits. Time-dependent problems will preserve temporal ordering, prevent leakage, and maintain separate train, validation, and final test periods. Simple baselines will precede more complex approaches, metrics will match the decision problem, and error analysis will inform methodology choices. Outputs will not be described as probabilities, causal effects, or business impact unless the evidence and estimator semantics justify those claims.

See the [methodology principles](docs/methodology_principles.md) and frozen [forecasting methodology](docs/forecasting_methodology.md) for the working standards.

## Deployment constraint

The intended system should remain lightweight enough to preserve options for free deployment without paid hosting, credit-card-required services, or billing-enabled cloud accounts. Dependencies and infrastructure will be added only when justified.

## Repository map

- `data/`: local raw, intermediate, and processed datasets (ignored by Git)
- `notebooks/`: dataset audits and future experiments
- `src/marketmind/`: reusable package code organized by capability; forecasting training and inference are implemented
- `models/`: generated model bundles (ignored) and reviewable artifact metadata
- `reports/`: research notes, decision records, and generated figures
- `docs/`: scope, methodology, and dataset requirements
- `tests/`: automated unit and integration-oriented forecasting tests
