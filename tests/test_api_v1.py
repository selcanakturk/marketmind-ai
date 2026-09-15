from copy import deepcopy
from types import SimpleNamespace
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from marketmind.api.main import app
from marketmind.api.smoke import payloads
from marketmind.api.services.recommendations import recommend_compact
from marketmind.recommendations.bundle import RecommendationBundle
from marketmind.recommendations.predict import recommend_visitor

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as value: yield value

def test_health_ready_models_and_request_id(client):
    health=client.get("/health"); assert health.status_code==200 and health.json()=={"status":"ok"} and health.headers["X-Request-ID"]
    ready=client.get("/ready").json(); assert ready["status"]=="ready" and all(ready["modules"].values())
    models=client.get("/api/v1/models"); text=models.text
    assert models.status_code==200 and len(models.json()["models"])==6 and "/Users/" not in text and "model.joblib" not in text

def test_registry_loaded_once_and_partial_readiness_503(client):
    registry=client.app.state.registry; assert all(x.load_count==1 for x in registry.modules.values())
    state=registry.modules["forecasting"]; ready,bundle=state.ready,state.bundle; state.ready=False; state.bundle=None
    response=client.post("/api/v1/forecast",json={"history":[],"future_calendar":[]})
    state.ready=ready; state.bundle=bundle
    assert response.status_code==503 and response.json()["error"]["code"]=="MODULE_UNAVAILABLE"
    assert all(x.load_count==1 for x in registry.modules.values())

@pytest.mark.parametrize("name",["forecast","segments","return-risk","recommendations","anomalies","inventory/recommend"])
def test_all_business_endpoints_happy_deterministic_and_warn(client,name):
    body=payloads(client)[name]; first=client.post("/api/v1/"+name,json=body); second=client.post("/api/v1/"+name,json=body)
    assert first.status_code==200,first.text; assert first.json()["rows"]==second.json()["rows"] and first.json()["meta"]["warnings"]

def test_expected_shapes_and_semantics(client):
    data=payloads(client)
    assert len(client.post("/api/v1/forecast",json=data["forecast"]).json()["rows"])==28
    segment=client.post("/api/v1/segments",json=data["segments"]).json(); assert all("confidence" not in row for row in segment["rows"])
    risk=client.post("/api/v1/return-risk",json=data["return-risk"]).json(); assert "uncalibrated ranking" in str(risk) and "probability" in str(risk)
    rec=client.post("/api/v1/recommendations",json=data["recommendations"]).json(); assert len(rec["rows"])==5
    anomaly=client.post("/api/v1/anomalies",json=data["anomalies"]).json()["rows"][0]; assert {"anomaly_score","is_statistical_alert","daily_review_rank","is_review_priority"}.issubset(anomaly)
    inventory=client.post("/api/v1/inventory/recommend",json=data["inventory/recommend"]).json()["rows"][0]; assert inventory["target_stock"]==pytest.approx(inventory["forecast_protection_demand"]+inventory["safety_stock"])

def test_anomaly_http_is_non_mutating(client):
    state=client.app.state.registry.require("anomalies").residual_state
    before={key:value.copy() for key,value in state.histories.items()}; payload=payloads(client)["anomalies"]
    client.post("/api/v1/anomalies",json=payload); client.post("/api/v1/anomalies",json=payload)
    assert state.state_updated_through=="2016-05-22" and all(np.array_equal(before[key],state.histories[key]) for key in before)

def test_recommendation_fallback_and_history_limit(client):
    body=payloads(client)["recommendations"]; body["history_item_ids"]=[]
    result=client.post("/api/v1/recommendations",json=body); assert result.status_code==200 and result.json()["fallback_reason"]=="no_history"
    body["history_item_ids"]=list(range(501)); result=client.post("/api/v1/recommendations",json=body); assert result.status_code==422

def test_anomaly_and_inventory_limits(client):
    data=payloads(client); anomaly=data["anomalies"]; anomaly["actual_sales"]*=71; anomaly["expected_sales"]*=71
    assert client.post("/api/v1/anomalies",json=anomaly).status_code==422
    inventory=data["inventory/recommend"]; inventory["forecasts"]*=71
    assert client.post("/api/v1/inventory/recommend",json=inventory).status_code==422

def test_standard_error_envelope_is_sanitized(client):
    response=client.post("/api/v1/recommendations",json={"visitor_id":-1,"snapshot_timestamp":"bad","k":0,"history_item_ids":[]}); body=response.json()
    assert response.status_code==422 and body["request_id"]==response.headers["X-Request-ID"]
    assert set(body)=={"error","request_id"} and "traceback" not in response.text.lower() and "/Users/" not in response.text

def test_cors_and_openapi(client):
    cors=client.options("/api/v1/models",headers={"Origin":"http://localhost:3000","Access-Control-Request-Method":"GET"})
    assert cors.headers["access-control-allow-origin"]=="http://localhost:3000"
    schema=client.get("/openapi.json"); assert schema.status_code==200
    expected={"/health","/ready","/api/v1/models","/api/v1/forecast","/api/v1/segments","/api/v1/return-risk","/api/v1/recommendations","/api/v1/anomalies","/api/v1/inventory/recommend"}
    assert expected.issubset(schema.json()["paths"])

def test_compact_adapter_parity_with_frozen_semantics():
    bundle=RecommendationBundle(item_ids=np.array([1,2,3]),neighbor_indptr=np.array([0,2,4,5]),neighbor_indices=np.array([0,1,1,2,2]),neighbor_similarities=np.array([1.,.5,1.,.4,1.]),popularity_item_ids=np.array([1,2,3]),popularity_counts=np.array([2,1,1]),item_first_seen_ms=np.array([1,1,1]),training_cutoff_ms=3,model_version="retailrocket-item-cf-v1",schema_version="1.0",configuration={"neighbors":50},training_statistics={},library_versions={},research_metrics={},lockbox_status="consumed")
    bundle._api_popularity_order=((1,2),(2,1),(3,1))
    events=pd.DataFrame({"timestamp":[1,2,3,3],"visitorid":[10,20,20,30],"itemid":[1,1,2,3],"event":["view"]*4})
    old=recommend_visitor(events,10,3,bundle,k=3); rows,_,reason=recommend_compact(bundle,10,pd.to_datetime(3,unit="ms",utc=True),[1],3)
    assert reason=="" and old.itemid.tolist()==[x["item_id"] for x in rows]
    assert old.recommendation_score.tolist()==pytest.approx([x["score"] for x in rows])
    assert old.score_source.tolist()==[x["recommendation_source"] for x in rows]
    assert old.was_previously_seen.tolist()==[x["seen_before"] for x in rows]
