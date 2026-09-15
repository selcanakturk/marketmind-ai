"""Validated deterministic production inventory recommendations."""
from __future__ import annotations
import numpy as np
import pandas as pd
from marketmind.inventory.bundle import InventoryBundle
from marketmind.inventory.config import (BUFFER_WARNING,MAX_FORECAST_HORIZON,OPTIONAL_INPUT_COLUMNS,OPTIONAL_SAFETY_STOCK_METHOD,
    OUTPUT_COLUMNS,PRIMARY_SAFETY_STOCK_METHOD,REQUIRED_INPUT_COLUMNS,ROBUST_NORMAL_WARNING,ZERO_MAD_WARNING)
from marketmind.inventory.contracts import InventoryScenarioInput,aggregate_forecast,days_of_cover,inventory_position,target_and_unconstrained_order
from marketmind.inventory.policy import apply_operational_constraints
from marketmind.inventory.uncertainty import buffer_days_safety_stock,robust_normal_safety_stock

def _inputs(frame:pd.DataFrame)->pd.DataFrame:
    missing=set(REQUIRED_INPUT_COLUMNS)-set(frame.columns)
    if missing: raise ValueError(f"inventory inputs missing required columns: {sorted(missing)}")
    result=frame.copy()
    for c in OPTIONAL_INPUT_COLUMNS:
        if c not in result: result[c]=pd.NA
    result["uncertainty_method"]=result.uncertainty_method.fillna(PRIMARY_SAFETY_STOCK_METHOD)
    result["snapshot_date"]=pd.to_datetime(result.snapshot_date,errors="raise").dt.normalize()
    if result.duplicated(["snapshot_date","store_id","dept_id"]).any(): raise ValueError("duplicate inventory decision series-snapshot")
    return result

def _optional_number(value): return None if pd.isna(value) else float(value)
def _optional_integer(value,label):
    if pd.isna(value): return None
    number=float(value)
    if not np.isfinite(number) or not number.is_integer(): raise ValueError(f"{label} must be an integer")
    return int(number)

def _attach_context(inputs:pd.DataFrame,anomaly_context:pd.DataFrame|None)->pd.DataFrame:
    if anomaly_context is None: return inputs
    if inputs.recent_anomaly_context.notna().any(): raise ValueError("anomaly context must be supplied in only one place")
    required={"snapshot_date","store_id","dept_id","recent_anomaly_context"}
    if not required.issubset(anomaly_context): raise ValueError("anomaly_context schema invalid")
    context=anomaly_context[list(required)].copy(); context["snapshot_date"]=pd.to_datetime(context.snapshot_date,errors="raise").dt.normalize()
    if context.duplicated(["snapshot_date","store_id","dept_id"]).any(): raise ValueError("duplicate anomaly context")
    merged=inputs.drop(columns="recent_anomaly_context").merge(context,on=["snapshot_date","store_id","dept_id"],how="left",validate="one_to_one")
    return merged

