import json
import numpy as np
import pandas as pd
import pytest
from marketmind.inventory.bundle import InventoryBundle,load_bundle,save_bundle
from marketmind.inventory.config import *
from marketmind.inventory.predict import recommend_inventory

@pytest.fixture(scope="module")
def bundle(): return load_bundle("models/inventory/inventory_bundle.joblib")

def inputs(bundle,n=1,**changes):
    rows=[]
    for r in bundle.uncertainty_state.head(n).itertuples():
        value=dict(snapshot_date="2016-05-22",store_id=r.store_id,dept_id=r.dept_id,on_hand_inventory=100.,on_order_inventory=10.,backorders=5.,lead_time_days=7,review_period_days=7,service_level_target=.95)
        value.update(changes); rows.append(value)
    return pd.DataFrame(rows)

def forecasts(bundle,n=1,value=10.):
    rows=[]
    for r in bundle.uncertainty_state.head(n).itertuples():
        for date in pd.date_range("2016-05-23",periods=28): rows.append(dict(forecast_date=date,store_id=r.store_id,dept_id=r.dept_id,predicted_sales=value))
    return pd.DataFrame(rows)

def test_frozen_config_and_metadata(bundle):
    assert MAX_FORECAST_HORIZON==28 and MAD_MULTIPLIER==1.4826 and PRIMARY_SAFETY_STOCK_METHOD=="robust_normal"
    meta=json.load(open("models/inventory/metadata.json")); assert meta["inventory_history_available"] is False and meta["historical_inventory_kpi_available"] is False

def test_primary_default_formulas_and_explainability(bundle):
    out=recommend_inventory(inputs(bundle),forecasts(bundle),bundle).iloc[0]
    assert out.uncertainty_method=="robust_normal" and out.inventory_position==105
    assert out.forecast_lead_time_demand==70 and out.forecast_protection_demand==140 and out.expected_daily_demand==10
    assert out.target_stock==pytest.approx(out.forecast_protection_demand+out.safety_stock)
    assert out.unconstrained_order_quantity==pytest.approx(max(0,out.target_stock-out.inventory_position))
    assert out.historical_residual_count==196 and ROBUST_NORMAL_WARNING in out.planning_warning

def test_lead_zero_and_service_boundaries(bundle):
    for target in (.50,.999):
        out=recommend_inventory(inputs(bundle,lead_time_days=0,review_period_days=1,service_level_target=target),forecasts(bundle),bundle).iloc[0]
        assert out.forecast_lead_time_demand==0 and out.protection_period_days==1
    for target in (.4999,1.0):
        with pytest.raises(ValueError): recommend_inventory(inputs(bundle,service_level_target=target),forecasts(bundle),bundle)

@pytest.mark.parametrize("column,value",[("on_hand_inventory",-1),("on_order_inventory",-1),("backorders",-1),("on_hand_inventory",np.inf)])
def test_invalid_inventory_rejected(bundle,column,value):
    with pytest.raises((ValueError,TypeError)): recommend_inventory(inputs(bundle,**{column:value}),forecasts(bundle),bundle)

def test_horizon_boundaries(bundle):
    recommend_inventory(inputs(bundle,lead_time_days=21,review_period_days=7),forecasts(bundle),bundle)
    with pytest.raises(ValueError): recommend_inventory(inputs(bundle,lead_time_days=22,review_period_days=7),forecasts(bundle),bundle)
    with pytest.raises(ValueError): recommend_inventory(inputs(bundle,review_period_days=0),forecasts(bundle),bundle)

@pytest.mark.parametrize("kind",["negative","nonfinite","duplicate","missing","wrong_date","wrong_series"])
def test_strict_forecast_validation(bundle,kind):
    inv=inputs(bundle); f=forecasts(bundle)
    if kind=="negative": f.loc[0,"predicted_sales"]=-1
    elif kind=="nonfinite": f.loc[0,"predicted_sales"]=np.inf
    elif kind=="duplicate": f=pd.concat([f.iloc[:-1],f.iloc[[0]]])
    elif kind=="missing": f=f.iloc[:-1]
    elif kind=="wrong_date": f.loc[0,"forecast_date"]="2017-01-01"
    else: f.loc[:,"dept_id"]="UNKNOWN"
    with pytest.raises(ValueError): recommend_inventory(inv,f,bundle)

def test_unknown_series_rejected(bundle):
    inv=inputs(bundle); f=forecasts(bundle); inv.loc[0,"dept_id"]="UNKNOWN"; f.loc[:,"dept_id"]="UNKNOWN"
    with pytest.raises(ValueError): recommend_inventory(inv,f,bundle)

