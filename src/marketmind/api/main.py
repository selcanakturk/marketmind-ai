"""MarketMind V1 FastAPI application."""
from __future__ import annotations
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from marketmind.api.errors import module_handler,unexpected_handler,validation_handler,value_handler
from marketmind.api.middleware import BodyLimitMiddleware,RequestContextMiddleware,SecurityHeadersMiddleware
from marketmind.api.registry import ArtifactRegistry,ModuleUnavailable
from marketmind.api.settings import APISettings
from marketmind.api.routers import anomalies,forecast,health,inventory,models,recommendations,return_risk,segmentation

def create_app(settings:APISettings|None=None,registry:ArtifactRegistry|None=None)->FastAPI:
    settings=settings or APISettings.from_environment()
    @asynccontextmanager
    async def lifespan(app):
        app.state.registry=registry or ArtifactRegistry(settings)
        if registry is None: app.state.registry.load_all()
        yield
    app=FastAPI(title="MarketMind AI API",version="1.0.0",description="Modular retail intelligence. M5, Complete Journey, and RetailRocket research entities are not cross-linked.",lifespan=lifespan,responses={413:{"description":"Request body exceeds the configured byte limit."},429:{"description":"Public-demo request rate exceeded."}})
    app.add_middleware(BodyLimitMiddleware,max_bytes=settings.max_body_bytes)
    app.add_middleware(SecurityHeadersMiddleware,production=settings.environment=="production")
    app.add_middleware(CORSMiddleware,allow_origins=list(settings.cors_origins),allow_credentials=False,allow_methods=["GET","POST"],allow_headers=["Content-Type","X-Request-ID"])
    app.add_middleware(RequestContextMiddleware,settings=settings,header=settings.request_id_header)
    app.add_exception_handler(RequestValidationError,validation_handler); app.add_exception_handler(ModuleUnavailable,module_handler); app.add_exception_handler(ValueError,value_handler); app.add_exception_handler(Exception,unexpected_handler)
    for router in (health.router,models.router,forecast.router,segmentation.router,return_risk.router,recommendations.router,anomalies.router,inventory.router): app.include_router(router)
    return app

app=create_app()
