"""Exercise synthetic contract-limit requests; measures operations, never model quality."""
from __future__ import annotations
import platform,resource,time
from pathlib import Path
from fastapi.testclient import TestClient
from measure_request_sizes import PAYLOADS,sizes
from marketmind.api.main import create_app
from marketmind.api.settings import APISettings

def peak_rss_mib():
    value=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value/(1024 if platform.system()=="Linux" else 1024*1024)

def main():
    root=Path(__file__).resolve().parents[1]
    app=create_app(APISettings(environment="production",artifact_root=root,cors_origins=("https://frontend.example",),max_concurrent_requests=2))
    paths={"forecast":"forecast","segments":"segments","return-risk":"return-risk","recommendations":"recommendations","anomalies":"anomalies","inventory":"inventory/recommend"}
    with TestClient(app) as client:
        for name,path in paths.items():
            before=time.perf_counter(); response=client.post("/api/v1/"+path,json=PAYLOADS[name]); elapsed=(time.perf_counter()-before)*1000
            print(f"{name} bytes={sizes()[name]} status={response.status_code} latency_ms={elapsed:.3f} peak_rss_mib={peak_rss_mib():.2f}")
            if response.status_code!=200: print(f"{name}_safe_error={response.json().get('error',{}).get('code','unknown')}")

if __name__=="__main__": main()