def recommend_inventory(inventory_inputs:pd.DataFrame,forecasts:pd.DataFrame,bundle:InventoryBundle,anomaly_context:pd.DataFrame|None=None)->pd.DataFrame:
    """Return one decision per independently supplied series snapshot."""
    bundle.validate(); inputs=_attach_context(_inputs(inventory_inputs),anomaly_context)
    required_forecast={"forecast_date","store_id","dept_id","predicted_sales"}
    if not required_forecast.issubset(forecasts): raise ValueError(f"forecast missing columns: {sorted(required_forecast-set(forecasts))}")
    forecast=forecasts.copy(); forecast["forecast_date"]=pd.to_datetime(forecast.forecast_date,errors="raise").dt.normalize()
    if forecast.duplicated(["forecast_date","store_id","dept_id"]).any(): raise ValueError("duplicate forecast series-date")
    requested=set(map(tuple,inputs[["store_id","dept_id"]].itertuples(index=False,name=None)))
    supplied=set(map(tuple,forecast[["store_id","dept_id"]].drop_duplicates().itertuples(index=False,name=None)))
    if supplied!=requested: raise ValueError("forecast and inventory series sets must align exactly")
    state=bundle.uncertainty_state.set_index(["store_id","dept_id"]); rows=[]
    for row in inputs.sort_values(["snapshot_date","store_id","dept_id"]).itertuples(index=False):
        key=(row.store_id,row.dept_id)
        if key not in state.index: raise ValueError(f"unknown inventory series: {key}")
        mode=row.uncertainty_method
        if mode not in (PRIMARY_SAFETY_STOCK_METHOD,OPTIONAL_SAFETY_STOCK_METHOD): raise ValueError("unsupported uncertainty_method")
        moq=_optional_number(row.minimum_order_quantity); pack=_optional_integer(row.case_pack_size,"case_pack_size"); maximum=_optional_integer(row.maximum_order_quantity,"maximum_order_quantity")
        scenario=InventoryScenarioInput(row.snapshot_date,row.store_id,row.dept_id,float(row.on_hand_inventory),float(row.on_order_inventory),float(row.backorders),
            _optional_integer(row.lead_time_days,"lead_time_days"),_optional_integer(row.review_period_days,"review_period_days"),float(row.service_level_target),moq,pack,maximum)
        selected=forecast[(forecast.store_id==row.store_id)&(forecast.dept_id==row.dept_id)]
        demand=aggregate_forecast(selected,scenario); uncertainty=state.loc[key]
        buffer_days=_optional_integer(row.safety_buffer_days,"safety_buffer_days")
        warnings=[]
        if mode==PRIMARY_SAFETY_STOCK_METHOD:
            if buffer_days is not None: raise ValueError("safety_buffer_days requires explicit user_buffer_days mode")
            safety=robust_normal_safety_stock(float(uncertainty.daily_robust_scale),scenario.lead_time_days+scenario.review_period_days,scenario.service_level_target)
            warnings.append(ROBUST_NORMAL_WARNING)
            if float(uncertainty.residual_mad)==0: warnings.append(ZERO_MAD_WARNING)
        else:
            if buffer_days is None: raise ValueError("user_buffer_days mode requires safety_buffer_days")
            safety=buffer_days_safety_stock(selected.sort_values("forecast_date").predicted_sales.reset_index(drop=True),buffer_days); warnings.append(BUFFER_WARNING)
        position=inventory_position(scenario.on_hand_inventory,scenario.on_order_inventory,scenario.backorders)
        target,raw=target_and_unconstrained_order(demand["forecast_protection_demand"],safety,position)
        constrained=apply_operational_constraints(raw,moq,pack,maximum)
        cover=days_of_cover(position,demand["expected_daily_demand"])
        if demand["expected_daily_demand"]<=0: status="zero_expected_demand"
        elif constrained["constraint_warning"]: status="constrained_replenishment"
        elif raw>0: status="replenishment_recommended"
        else: status="sufficient_inventory"
        rows.append({"snapshot_date":row.snapshot_date,"store_id":row.store_id,"dept_id":row.dept_id,
            "on_hand_inventory":scenario.on_hand_inventory,"on_order_inventory":scenario.on_order_inventory,"backorders":scenario.backorders,"inventory_position":position,
            "lead_time_days":scenario.lead_time_days,"review_period_days":scenario.review_period_days,"protection_period_days":scenario.lead_time_days+scenario.review_period_days,
            **demand,"uncertainty_method":mode,"safety_buffer_days":buffer_days,"historical_residual_count":int(uncertainty.residual_count),
            "historical_residual_mad":float(uncertainty.residual_mad),"forecast_uncertainty_scale":float(uncertainty.daily_robust_scale),"service_level_target":scenario.service_level_target,
            "safety_stock":safety,"target_stock":target,"unconstrained_order_quantity":raw,"minimum_order_quantity":moq,"case_pack_size":pack,
            **constrained,"maximum_order_quantity":maximum,"replenishment_needed":raw>0,"days_of_cover":cover,"recent_anomaly_context":row.recent_anomaly_context,
            "planning_status":status,"planning_warning":" | ".join(warnings)})
    return pd.DataFrame(rows).loc[:,OUTPUT_COLUMNS].sort_values(["snapshot_date","store_id","dept_id"]).reset_index(drop=True)
