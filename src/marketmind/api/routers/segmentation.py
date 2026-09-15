from fastapi import APIRouter,Request
from marketmind.api.registry import safe_warnings
from marketmind.api.schemas.common import ResponseMeta
from marketmind.api.schemas.segmentation import SegmentationRequest,SegmentationResponse
from marketmind.api.services.segmentation import run
router=APIRouter(prefix="/api/v1",tags=["segmentation"])
@router.post("/segments",response_model=SegmentationResponse,summary="Assign semantic customer segments")
def segments_endpoint(payload:SegmentationRequest,request:Request):
    bundle=request.app.state.registry.require("segmentation"); return {"meta":ResponseMeta(module_version=bundle.model_version,artifact_version=bundle.schema_version,warnings=safe_warnings("segmentation")),"rows":run(payload,bundle)}
