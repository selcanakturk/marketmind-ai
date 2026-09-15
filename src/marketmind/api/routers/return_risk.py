from fastapi import APIRouter,Request
from marketmind.api.registry import safe_warnings
from marketmind.api.schemas.common import ResponseMeta
from marketmind.api.schemas.return_risk import ReturnRiskRequest,ReturnRiskResponse
from marketmind.api.services.return_risk import run
router=APIRouter(prefix="/api/v1",tags=["return-risk"])
@router.post("/return-risk",response_model=ReturnRiskResponse,summary="Rank 28-day customer return risk")
def return_risk_endpoint(payload:ReturnRiskRequest,request:Request):
    bundle=request.app.state.registry.require("return_risk"); return {"meta":ResponseMeta(module_version=bundle.model_version,artifact_version=bundle.schema_version,warnings=safe_warnings("return_risk")),"rows":run(payload,bundle)}
