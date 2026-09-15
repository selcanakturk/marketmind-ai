"""Request identity, bounded concurrency, and privacy-safe access logging."""
from __future__ import annotations
import logging,time,uuid
import anyio
from starlette.middleware.base import BaseHTTPMiddleware

logger=logging.getLogger("marketmind.api")
class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self,app,max_concurrent_requests=4,header="X-Request-ID"):
        super().__init__(app); self.limiter=anyio.CapacityLimiter(max_concurrent_requests); self.header=header
    async def dispatch(self,request,call_next):
        request.state.request_id=str(uuid.uuid4()); started=time.perf_counter()
        async with self.limiter:
            response=await call_next(request)
        response.headers[self.header]=request.state.request_id
        logger.info("request_id=%s method=%s route=%s status=%s latency_ms=%.3f error_code=%s",request.state.request_id,request.method,request.url.path,response.status_code,(time.perf_counter()-started)*1000,getattr(request.state,"error_code","none"))
        return response
