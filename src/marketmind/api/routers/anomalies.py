from fastapi import APIRouter,Request
from marketmind.api.registry import safe_warnings
from marketmind.api.schemas.common import ResponseMeta
from marketmind.api.schemas.anomalies import AnomalyRequest,AnomalyResponse
from marketmind.api.services.anomalies import run
router=APIRouter(prefix="/api/v1",tags=["anomalies"])
@router.post("/anomalies",response_model=AnomalyResponse,summary="Preview sales anomalies without state mutation")
def anomalies_endpoint(payload:AnomalyRequest,request:Request):
    bundle=request.app.state.registry.require("anomalies"); return {"meta":ResponseMeta(module_version=bundle.residual_state.model_version,artifact_version=bundle.residual_state.schema_version,warnings=safe_warnings("anomalies")+["Isolation Forest is secondary diagnostic only."]),"rows":run(payload,bundle)}
