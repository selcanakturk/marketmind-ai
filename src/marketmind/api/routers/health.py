from fastapi import APIRouter,Request
from marketmind.api.schemas.common import ReadyResponse,StatusResponse
router=APIRouter(tags=["operations"])
@router.get("/health",response_model=StatusResponse,summary="Service liveness")
def health(): return {"status":"ok"}
@router.get("/ready",response_model=ReadyResponse,summary="Artifact readiness")
def ready(request:Request):
    modules=request.app.state.registry.readiness(); return {"status":"ready" if all(modules.values()) else "degraded","modules":modules}
