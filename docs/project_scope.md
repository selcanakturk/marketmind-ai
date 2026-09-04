# Project Scope

## Proposed V1 scope

The V1 scope is provisional and will be reduced or refined if Phase 0 dataset audits do not support a defensible implementation.

### Core ML

- **Demand Forecasting:** estimate future demand at a supported product or aggregate level using temporally valid evaluation.
- **Customer Segmentation:** identify useful, interpretable customer groups from observed transactional behavior.
- **Churn Prediction:** estimate future inactivity or attrition risk only when the data supports a defensible temporal churn definition. Features must be constructed from snapshots before their outcome windows.
- **Recommendation Engine:** rank relevant products for customers using available historical interactions and leakage-safe evaluation.

### Decision Support

- **Inventory Intelligence:** translate forecast outputs and genuine operational inputs into replenishment or stock-risk guidance. This capability may combine demand forecasts with operational and business rules rather than require a standalone ML model.
- **Sales Anomaly Detection:** flag unusual sales behavior for review. An initial approach may use deviations from expected demand or forecast residual behavior rather than a separate complex model.

## V2 candidate

- **Price Intelligence:** explore relationships among price, promotions, and demand. This remains a V2 candidate because observational correlation must not be presented as a causal price effect.

## Scope controls

Modules will not be forced onto unsuitable datasets. Churn will not be implemented unless persistent customer histories and a defensible temporal outcome definition are available. Operational fields such as inventory and lead time will not be fabricated when absent.

