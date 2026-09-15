from marketmind.forecasting.predict import forecast
from .common import frame,records
def run(request,bundle):
    if len(request.history)>3920: raise ValueError("forecast history exceeds 3,920 rows")
    series={(r.store_id,r.dept_id) for r in request.history}
    if len(series)>70: raise ValueError("forecast request exceeds 70 series")
    result=forecast(bundle,frame(request.history),frame(request.future_calendar)).rename(columns={"forecast_date":"date","forecast_horizon":"horizon"})
    return records(result)
