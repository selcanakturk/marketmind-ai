"""Reviewable endpoint and dependency contracts for the future FastAPI service."""
from __future__ import annotations

API_VERSION="v1"
API_PREFIX=f"/api/{API_VERSION}"
ENDPOINTS=(
    ("GET","/health","liveness"),
    ("GET","/ready","artifact_readiness"),
    ("GET",f"{API_PREFIX}/models","model_metadata"),
    ("POST",f"{API_PREFIX}/forecast","forecasting"),
    ("POST",f"{API_PREFIX}/segments","segmentation"),
    ("POST",f"{API_PREFIX}/return-risk","return_risk"),
    ("POST",f"{API_PREFIX}/recommendations","recommendations"),
    ("POST",f"{API_PREFIX}/anomalies","anomalies"),
    ("POST",f"{API_PREFIX}/inventory/recommend","inventory"),
)
MODULE_DEPENDENCIES={
    "forecasting":(),"segmentation":(),"return_risk":(),"recommendations":(),
    "anomalies":("forecasting_contract",),
    "inventory":("forecasting_contract","anomaly_context_optional"),
}
ARTIFACTS={
    "forecasting":"models/forecasting/model.joblib",
    "segmentation":"models/segmentation/model.joblib",
    "return_risk":"models/return_risk/model.joblib",
    "recommendations":"models/recommendations/model.joblib",
    "anomalies":"models/anomalies/model.joblib",
    "inventory":"models/inventory/inventory_bundle.joblib",
}
STATE_POLICIES={"anomalies":"stateless_preview_no_commit","recommendations":"caller_supplied_compact_history","inventory":"stateless_scenario"}
ERROR_CODES={400:"malformed_request",404:"unknown_entity",409:"temporal_conflict",422:"validation_error",500:"internal_error",503:"module_unavailable"}
WARNING_CODES={"segmentation":"distance_not_confidence","return_risk":"ranking_score_not_probability","recommendations":"fallback_or_no_history","anomalies":"score_not_probability","inventory":"robust_normal_approximation"}
REQUEST_LIMITS={"forecast_history_rows":3920,"forecast_series":70,"segmentation_feature_rows":2500,"return_risk_transaction_rows":50000,"recommendation_history_items":500,"anomaly_rows":70,"inventory_decisions":70,"inventory_forecast_rows":1960}

def assert_acyclic_dependencies(graph=MODULE_DEPENDENCIES):
    visiting=set(); visited=set()
    def visit(node):
        if node in visiting: raise ValueError("module dependency cycle")
        if node in visited: return
        visiting.add(node)
        for dependency in graph.get(node,()):
            if dependency in graph: visit(dependency)
        visiting.remove(node); visited.add(node)
    for node in graph: visit(node)
    return True

