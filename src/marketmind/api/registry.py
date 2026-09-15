"""Load-once artifact registry with independent module readiness."""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any,Callable
from marketmind.api.contracts import ARTIFACTS
from marketmind.api.settings import APISettings
from marketmind.forecasting.bundle import load_bundle as load_forecast
from marketmind.segmentation.bundle import load_bundle as load_segments
from marketmind.return_risk.bundle import load_bundle as load_risk
from marketmind.recommendations.bundle import load_bundle as load_recommendations
from marketmind.anomalies.bundle import load_artifacts as load_anomalies
from marketmind.inventory.bundle import load_bundle as load_inventory

LOADERS={"forecasting":load_forecast,"segmentation":load_segments,"return_risk":load_risk,"recommendations":load_recommendations,"anomalies":load_anomalies,"inventory":load_inventory}
METADATA_FILES={name:str(Path(path).with_name("metadata.json")) for name,path in ARTIFACTS.items()}

@dataclass
class ModuleState:
    ready:bool=False; bundle:Any=None; metadata:dict|None=None; reason_code:str|None=None; load_count:int=0

class ArtifactRegistry:
    def __init__(self,settings:APISettings,loaders:dict[str,Callable]|None=None):
        self.settings=settings; self.loaders=loaders or LOADERS; self.modules={name:ModuleState() for name in ARTIFACTS}
    def load_all(self):
        paths=self.settings.artifact_paths()
        for name in self.modules:
            state=self.modules[name]
            try:
                state.load_count+=1; bundle=self.loaders[name](paths[name]); metadata_path=self.settings.artifact_root/METADATA_FILES[name]
                metadata=json.loads(metadata_path.read_text())
                bundle_version=getattr(bundle,"model_version",getattr(bundle,"residual_state",None) and bundle.residual_state.model_version)
                metadata_version=metadata.get("model_version") or metadata.get("version")
                if metadata_version and bundle_version and metadata_version!=bundle_version: raise ValueError("artifact metadata version mismatch")
                if name=="recommendations":
                    _=bundle.item_to_index
                    bundle._api_popularity_order=tuple(sorted(zip(map(int,bundle.popularity_item_ids),map(int,bundle.popularity_counts)),key=lambda x:(-x[1],x[0])))
                state.bundle=bundle; state.metadata=metadata; state.ready=True; state.reason_code=None
            except Exception:
                state.bundle=None; state.metadata=None; state.ready=False; state.reason_code="ARTIFACT_LOAD_FAILED"
        return self
    def require(self,name):
        state=self.modules[name]
        if not state.ready: raise ModuleUnavailable(name)
        return state.bundle
    def readiness(self): return {name:state.ready for name,state in self.modules.items()}
    def safe_models(self):
        result=[]
        for name,state in self.modules.items():
            meta=state.metadata or {}; result.append({"module":name,"ready":state.ready,"version":meta.get("model_version") or meta.get("version"),
                "model_family":meta.get("model_family") or meta.get("primary_safety_stock_method"),"grain":meta.get("forecast_grain") or meta.get("grain") or meta.get("planning_grain"),
                "warnings":safe_warnings(name),"status_reason":state.reason_code})
        return result

class ModuleUnavailable(RuntimeError):
    def __init__(self,module): self.module=module; super().__init__("module unavailable")

def safe_warnings(name):
    return {"forecasting":["Forecast horizon is fixed at 28 days."],"segmentation":["Centroid distance is not probability or confidence."],
        "return_risk":["Score is an uncalibrated ranking score, not churn probability."],"recommendations":["Personalization depends on caller-supplied compact history."],
        "anomalies":["Anomaly score is not probability; HTTP scoring is non-mutating preview."],"inventory":["Business inventory inputs are scenarios; robust-normal safety stock is an approximation."]}[name]
