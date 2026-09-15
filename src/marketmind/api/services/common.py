import pandas as pd
def frame(rows): return pd.DataFrame([row.model_dump() for row in rows])
def records(frame):
    value=frame.copy()
    value=value.astype(object).where(pd.notna(value),None)
    return value.to_dict(orient="records")
