# MarketMind AI — E-Commerce Intelligence Platform

MarketMind AI is a planned production-oriented ML engineering portfolio project for turning retail and e-commerce data into predictive insights and operational decision support. Phase 0 established an empirical dataset-to-module architecture; Phase 1 now defines the demand-forecasting methodology before experiments begin.

## Current status

**Phase 0 — Dataset Research & Feasibility: Complete**

**Phase 1 — Demand Forecasting: Methodology Definition**

M5 is selected for demand forecasting, later sales-anomaly work, and forecast input to inventory decision support; Complete Journey 2.0 is selected for customer segmentation and customer return risk; RetailRocket is selected for recommendation. Olist remains documented rejection evidence. Forecasting models and application services have not yet been developed.

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

If supported by the selected data, the project may eventually include reusable Python data and ML pipelines, versioned model artifacts and metadata, API-based inference through FastAPI, relational storage using PostgreSQL or Supabase, and a React/TypeScript interface. Docker may support reproducible packaging. None of these application components are initialized yet.

## Methodology

Future work will begin with explicit problem definitions and dataset audits. Time-dependent problems will preserve temporal ordering, prevent leakage, and maintain separate train, validation, and final test periods. Simple baselines will precede more complex approaches, metrics will match the decision problem, and error analysis will inform methodology choices. Outputs will not be described as probabilities, causal effects, or business impact unless the evidence and estimator semantics justify those claims.

See the [methodology principles](docs/methodology_principles.md) and frozen [forecasting methodology](docs/forecasting_methodology.md) for the working standards.

## Deployment constraint

The intended system should remain lightweight enough to preserve options for free deployment without paid hosting, credit-card-required services, or billing-enabled cloud accounts. Dependencies and infrastructure will be added only when justified.

## Repository map

- `data/`: local raw, intermediate, and processed datasets (ignored by Git)
- `notebooks/`: dataset audits and future experiments
- `src/marketmind/`: future reusable package code, organized by capability
- `models/`: future exported model artifacts and metadata (ignored by Git)
- `reports/`: research notes, decision records, and generated figures
- `docs/`: scope, methodology, and dataset requirements
- `tests/`: future automated tests
