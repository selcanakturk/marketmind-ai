import numpy as np
import pandas as pd
import pytest

from marketmind.inventory.contracts import InventoryScenarioInput,aggregate_forecast,days_of_cover,validate_protection_period
from marketmind.inventory.policy import apply_operational_constraints,scenario_calculation
from marketmind.inventory.uncertainty import (MAD_MULTIPLIER,block_audit,buffer_days_safety_stock,cumulative_windows,
    empirical_safety_stock,load_final_oos_residuals,robust_normal_safety_stock)


def test_only_complete_provenance_oos_corpus_accepted(tmp_path):
    source=load_final_oos_residuals(); assert len(source)==13720
    # A directory without both canonical, provenance-bearing sources is rejected.
    with pytest.raises((FileNotFoundError,ValueError)): load_final_oos_residuals(tmp_path)


def test_contiguous_windows_do_not_cross_gap_and_sums_are_correct():
    frame=pd.DataFrame({"block":"b","store_id":"S","dept_id":"D","date":pd.to_datetime(["2020-01-01","2020-01-02","2020-01-04"]),"residual":[1.,2.,4.]})
    with pytest.raises(ValueError): cumulative_windows(frame,3)
    clean=frame.iloc[:2]; windows=cumulative_windows(clean,2)
    assert len(windows)==1 and windows.cumulative_residual.iloc[0]==3


def test_authentic_window_sample_counts():
    frame=load_final_oos_residuals()
    assert len(cumulative_windows(frame,1))==13720
    assert len(cumulative_windows(frame,7))==10780
    assert len(cumulative_windows(frame,28))==490


def test_exact_robust_multiplier_and_normal_properties():
    assert MAD_MULTIPLIER==1.4826
    low=robust_normal_safety_stock(10,7,.90); high=robust_normal_safety_stock(10,7,.99)
    assert 0<=low<=high and robust_normal_safety_stock(10,14,.90)>=low
    assert robust_normal_safety_stock(0,28,.99)==0


def test_empirical_nonnegative_and_insufficiency_exposed():
    enough=pd.DataFrame({"cumulative_residual":np.arange(-50,50,dtype=float)})
    value,reason=empirical_safety_stock(enough,.90); assert value>=0 and reason is None
    value,reason=empirical_safety_stock(enough,.99); assert value is None and "insufficient" in reason
    favorable=pd.DataFrame({"cumulative_residual":np.arange(-100,-50,dtype=float)})
    value,reason=empirical_safety_stock(favorable,.80); assert value==0 and reason is None


def test_buffer_days_deterministic_and_not_service_derived():
    forecast=pd.Series([1.,2.,3.,4.])
    assert buffer_days_safety_stock(forecast,3)==6
    assert buffer_days_safety_stock(forecast,0)==0


def test_operational_constraint_examples_and_whole_units():
    assert apply_operational_constraints(0,moq=100,case_pack=24)["recommended_order_quantity"]==0
    assert apply_operational_constraints(40,moq=100)["recommended_order_quantity"]==100
    assert apply_operational_constraints(150,moq=100)["recommended_order_quantity"]==150
    assert apply_operational_constraints(101,case_pack=24)["recommended_order_quantity"]==120
    assert apply_operational_constraints(40,moq=100,case_pack=24)["recommended_order_quantity"]==120
    capped=apply_operational_constraints(239.2,maximum=200)
    assert capped["pre_max_constrained_quantity"]==240 and capped["recommended_order_quantity"]==200 and capped["constraint_warning"]
    assert isinstance(capped["recommended_order_quantity"],int)


def test_policy_invariants_and_anomaly_independence():
    base=scenario_calculation(100,20,50,10,5); more_hand=scenario_calculation(100,20,70,10,5)
    more_order=scenario_calculation(100,20,50,30,5); more_backorders=scenario_calculation(100,20,50,10,20)
    assert more_hand["unconstrained_order_quantity"]<=base["unconstrained_order_quantity"]
    assert more_order["unconstrained_order_quantity"]<=base["unconstrained_order_quantity"]
    assert more_backorders["unconstrained_order_quantity"]>=base["unconstrained_order_quantity"]
    warned=scenario_calculation(100,20,50,10,5,recent_anomaly_context="warning")
    for key in base:
        if key!="recent_anomaly_context": assert base[key]==warned[key]


def test_horizon_boundary_days_cover_and_strict_forecast_alignment():
    assert validate_protection_period(21,7)==28
    with pytest.raises(ValueError): validate_protection_period(22,7)
    assert days_of_cover(-10,5)==-2 and days_of_cover(10,0) is None
    s=InventoryScenarioInput("2020-01-01","S","D",0,0,0,1,1,.95)
    frame=pd.DataFrame({"forecast_date":pd.date_range("2020-01-02",periods=28),"store_id":"S","dept_id":"D","predicted_sales":1.})
    assert aggregate_forecast(frame,s)["forecast_lead_time_demand"]==1
    with pytest.raises(ValueError): aggregate_forecast(frame.iloc[:-1],s)
    duplicate=pd.concat([frame.iloc[:-1],frame.iloc[[0]]]);
    with pytest.raises(ValueError): aggregate_forecast(duplicate,s)
    wrong=frame.copy(); wrong.loc[0,"forecast_date"]=pd.Timestamp("2020-02-01")
    with pytest.raises(ValueError): aggregate_forecast(wrong,s)
