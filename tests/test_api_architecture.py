from pathlib import Path
import pytest
from marketmind.api.contracts import *
from marketmind.api.settings import APISettings

def test_version_and_endpoint_names_are_frozen_unique():
    assert API_VERSION=="v1" and API_PREFIX=="/api/v1"
    pairs=[(method,path) for method,path,_ in ENDPOINTS]; assert len(pairs)==len(set(pairs))
    assert ("GET","/health") in [(m,p) for m,p,_ in ENDPOINTS] and ("GET","/ready") in [(m,p) for m,p,_ in ENDPOINTS]

def test_business_endpoints_are_versioned():
    for method,path,_ in ENDPOINTS:
        if path not in ("/health","/ready"): assert path.startswith("/api/v1/")

def test_dependency_graph_is_acyclic_and_explicit():
    assert assert_acyclic_dependencies()
    assert MODULE_DEPENDENCIES["inventory"]==("forecasting_contract","anomaly_context_optional")
    with pytest.raises(ValueError): assert_acyclic_dependencies({"a":("b",),"b":("a",)})

def test_artifact_paths_are_relative_and_configurable(tmp_path,monkeypatch):
    assert all(not Path(path).is_absolute() for path in ARTIFACTS.values())
    monkeypatch.setenv("MARKETMIND_ARTIFACT_ROOT",str(tmp_path)); settings=APISettings.from_environment()
    assert all(path.is_relative_to(tmp_path) for path in settings.artifact_paths().values())

def test_special_state_contracts():
    assert STATE_POLICIES["anomalies"]=="stateless_preview_no_commit"
    assert STATE_POLICIES["recommendations"]=="caller_supplied_compact_history"
    assert STATE_POLICIES["inventory"]=="stateless_scenario"

def test_recommendation_contract_avoids_raw_event_table():
    assert REQUEST_LIMITS["recommendation_history_items"]==500
    assert "event" not in STATE_POLICIES["recommendations"]

def test_errors_warnings_and_limits_are_complete():
    assert set(ERROR_CODES)=={400,404,409,422,500,503}
    assert set(WARNING_CODES)=={"segmentation","return_risk","recommendations","anomalies","inventory"}
    assert REQUEST_LIMITS["inventory_forecast_rows"]==70*28 and REQUEST_LIMITS["anomaly_rows"]==70

def test_cors_defaults_are_explicit_not_wildcard():
    settings=APISettings(); assert settings.cors_origins and "*" not in settings.cors_origins
