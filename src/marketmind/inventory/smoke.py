"""Production inventory smoke test using explicitly labeled scenario/business inputs."""
from __future__ import annotations
import json,time,tracemalloc
import pandas as pd
from marketmind.inventory.bundle import load_bundle
from marketmind.inventory.predict import recommend_inventory

def fixtures(bundle):
    inventory=[]; forecasts=[]
    for i,r in enumerate(bundle.uncertainty_state.itertuples()):
        lead=i%14; review=1+(i%7); mode="user_buffer_days" if i==0 else "robust_normal"
        inventory.append({"snapshot_date":"2016-05-22","store_id":r.store_id,"dept_id":r.dept_id,"on_hand_inventory":100+i*3,
            "on_order_inventory":20 if i%4==0 else 0,"backorders":10 if i%9==0 else 0,"lead_time_days":lead,"review_period_days":review,
            "service_level_target":.95,"uncertainty_method":mode,"safety_buffer_days":2 if mode=="user_buffer_days" else None,
            "minimum_order_quantity":100 if i%10==0 else None,"case_pack_size":24 if i%11==0 else None,"maximum_order_quantity":500 if i%13==0 else None,
            "recent_anomaly_context":"scenario informational warning" if i==1 else None})
        for date in pd.date_range("2016-05-23",periods=28): forecasts.append({"forecast_date":date,"store_id":r.store_id,"dept_id":r.dept_id,"predicted_sales":float(15+i)})
    return pd.DataFrame(inventory),pd.DataFrame(forecasts)

def run(path="models/inventory/inventory_bundle.joblib"):
    started=time.perf_counter(); bundle=load_bundle(path); load=time.perf_counter()-started; inv,fc=fixtures(bundle)
    one_inv=inv.iloc[[0]]; key=one_inv.iloc[0]; one_fc=fc[(fc.store_id==key.store_id)&(fc.dept_id==key.dept_id)]
    started=time.perf_counter(); recommend_inventory(one_inv,one_fc,bundle); single=time.perf_counter()-started
    tracemalloc.start(); started=time.perf_counter(); output=recommend_inventory(inv,fc,bundle); batch=time.perf_counter()-started; _,peak=tracemalloc.get_traced_memory(); tracemalloc.stop()
    return {"label":"PRODUCTION INVENTORY SMOKE TEST — SCENARIO ONLY","inventory_input_provenance":"SCENARIO / BUSINESS INPUT — not observed M5 inventory truth",
        "forecast_input_provenance":"current-style 28-day forecast fixture — operational smoke only","decisions_generated":len(output),"series_count":output[["store_id","dept_id"]].drop_duplicates().shape[0],
        "protection_period_range":[int(output.protection_period_days.min()),int(output.protection_period_days.max())],"robust_normal_decisions":int((output.uncertainty_method=="robust_normal").sum()),
        "buffer_mode_decisions":int((output.uncertainty_method=="user_buffer_days").sum()),"zero_order_decisions":int((output.recommended_order_quantity==0).sum()),
        "positive_replenishment_decisions":int(output.replenishment_needed.sum()),"constrained_decisions":int(output.constraint_warning.notna().sum()),
        "artifact_load_seconds":load,"single_decision_seconds":single,"batch_70_series_seconds":batch,"peak_tracemalloc_bytes":peak}
if __name__=="__main__": print(json.dumps(run(),indent=2))
