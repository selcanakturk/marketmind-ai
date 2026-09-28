"""Project-relative, environment-configurable settings contract."""
from __future__ import annotations
from dataclasses import dataclass,field
import os
from pathlib import Path
from urllib.parse import urlparse
from marketmind.api.contracts import API_PREFIX,ARTIFACTS

@dataclass(frozen=True)
class APISettings:
    environment:str="development"
    api_prefix:str=API_PREFIX
    artifact_root:Path=Path(".")
    log_level:str="INFO"
    cors_origins:tuple[str,...]=field(default_factory=lambda:("http://localhost:3000","http://localhost:5173"))
    request_id_header:str="X-Request-ID"
    max_concurrent_requests:int=4
    max_body_bytes:int=16*1024*1024
    inference_queue_timeout_seconds:float=.25
    rate_limit_operations:int=60
    rate_limit_standard:int=10
    rate_limit_expensive:int=6
    rate_limit_return_risk:int=3
    rate_limit_window_seconds:int=60
    def __post_init__(self):
        if self.max_concurrent_requests<1 or self.max_body_bytes<1024 or self.inference_queue_timeout_seconds<=0: raise ValueError("invalid request protection settings")
        if min(self.rate_limit_operations,self.rate_limit_standard,self.rate_limit_expensive,self.rate_limit_return_risk,self.rate_limit_window_seconds)<1: raise ValueError("invalid rate limit settings")
        for origin in self.cors_origins:
            parsed=urlparse(origin)
            if origin=="*" or parsed.scheme not in {"http","https"} or not parsed.netloc or parsed.path not in {"","/"} or parsed.query or parsed.fragment: raise ValueError("invalid CORS origin")
        if self.environment=="production" and (not self.cors_origins or any(urlparse(origin).scheme!="https" for origin in self.cors_origins)): raise ValueError("production requires explicit HTTPS CORS origins")
    @classmethod
    def from_environment(cls):
        origins=tuple(x.strip() for x in os.getenv("MARKETMIND_CORS_ORIGINS","http://localhost:3000,http://localhost:5173").split(",") if x.strip())
        return cls(environment=os.getenv("MARKETMIND_ENV","development"),artifact_root=Path(os.getenv("MARKETMIND_ARTIFACT_ROOT",".")),log_level=os.getenv("MARKETMIND_LOG_LEVEL","INFO"),cors_origins=origins,max_concurrent_requests=int(os.getenv("MARKETMIND_MAX_CONCURRENT_REQUESTS","4")),max_body_bytes=int(os.getenv("MARKETMIND_MAX_BODY_BYTES",str(16*1024*1024))),inference_queue_timeout_seconds=float(os.getenv("MARKETMIND_INFERENCE_QUEUE_TIMEOUT_SECONDS","0.25")),rate_limit_operations=int(os.getenv("MARKETMIND_RATE_LIMIT_OPERATIONS","60")),rate_limit_standard=int(os.getenv("MARKETMIND_RATE_LIMIT_STANDARD","10")),rate_limit_expensive=int(os.getenv("MARKETMIND_RATE_LIMIT_EXPENSIVE","6")),rate_limit_return_risk=int(os.getenv("MARKETMIND_RATE_LIMIT_RETURN_RISK","3")),rate_limit_window_seconds=int(os.getenv("MARKETMIND_RATE_LIMIT_WINDOW_SECONDS","60")))
    def artifact_paths(self): return {name:self.artifact_root/relative for name,relative in ARTIFACTS.items()}
