from datetime import datetime,timezone
from typing import Any
from pydantic import BaseModel,ConfigDict,Field
class StrictModel(BaseModel): model_config=ConfigDict(extra="forbid",allow_inf_nan=False)
class ResponseMeta(StrictModel):
    module_version:str|None=None
    artifact_version:str|None=None
    generated_at:datetime=Field(default_factory=lambda:datetime.now(timezone.utc))
    warnings:list[str]=Field(default_factory=list)
class StatusResponse(StrictModel): status:str
class ReadyResponse(StrictModel): status:str; modules:dict[str,bool]
class ModelInfo(StrictModel): module:str; ready:bool; version:str|None=None; model_family:str|None=None; grain:list[str]|None=None; warnings:list[str]; status_reason:str|None=None
class ModelsResponse(StrictModel): models:list[ModelInfo]
