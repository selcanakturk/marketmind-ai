"""Construct synthetic maximum-contract payloads and report compact JSON byte sizes."""
from __future__ import annotations
import csv,json
from datetime import datetime,timedelta,timezone

def iso(day): return day.replace(tzinfo=timezone.utc).isoformat().replace("+00:00","Z")
with open("models/inventory/uncertainty_state.csv",newline="") as handle: series_keys=[(x["store_id"],x["dept_id"]) for x in csv.DictReader(handle)]

def feature(i=0): return {"household_id":i,"recency_days":1,"basket_frequency":1,"monetary_value":1,"avg_basket_value":1,"unique_departments":1,"department_spend_hhi":.5,"discount_share_of_gross":.1,"coupon_basket_rate":.1,"private_label_spend_share":.1}
history_start=datetime(2015,11,1)
history=[{"d":f"d_{day+1}","date":iso(history_start+timedelta(days=day)),"store_id":store,"dept_id":dept,"state_id":store.split("_")[0],"sales":1} for store,dept in series_keys for day in range(56)]
calendar=[{"d":f"d_{i+57}","date":iso(history_start+timedelta(days=56+i)),"event_name":"None","event_type":"None","snap_CA":0,"snap_TX":0,"snap_WI":0} for i in range(28)]
risk_start=datetime(2016,7,1)
transactions=[{"household_id":household,"store_id":1,"basket_id":household*20+visit,"product_id":1,"sales_value":1,"retail_disc":0,"coupon_disc":0,"coupon_match_disc":0,"transaction_timestamp":iso(risk_start+timedelta(days=visit*10))} for household in range(2500) for visit in range(20)]
actual=[{"date":"2016-05-23T00:00:00","store_id":store,"dept_id":dept,"actual_sales":1} for store,dept in series_keys]
expected=[{"date":x["date"],"store_id":x["store_id"],"dept_id":x["dept_id"],"expected_sales":1} for x in actual]
inputs=[{"snapshot_date":"2016-01-01T00:00:00Z","store_id":store,"dept_id":dept,"on_hand_inventory":1,"on_order_inventory":0,"backorders":0,"lead_time_days":1,"review_period_days":1,"service_level_target":.95,"uncertainty_method":"robust_normal"} for store,dept in series_keys]
forecasts=[{"forecast_date":iso(datetime(2016,1,2)+timedelta(days=day)),"store_id":store,"dept_id":dept,"predicted_sales":1} for store,dept in series_keys for day in range(28)]
PAYLOADS={
 "forecast":{"history":history,"future_calendar":calendar},
 "segments":{"snapshot_at":"2017-01-01T00:00:00Z","feature_rows":[feature(i) for i in range(2500)]},
 "return-risk":{"transactions":transactions,"products":[{"product_id":1,"department":"D","brand":"B"}],"snapshot_at":"2017-02-01T00:00:00Z","capacity":.1},
 "recommendations":{"visitor_id":1,"snapshot_timestamp":"2016-01-01T00:00:00Z","k":20,"history_item_ids":list(range(500))},
 "anomalies":{"actual_sales":actual,"expected_sales":expected,"calendar_context":None,"include_if_diagnostic":False},
 "inventory":{"inventory_inputs":inputs,"forecasts":forecasts},
}
def sizes(): return {name:len(json.dumps(payload,separators=(",",":"),ensure_ascii=False).encode()) for name,payload in PAYLOADS.items()}
if __name__=="__main__":
    for name,size in sizes().items(): print(f"{name}: {size} bytes")
