"""Compact operational smoke runner for all V1 endpoints; no model evaluation."""
from __future__ import annotations
import json,time
import pandas as pd
from fastapi.testclient import TestClient
from marketmind.api.main import app

def payloads(client):
    cal=pd.read_csv("data/raw/m5/calendar.csv"); cal=cal[cal.d.isin([f"d_{x}" for x in range(1886,1970)])].copy(); cal["event_name_1"]=cal.event_name_1.fillna("none"); cal["event_type_1"]=cal.event_type_1.fillna("none")
    history=[{"d":r.d,"date":r.date,"store_id":"CA_1","dept_id":"FOODS_1","state_id":"CA","sales":100.} for r in cal.iloc[:56].itertuples()]
    future=[{"d":r.d,"date":r.date,"event_name":r.event_name_1,"event_type":r.event_type_1,"snap_CA":r.snap_CA,"snap_TX":r.snap_TX,"snap_WI":r.snap_WI} for r in cal.iloc[56:84].itertuples()]
    segment={"snapshot_at":"2017-09-30T23:59:59","feature_rows":[{"household_id":1,"recency_days":10,"basket_frequency":10,"monetary_value":500,"avg_basket_value":50,"unique_departments":5,"department_spend_hhi":.25,"discount_share_of_gross":.1,"coupon_basket_rate":.1,"private_label_spend_share":.2}]}
    dates=["2017-08-01","2017-08-25","2017-09-20","2017-10-15","2017-11-10"]
    transactions=[{"household_id":1,"store_id":1,"basket_id":i+1,"product_id":1,"sales_value":10,"retail_disc":0,"coupon_disc":0,"coupon_match_disc":0,"transaction_timestamp":d} for i,d in enumerate(dates)]
    risk={"transactions":transactions,"products":[{"product_id":1,"department":"GROCERY","brand":"NATIONAL"}],"snapshot_at":"2017-11-30T23:59:59","capacity":.1}
    rec_bundle=client.app.state.registry.require("recommendations"); history_item=int(rec_bundle.item_ids[0]); rec={"visitor_id":42,"snapshot_timestamp":pd.to_datetime(rec_bundle.training_cutoff_ms+1000,unit="ms",utc=True).isoformat(),"k":5,"history_item_ids":[history_item]}
    anomaly={"actual_sales":[{"date":"2016-05-23","store_id":"CA_1","dept_id":"FOODS_1","actual_sales":120}],"expected_sales":[{"date":"2016-05-23","store_id":"CA_1","dept_id":"FOODS_1","expected_sales":100}],"include_if_diagnostic":False}
    inv_input={"snapshot_date":"2016-05-22","store_id":"CA_1","dept_id":"FOODS_1","on_hand_inventory":100,"on_order_inventory":0,"backorders":0,"lead_time_days":7,"review_period_days":7,"service_level_target":.95}
    inv_forecast=[{"forecast_date":d.isoformat(),"store_id":"CA_1","dept_id":"FOODS_1","predicted_sales":10} for d in pd.date_range("2016-05-23",periods=28)]
    return {"forecast":{"history":history,"future_calendar":future},"segments":segment,"return-risk":risk,"recommendations":rec,"anomalies":anomaly,"inventory/recommend":{"inventory_inputs":[inv_input],"forecasts":inv_forecast}}

def run():
    results={}
    with TestClient(app) as client:
        for path in ("health","ready","api/v1/models"):
            started=time.perf_counter(); response=client.get("/"+path); results[path]={"status":response.status_code,"latency_seconds":time.perf_counter()-started,"rows":len(response.json().get("models",[]))}
        for name,payload in payloads(client).items():
            started=time.perf_counter(); response=client.post("/api/v1/"+name,json=payload); body=response.json(); results[name]={"status":response.status_code,"latency_seconds":time.perf_counter()-started,"rows":len(body.get("rows",[])),"warnings":body.get("meta",{}).get("warnings",[])}
    return {"label":"V1 API SMOKE TEST — OPERATIONAL ONLY","modules":results}
if __name__=="__main__": print(json.dumps(run(),indent=2))
