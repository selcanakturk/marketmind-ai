import pandas as pd
from marketmind.segmentation.assignment import assign_eligible_households
from marketmind.segmentation.config import FEATURE_ORDER
def run(request,bundle):
    if len(request.feature_rows)>2500: raise ValueError("segmentation request exceeds 2,500 rows")
    rows=[x.model_dump() for x in request.feature_rows]; features=pd.DataFrame(rows).set_index("household_id")
    if tuple(features.columns)!=FEATURE_ORDER: raise ValueError("segmentation feature schema does not match frozen nine-feature contract")
    result=assign_eligible_households(features,scaler=bundle.scaler,model=bundle.estimator,semantic_mapping=bundle.semantic_mapping,snapshot_date=request.snapshot_at)
    return [{"household_id":int(x.household_id),"snapshot_at":x.snapshot_date,"segment_code":x.segment_code,"segment_name":x.segment_name,"centroid_distance":float(x.distance_to_centroid)} for x in result.itertuples()]
