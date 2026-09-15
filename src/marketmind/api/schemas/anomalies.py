from datetime import datetime
from pydantic import Field
from .common import StrictModel,ResponseMeta
class ActualSalesRow(StrictModel): date:datetime; store_id:str; dept_id:str; actual_sales:float=Field(ge=0)
class ExpectedSalesRow(StrictModel): date:datetime; store_id:str; dept_id:str; expected_sales:float=Field(ge=0)
class CalendarContextRow(StrictModel): date:datetime; event_name:str|None=None; event_type:str|None=None; snap_CA:int=Field(default=0,ge=0,le=1); snap_TX:int=Field(default=0,ge=0,le=1); snap_WI:int=Field(default=0,ge=0,le=1)
class AnomalyRequest(StrictModel): actual_sales:list[ActualSalesRow]; expected_sales:list[ExpectedSalesRow]; calendar_context:list[CalendarContextRow]|None=None; include_if_diagnostic:bool=False
class AnomalyRow(StrictModel):
    date:datetime; store_id:str; dept_id:str; actual_sales:float; expected_sales:float; residual:float; anomaly_score:float|None=None; direction:str; is_statistical_alert:bool; daily_review_rank:int|None=None; is_review_priority:bool; if_anomaly_score:float|None=None; event_name:str|None=None; event_type:str|None=None; snap_active:int; undefined_score_reason:str|None=None
class AnomalyResponse(StrictModel): meta:ResponseMeta; rows:list[AnomalyRow]
