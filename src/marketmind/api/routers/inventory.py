from fastapi import APIRouter,Request
from marketmind.api.registry import safe_warnings
from marketmind.api.schemas.common import ResponseMeta
from marketmind.api.schemas.inventory import InventoryRequest,InventoryResponse
from marketmind.api.services.inventory import run
router=APIRouter(prefix="/api/v1",tags=["inventory"])
@router.post("/inventory/recommend",response_model=InventoryResponse,summary="Generate explainable inventory decisions")
def inventory_endpoint(payload:InventoryRequest,request:Request):
    bundle=request.app.state.registry.require("inventory"); return {"meta":ResponseMeta(module_version=bundle.model_version,artifact_version=bundle.schema_version,warnings=safe_warnings("inventory")),"rows":run(payload,bundle)}
