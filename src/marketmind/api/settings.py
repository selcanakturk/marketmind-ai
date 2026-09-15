"""Project-relative, environment-configurable settings contract."""
from __future__ import annotations
from dataclasses import dataclass,field
import os
from pathlib import Path
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
    @classmethod
    def from_environment(cls):
        origins=tuple(x.strip() for x in os.getenv("MARKETMIND_CORS_ORIGINS","http://localhost:3000,http://localhost:5173").split(",") if x.strip())
        return cls(environment=os.getenv("MARKETMIND_ENV","development"),artifact_root=Path(os.getenv("MARKETMIND_ARTIFACT_ROOT",".")),log_level=os.getenv("MARKETMIND_LOG_LEVEL","INFO"),cors_origins=origins,max_concurrent_requests=int(os.getenv("MARKETMIND_MAX_CONCURRENT_REQUESTS","4")))
    def artifact_paths(self): return {name:self.artifact_root/relative for name,relative in ARTIFACTS.items()}
