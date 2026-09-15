from datetime import datetime
from pydantic import Field
from .common import StrictModel,ResponseMeta
class SegmentFeatureRow(StrictModel):
    household_id:int; recency_days:float=Field(ge=0); basket_frequency:float=Field(ge=0); monetary_value:float=Field(ge=0); avg_basket_value:float=Field(ge=0); unique_departments:float=Field(ge=0); department_spend_hhi:float=Field(ge=0,le=1); discount_share_of_gross:float=Field(ge=0,le=1); coupon_basket_rate:float=Field(ge=0,le=1); private_label_spend_share:float=Field(ge=0,le=1)
class SegmentationRequest(StrictModel): snapshot_at:datetime; feature_rows:list[SegmentFeatureRow]
class SegmentRow(StrictModel): household_id:int; snapshot_at:datetime; segment_code:str; segment_name:str; centroid_distance:float
class SegmentationResponse(StrictModel): meta:ResponseMeta; rows:list[SegmentRow]
