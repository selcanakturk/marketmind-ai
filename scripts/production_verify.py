"""Production-mode artifact, registry, operations, and six-route smoke verification."""
from __future__ import annotations
import platform,resource,time
from pathlib import Path
from fastapi.testclient import TestClient
from marketmind.api.artifacts import verify_repository_artifacts
from marketmind.api.main import create_app
from marketmind.api.settings import APISettings
from marketmind.api.smoke import payloads

def peak_rss_mib():
    value=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value/(1024 if platform.system()=="Linux" else 1024*1024)

def main():
    root=Path(__file__).resolve().parents[1]; started=time.perf_counter(); verified=verify_repository_artifacts(root); verify_seconds=time.perf_counter()-started
    settings=APISettings(environment="production",artifact_root=root,cors_origins=("https://frontend.example",),max_concurrent_requests=2)
    app=create_app(settings); registry_started=time.perf_counter()
    with TestClient(app) as client:
        load_seconds=time.perf_counter()-registry_started
        assert client.get("/health").json()=={"status":"ok"}
        ready=client.get("/ready").json(); assert ready["status"]=="ready" and all(ready["modules"].values())
        assert len(client.get("/api/v1/models").json()["models"])==6
        results={}
        for name,body in payloads(client).items():
            before=time.perf_counter(); response=client.post("/api/v1/"+name,json=body); response.raise_for_status(); results[name]=(time.perf_counter()-before)*1000
    print(f"platform={platform.platform()} python={platform.python_version()} artifacts={len(verified)} verify_s={verify_seconds:.3f} registry_load_s={load_seconds:.3f} peak_rss_mib={peak_rss_mib():.2f}")
    for name,latency in results.items(): print(f"{name}_latency_ms={latency:.3f}")

if __name__=="__main__": main()
