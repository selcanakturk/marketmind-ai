from marketmind.return_risk.predict import score_return_risk
from .common import frame,records
def run(request,bundle):
    if len(request.transactions)>50000: raise ValueError("return-risk request exceeds 50,000 transactions")
    return records(score_return_risk(frame(request.transactions),frame(request.products),request.snapshot_at,bundle,request.capacity))