def test_buffer_mode_explicit_zero_and_no_blend(bundle):
    f=forecasts(bundle,value=3)
    out=recommend_inventory(inputs(bundle,uncertainty_method="user_buffer_days",safety_buffer_days=2),f,bundle).iloc[0]
    assert out.safety_stock==6 and out.safety_buffer_days==2 and BUFFER_WARNING in out.planning_warning
    zero=recommend_inventory(inputs(bundle,uncertainty_method="user_buffer_days",safety_buffer_days=0),f,bundle).iloc[0]; assert zero.safety_stock==0
    with pytest.raises(ValueError): recommend_inventory(inputs(bundle,safety_buffer_days=2),f,bundle)
    with pytest.raises(ValueError): recommend_inventory(inputs(bundle,uncertainty_method="user_buffer_days"),f,bundle)
    with pytest.raises(ValueError): recommend_inventory(inputs(bundle,uncertainty_method="user_buffer_days",safety_buffer_days=29),f,bundle)

def test_zero_mad_warning(bundle):
    state=bundle.uncertainty_state.copy(); state.loc[0,["residual_mad","daily_robust_scale"]]=0
    zero=InventoryBundle(state,bundle.provenance,bundle.frozen_config)
    out=recommend_inventory(inputs(zero),forecasts(zero),zero).iloc[0]
    assert out.safety_stock==0 and ZERO_MAD_WARNING in out.planning_warning

def test_monotonicity_negative_position_and_replenishment_flag(bundle):
    f=forecasts(bundle)
    low=recommend_inventory(inputs(bundle,service_level_target=.9),f,bundle).iloc[0]; high=recommend_inventory(inputs(bundle,service_level_target=.99),f,bundle).iloc[0]
    assert high.safety_stock>=low.safety_stock
    more_inventory=recommend_inventory(inputs(bundle,on_hand_inventory=1000),f,bundle).iloc[0]; assert more_inventory.unconstrained_order_quantity<=low.unconstrained_order_quantity
    negative=recommend_inventory(inputs(bundle,on_hand_inventory=0,on_order_inventory=0,backorders=100),f,bundle).iloc[0]; assert negative.inventory_position==-100 and negative.days_of_cover<0
    capped=recommend_inventory(inputs(bundle,on_hand_inventory=0,on_order_inventory=0,backorders=0,maximum_order_quantity=1),f,bundle).iloc[0]
    assert capped.replenishment_needed and capped.recommended_order_quantity==1 and capped.constraint_warning

def test_constraint_order_whole_units_and_zero_need(bundle):
    f=forecasts(bundle,value=0)
    zero=recommend_inventory(inputs(bundle,on_hand_inventory=100,minimum_order_quantity=100,case_pack_size=24,uncertainty_method="user_buffer_days",safety_buffer_days=0),f,bundle).iloc[0]; assert zero.recommended_order_quantity==0 and not zero.replenishment_needed and pd.isna(zero.days_of_cover)
    moq=recommend_inventory(inputs(bundle,on_hand_inventory=0,on_order_inventory=0,backorders=0,uncertainty_method="user_buffer_days",safety_buffer_days=0,minimum_order_quantity=100),forecasts(bundle,value=40/14),bundle).iloc[0]
    assert moq.recommended_order_quantity==100
    packed=recommend_inventory(inputs(bundle,on_hand_inventory=0,on_order_inventory=0,backorders=0,uncertainty_method="user_buffer_days",safety_buffer_days=0,case_pack_size=24),forecasts(bundle,value=101/14),bundle).iloc[0]
    assert packed.recommended_order_quantity==120 and isinstance(packed.recommended_order_quantity,(int,np.integer))

def test_anomaly_context_independent(bundle):
    inv=inputs(bundle); f=forecasts(bundle); base=recommend_inventory(inv,f,bundle)
    context=inv[["snapshot_date","store_id","dept_id"]].assign(recent_anomaly_context="review")
    warned=recommend_inventory(inv,f,bundle,context)
    pd.testing.assert_frame_equal(base.drop(columns=["recent_anomaly_context"]),warned.drop(columns=["recent_anomaly_context"]))

def test_batch_row_order_and_determinism(bundle):
    inv=inputs(bundle,3); f=forecasts(bundle,3)
    first=recommend_inventory(inv,f,bundle); second=recommend_inventory(inv.sample(frac=1,random_state=1),f.sample(frac=1,random_state=2),bundle)
    pd.testing.assert_frame_equal(first,second); pd.testing.assert_frame_equal(first,recommend_inventory(inv,f,bundle))

def test_serialization_roundtrip(bundle,tmp_path):
    path=tmp_path/"inventory.joblib"; save_bundle(bundle,path); loaded=load_bundle(path)
    pd.testing.assert_frame_equal(recommend_inventory(inputs(bundle),forecasts(bundle),bundle),recommend_inventory(inputs(bundle),forecasts(bundle),loaded))
