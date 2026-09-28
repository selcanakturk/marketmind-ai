import hashlib,json
from pathlib import Path
from types import SimpleNamespace
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from marketmind.api.artifacts import ArtifactVerifier,ArtifactVerificationError
from marketmind.api.main import create_app
from marketmind.api.middleware import BodyLimitMiddleware,RequestContextMiddleware,SecurityHeadersMiddleware
from marketmind.api.registry import ArtifactRegistry
from marketmind.api.settings import APISettings

def manifest_for(path:Path,data:bytes,**overrides):
    item={"module":"forecasting","path":"models/model.joblib","sha256":hashlib.sha256(data).hexdigest(),"size_bytes":len(data),"version":"v1","artifact_role":"production_bundle","immutable":True}|overrides
    (path/"models").mkdir(); (path/"models"/"model.joblib").write_bytes(data); (path/"models"/"artifact_manifest.json").write_text(json.dumps({"manifest_version":"1.0","artifacts":[item]})); return item

def test_artifact_verifier_valid(tmp_path):
    manifest_for(tmp_path,b"frozen"); assert ArtifactVerifier(tmp_path).verify("forecasting").read_bytes()==b"frozen"

@pytest.mark.parametrize(("change","code"),[("missing","ARTIFACT_MISSING"),("size","ARTIFACT_SIZE_MISMATCH"),("checksum","ARTIFACT_CHECKSUM_MISMATCH")])
def test_artifact_verifier_detects_integrity_failures(tmp_path,change,code):
    manifest_for(tmp_path,b"frozen")
    if change=="missing": (tmp_path/"models"/"model.joblib").unlink()
    elif change=="size": (tmp_path/"models"/"model.joblib").write_bytes(b"changed-size")
    else: (tmp_path/"models"/"model.joblib").write_bytes(b"broken")
    with pytest.raises(ArtifactVerificationError,match=code): ArtifactVerifier(tmp_path).verify("forecasting")

def test_artifact_verifier_rejects_malformed_and_unsafe_manifest(tmp_path):
    (tmp_path/"models").mkdir(); (tmp_path/"models"/"artifact_manifest.json").write_text("not-json")
    with pytest.raises(ArtifactVerificationError,match="ARTIFACT_MANIFEST_INVALID"): ArtifactVerifier(tmp_path)
    (tmp_path/"models"/"artifact_manifest.json").write_text(json.dumps({"manifest_version":"1.0","artifacts":[{"module":"x","path":"../escape","sha256":"0"*64,"size_bytes":1,"version":"v","artifact_role":"production","immutable":True}]}))
    with pytest.raises(ArtifactVerificationError,match="ARTIFACT_PATH_UNSAFE"): ArtifactVerifier(tmp_path)

def hardened_app(**overrides):
    settings=APISettings(environment="production",cors_origins=("https://frontend.example",),max_body_bytes=1024,rate_limit_standard=1,rate_limit_operations=10,**overrides); app=FastAPI()
    @app.post("/api/v1/segments")
    def endpoint(): return {"ok":True}
    app.add_middleware(BodyLimitMiddleware,max_bytes=settings.max_body_bytes); app.add_middleware(SecurityHeadersMiddleware); app.add_middleware(RequestContextMiddleware,settings=settings)
    return app

def test_body_limit_uses_canonical_error_and_request_id():
    with TestClient(hardened_app()) as client:
        response=client.post("/api/v1/segments",content=b"x"*1025,headers={"Content-Type":"application/json"})
    assert response.status_code==413 and response.json()["error"]["code"]=="REQUEST_TOO_LARGE"
    assert response.json()["request_id"]==response.headers["X-Request-ID"]

def test_rate_limit_is_canonical_deterministic_and_ignores_spoofed_forwarded_for():
    with TestClient(hardened_app()) as client:
        assert client.post("/api/v1/segments",headers={"X-Forwarded-For":"1.2.3.4"}).status_code==200
        response=client.post("/api/v1/segments",headers={"X-Forwarded-For":"5.6.7.8"})
    assert response.status_code==429 and response.json()["error"]["code"]=="RATE_LIMITED" and int(response.headers["Retry-After"])>0

def test_security_headers_and_production_settings_validation():
    with TestClient(hardened_app()) as client: response=client.post("/api/v1/segments")
    assert response.headers["X-Content-Type-Options"]=="nosniff" and response.headers["X-Frame-Options"]=="DENY"
    with pytest.raises(ValueError): APISettings(environment="production",cors_origins=("*",))
    with pytest.raises(ValueError): APISettings(environment="production",cors_origins=("http://example.com",))
    assert APISettings(environment="production",cors_origins=("https://example.com",)).cors_origins==("https://example.com",)

def test_checksum_failure_degrades_only_affected_module(monkeypatch):
    original=ArtifactVerifier.verify
    def fail_forecast(self,module,expected_relative_path=None):
        if module=="forecasting": raise ArtifactVerificationError("ARTIFACT_CHECKSUM_MISMATCH")
        return original(self,module,expected_relative_path)
    monkeypatch.setattr(ArtifactVerifier,"verify",fail_forecast)
    registry=ArtifactRegistry(APISettings()).load_all()
    assert registry.modules["forecasting"].ready is False and registry.modules["forecasting"].reason_code=="ARTIFACT_LOAD_FAILED"
    assert all(registry.modules[name].ready for name in registry.modules if name!="forecasting")
    assert not hasattr(registry,"train") and not hasattr(registry,"rebuild")

def test_production_cors_allows_exact_origin_and_denies_other():
    registry=SimpleNamespace(readiness=lambda:{},safe_models=lambda:[])
    app=create_app(APISettings(environment="production",cors_origins=("https://frontend.example",)),registry=registry)
    with TestClient(app) as client:
        allowed=client.options("/health",headers={"Origin":"https://frontend.example","Access-Control-Request-Method":"GET"})
        denied=client.options("/health",headers={"Origin":"https://other.example","Access-Control-Request-Method":"GET"})
    assert allowed.headers["access-control-allow-origin"]=="https://frontend.example" and "access-control-allow-credentials" not in allowed.headers
    assert "access-control-allow-origin" not in denied.headers
