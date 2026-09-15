from datetime import datetime
from pydantic import Field,field_validator
from .common import StrictModel,ResponseMeta
class RecommendationRequest(StrictModel):
    visitor_id:int=Field(ge=0); snapshot_timestamp:datetime; k:int=Field(default=20,ge=1,le=1000); history_item_ids:list[int]=Field(default_factory=list,max_length=500)
    @field_validator("history_item_ids")
    @classmethod
    def distinct(cls,v):
        if len(v)!=len(set(v)): raise ValueError("history_item_ids must be distinct")
        if any(x<0 for x in v): raise ValueError("history item IDs must be nonnegative")
        return v
class RecommendationRow(StrictModel): visitor_id:int; snapshot_timestamp:datetime; rank:int; item_id:int; score:float; recommendation_source:str; seen_before:bool
class RecommendationResponse(StrictModel): meta:ResponseMeta; status:str; fallback_reason:str; rows:list[RecommendationRow]
