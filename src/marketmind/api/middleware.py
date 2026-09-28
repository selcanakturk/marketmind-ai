"""Request identity, body/rate/concurrency bounds, security headers, and safe logs."""
from __future__ import annotations
import json,logging,time,uuid
from collections.abc import Callable
import anyio
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger=logging.getLogger("marketmind.api")
INFERENCE_POLICIES={
    "/api/v1/forecast":("forecasting","expensive"),"/api/v1/segments":("segmentation","standard"),
    "/api/v1/return-risk":("return_risk","return_risk"),"/api/v1/recommendations":("recommendations","standard"),
    "/api/v1/anomalies":("anomalies","expensive"),"/api/v1/inventory/recommend":("inventory","standard"),
}

def error_response(request_id:str,status:int,code:str,message:str,headers:dict[str,str]|None=None):
    response=JSONResponse(status_code=status,content={"error":{"code":code,"message":message,"details":None},"request_id":request_id})
    response.headers["X-Request-ID"]=request_id
    for key,value in (headers or {}).items(): response.headers[key]=value
    return response

class FixedWindowRateLimiter:
    """Small deterministic limiter for the frozen single-process deployment."""
    def __init__(self,window_seconds:int=60,clock:Callable[[],float]=time.monotonic): self.window_seconds=window_seconds; self.clock=clock; self.buckets={}
    def allow(self,client:str,policy:str,limit:int)->tuple[bool,int]:
        now=self.clock(); key=(client,policy); started,count=self.buckets.get(key,(now,0))
        if now-started>=self.window_seconds: started,count=now,0
        if count>=limit: return False,max(1,int(self.window_seconds-(now-started)+.999))
        self.buckets[key]=(started,count+1); return True,0

class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self,app,settings,header="X-Request-ID",limiter=None):
        super().__init__(app); self.settings=settings; self.header=header; self.concurrency=anyio.CapacityLimiter(settings.max_concurrent_requests); self.rate_limiter=limiter or FixedWindowRateLimiter(settings.rate_limit_window_seconds)
    async def dispatch(self,request,call_next):
        request.state.request_id=str(uuid.uuid4()); started=time.perf_counter(); module,rate_class=INFERENCE_POLICIES.get(request.url.path,("operations","operations"))
        limits={"operations":self.settings.rate_limit_operations,"standard":self.settings.rate_limit_standard,"expensive":self.settings.rate_limit_expensive,"return_risk":self.settings.rate_limit_return_risk}
        # Socket peer is used after server-level trusted-proxy normalization; the app never parses arbitrary X-Forwarded-For.
        client=request.client.host if request.client else "unknown"
        allowed,retry=(self.rate_limiter.allow(client,rate_class,limits[rate_class]) if self.settings.environment=="production" else (True,0))
        if not allowed:
            request.state.error_code="RATE_LIMITED"; response=error_response(request.state.request_id,429,"RATE_LIMITED","Request rate limit exceeded.",{"Retry-After":str(retry)})
        elif module=="operations": response=await call_next(request)
        else:
            try:
                with anyio.fail_after(self.settings.inference_queue_timeout_seconds):
                    await self.concurrency.acquire()
            except TimeoutError:
                request.state.error_code="SERVER_BUSY"; response=error_response(request.state.request_id,503,"SERVER_BUSY","The inference service is busy. Try again shortly.",{"Retry-After":"1"})
            else:
                try: response=await call_next(request)
                finally: self.concurrency.release()
        response.headers[self.header]=request.state.request_id; route=request.scope.get("route"); route_template=getattr(route,"path",request.url.path)
        fields={"event":"request","request_id":request.state.request_id,"method":request.method,"route":route_template,"status":response.status_code,"latency_ms":round((time.perf_counter()-started)*1000,3),"module":module,"error_code":getattr(request.state,"error_code","none")}
        if self.settings.environment=="production": logger.info(json.dumps(fields,separators=(",",":")))
        else: logger.info("request_id=%s method=%s route=%s status=%s latency_ms=%.3f module=%s error_code=%s",fields["request_id"],fields["method"],fields["route"],fields["status"],fields["latency_ms"],fields["module"],fields["error_code"])
        return response

class BodyLimitMiddleware:
    """Reject oversized Content-Length or streamed bodies without pre-buffering them."""
    def __init__(self,app,max_bytes:int): self.app=app; self.max_bytes=max_bytes
    async def __call__(self,scope,receive,send):
        if scope["type"]!="http": await self.app(scope,receive,send); return
        state=scope.get("state",{}); request_id=(state.get("request_id") if isinstance(state,dict) else getattr(state,"request_id",None)) or str(uuid.uuid4())
        headers={k.lower():v for k,v in scope.get("headers",[])}
        try: declared=int(headers.get(b"content-length",b"0"))
        except ValueError: declared=0
        if declared>self.max_bytes: await error_response(request_id,413,"REQUEST_TOO_LARGE","Request body exceeds the configured limit.")(scope,receive,send); return
        consumed=0
        async def limited_receive():
            nonlocal consumed
            message=await receive()
            if message["type"]=="http.request":
                consumed+=len(message.get("body",b""))
                if consumed>self.max_bytes: raise _BodyTooLarge
            return message
        try: await self.app(scope,limited_receive,send)
        except _BodyTooLarge: await error_response(request_id,413,"REQUEST_TOO_LARGE","Request body exceeds the configured limit.")(scope,receive,send)

class _BodyTooLarge(Exception): pass

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self,app,production=False): super().__init__(app); self.production=production
    async def dispatch(self,request,call_next):
        response=await call_next(request); response.headers["X-Content-Type-Options"]="nosniff"; response.headers["Referrer-Policy"]="no-referrer"; response.headers["X-Frame-Options"]="DENY"; response.headers["Content-Security-Policy"]="frame-ancestors 'none'"
        if self.production: response.headers["Strict-Transport-Security"]="max-age=31536000; includeSubDomains"
        return response
