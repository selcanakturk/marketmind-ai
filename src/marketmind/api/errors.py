"""Sanitized API errors and centralized handlers."""
from __future__ import annotations
import logging
import re
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from marketmind.api.registry import ModuleUnavailable

def envelope(request:Request,code:str,message:str,details=None):
    request.state.error_code=code
    return {"error":{"code":code,"message":message,"details":details},"request_id":getattr(request.state,"request_id","")}

def _safe_engine_message(exc: ValueError) -> str:
    message=str(exc)
    if re.search(r"(?:^|\s)/(?:[^\s/]+/){2,}|[A-Za-z]:\\\\|Traceback|\.joblib",message,re.IGNORECASE):
        return "The request violates an engine input constraint."
    return message
async def validation_handler(request,exc:RequestValidationError):
    details=[{"field":".".join(map(str,e["loc"])),"message":e["msg"]} for e in exc.errors()]
    return JSONResponse(status_code=422,content=envelope(request,"VALIDATION_ERROR","Request validation failed.",details))
async def module_handler(request,exc:ModuleUnavailable): return JSONResponse(status_code=503,content=envelope(request,"MODULE_UNAVAILABLE",f"Module '{exc.module}' is unavailable."))
async def value_handler(request,exc:ValueError): return JSONResponse(status_code=422,content=envelope(request,"ENGINE_VALIDATION_ERROR",_safe_engine_message(exc)))
async def unexpected_handler(request,exc:Exception):
    logging.getLogger("marketmind.api").exception("unexpected request failure")
    return JSONResponse(status_code=500,content=envelope(request,"INTERNAL_ERROR","An unexpected internal error occurred."))
