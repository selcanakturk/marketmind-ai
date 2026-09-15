from fastapi import APIRouter,Request
from marketmind.api.registry import safe_warnings
from marketmind.api.schemas.common import ResponseMeta
from marketmind.api.schemas.forecast import ForecastRequest,ForecastResponse
from marketmind.api.services.forecast import run
router=APIRouter(prefix="/api/v1",tags=["forecasting"])
@router.post("/forecast",response_model=ForecastResponse,summary="Generate the frozen 28-day demand forecast")
def forecast_endpoint(payload:ForecastRequest,request:Request):
    bundle=request.app.state.registry.require("forecasting"); return {"meta":ResponseMeta(module_version=bundle.model_version,artifact_version=bundle.schema_version,warnings=safe_warnings("forecasting")),"rows":run(payload,bundle)}
