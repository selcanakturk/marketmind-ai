from marketmind.anomalies.predict import score_batch
from .common import frame,records
def run(request,bundle):
    if len(request.actual_sales)>70 or len(request.expected_sales)>70: raise ValueError("anomaly request exceeds 70 rows")
    calendar=frame(request.calendar_context) if request.calendar_context is not None else None
    model=bundle.isolation_forest if request.include_if_diagnostic else None
    return records(score_batch(frame(request.actual_sales),frame(request.expected_sales),bundle.residual_state,calendar,model))
