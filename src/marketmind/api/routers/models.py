from fastapi import APIRouter,Request
from marketmind.api.schemas.common import ModelsResponse
router=APIRouter(prefix="/api/v1",tags=["models"])
@router.get("/models",response_model=ModelsResponse,summary="Production module metadata")
def models(request:Request): return {"models":request.app.state.registry.safe_models()}
