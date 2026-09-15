from datetime import datetime
from pydantic import Field
from .common import StrictModel,ResponseMeta
class TransactionRow(StrictModel): household_id:int; store_id:int|str; basket_id:int; product_id:int; sales_value:float=Field(ge=0); retail_disc:float=Field(ge=0); coupon_disc:float=Field(ge=0); coupon_match_disc:float=Field(ge=0); transaction_timestamp:datetime
class ProductRow(StrictModel): product_id:int; department:str; brand:str|None=None
class ReturnRiskRequest(StrictModel): transactions:list[TransactionRow]; products:list[ProductRow]; snapshot_at:datetime; capacity:float|None=Field(default=None,gt=0,le=1)
class ReturnRiskRow(StrictModel): household_id:int; snapshot_date:datetime; eligibility_status:str; eligibility_reason:str; risk_score:float|None=None; risk_rank:int|None=None; risk_percentile:float|None=None; selected_capacity:float; flagged:bool
class ReturnRiskResponse(StrictModel): meta:ResponseMeta; rows:list[ReturnRiskRow]
