from datetime import datetime
from pydantic import Field
from .common import StrictModel,ResponseMeta
class HistoryRow(StrictModel): d:str; date:datetime; store_id:str; dept_id:str; state_id:str; sales:float=Field(ge=0)
class CalendarRow(StrictModel): d:str; date:datetime; event_name:str; event_type:str; snap_CA:int=Field(ge=0,le=1); snap_TX:int=Field(ge=0,le=1); snap_WI:int=Field(ge=0,le=1)
class ForecastRequest(StrictModel): history:list[HistoryRow]; future_calendar:list[CalendarRow]
class ForecastRow(StrictModel): date:datetime; store_id:str; dept_id:str; state_id:str; horizon:int; predicted_sales:float
class ForecastResponse(StrictModel): meta:ResponseMeta; rows:list[ForecastRow]
