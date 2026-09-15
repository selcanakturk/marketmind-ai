from marketmind.inventory.predict import recommend_inventory
from .common import frame,records
def run(request,bundle):
    if len(request.inventory_inputs)>70: raise ValueError("inventory request exceeds 70 decisions")
    if len(request.forecasts)>1960: raise ValueError("inventory request exceeds 1,960 forecast rows")
    return records(recommend_inventory(frame(request.inventory_inputs),frame(request.forecasts),bundle))
