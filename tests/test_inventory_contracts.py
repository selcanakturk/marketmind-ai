import numpy as np
import pandas as pd
import pytest

from marketmind.inventory.contracts import (
    InventoryScenarioInput, aggregate_forecast, apply_order_constraints, days_of_cover,
    inventory_position, normal_scale_safety_stock, target_and_unconstrained_order,
    validate_protection_period,
)


def scenario(**changes):
    values=dict(snapshot_date="2026-01-01",store_id="CA_1",dept_id="FOODS_1",
                on_hand_inventory=50,on_order_inventory=10,backorders=5,
                lead_time_days=7,review_period_days=7,service_level_target=.95)
    values.update(changes); return InventoryScenarioInput(**values)


def forecast(value=10.0, start="2026-01-02"):
    return pd.DataFrame({"forecast_date":pd.date_range(start,periods=28),"store_id":"CA_1",
                         "dept_id":"FOODS_1","predicted_sales":value})


def test_inventory_position_and_negative_position_from_backorders():
    assert inventory_position(50,10,5)==55
    assert inventory_position(1,2,8)==-5


@pytest.mark.parametrize("values",[(-1,0,0),(0,-1,0),(0,0,-1)])
def test_negative_inventory_components_rejected(values):
    with pytest.raises(ValueError): inventory_position(*values)


def test_protection_period_and_horizon_boundary():
    assert validate_protection_period(21,7)==28
    with pytest.raises(ValueError): validate_protection_period(22,7)


def test_forecast_alignment_and_demand_aggregation():
    result=aggregate_forecast(forecast(),scenario())
    assert result=={"forecast_lead_time_demand":70.0,"forecast_protection_demand":140.0,"expected_daily_demand":10.0}
    with pytest.raises(ValueError): aggregate_forecast(forecast(start="2026-01-03"),scenario())


def test_negative_demand_and_duplicate_forecasts_rejected():
    invalid=forecast(); invalid.loc[0,"predicted_sales"]=-1
    with pytest.raises(ValueError): aggregate_forecast(invalid,scenario())
    duplicated=pd.concat([forecast().iloc[:-1],forecast().iloc[[0]]])
    with pytest.raises(ValueError): aggregate_forecast(duplicated,scenario())


def test_moq_case_pack_max_and_zero_semantics():
    assert apply_order_constraints(0,minimum_order_quantity=20,case_pack_size=12)==(0,None)
    assert apply_order_constraints(5,minimum_order_quantity=20)==(20,None)
    assert apply_order_constraints(13,case_pack_size=12)==(24,None)
    quantity,warning=apply_order_constraints(51,minimum_order_quantity=20,case_pack_size=12,maximum_order_quantity=50)
    assert quantity==50 and warning is not None


def test_monotonic_inventory_and_demand_invariants():
    target_low,order_low=target_and_unconstrained_order(100,10,50)
    target_high,order_high=target_and_unconstrained_order(120,10,50)
    _,order_more_inventory=target_and_unconstrained_order(100,10,70)
    assert target_high>=target_low and order_high>=order_low and order_more_inventory<=order_low


def test_longer_period_does_not_reduce_nonnegative_cumulative_demand():
    frame=forecast(); frame["predicted_sales"]=np.arange(28,dtype=float)
    short=aggregate_forecast(frame,scenario(lead_time_days=3,review_period_days=2))
    long=aggregate_forecast(frame,scenario(lead_time_days=5,review_period_days=5))
    assert long["forecast_protection_demand"]>=short["forecast_protection_demand"]


def test_higher_service_target_does_not_reduce_candidate_safety_stock():
    low=normal_scale_safety_stock(12,14,.90); high=normal_scale_safety_stock(12,14,.99)
    assert high>=low>=0


def test_zero_demand_cover_and_determinism():
    assert days_of_cover(50,0) is None
    inputs=(17,20,12,100)
    assert apply_order_constraints(*inputs)==apply_order_constraints(*inputs)


def test_scenario_requires_explicit_valid_operational_inputs():
    scenario().validate()
    with pytest.raises(ValueError): scenario(on_hand_inventory=-1).validate()
    with pytest.raises(ValueError): scenario(service_level_target=.9999).validate()

