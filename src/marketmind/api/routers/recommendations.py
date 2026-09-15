from fastapi import APIRouter,Request
from marketmind.api.registry import safe_warnings
from marketmind.api.schemas.common import ResponseMeta
from marketmind.api.schemas.recommendations import RecommendationRequest,RecommendationResponse
from marketmind.api.services.recommendations import run
router=APIRouter(prefix="/api/v1",tags=["recommendations"])
@router.post("/recommendations",response_model=RecommendationResponse,summary="Recommend products from compact visitor history")
def recommendations_endpoint(payload:RecommendationRequest,request:Request):
    bundle=request.app.state.registry.require("recommendations"); rows,status,reason=run(payload,bundle); warnings=safe_warnings("recommendations")+([f"Fallback: {reason}."] if reason else [])
    return {"meta":ResponseMeta(module_version=bundle.model_version,artifact_version=bundle.schema_version,warnings=warnings),"status":status,"fallback_reason":reason,"rows":rows}
