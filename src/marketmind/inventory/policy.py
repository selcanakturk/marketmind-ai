"""Frozen mathematical policy helpers for assessment; not a production engine."""
from __future__ import annotations
from math import ceil,isfinite
from typing import Any

def apply_operational_constraints(raw:float,moq:float|None=None,case_pack:int|None=None,maximum:int|None=None)->dict[str,Any]:
    if not isfinite(raw) or raw<0: raise ValueError("raw requirement must be finite and nonnegative")
    if moq is not None and (not isfinite(moq) or moq<=0): raise ValueError("MOQ must be positive")
    if case_pack is not None and (isinstance(case_pack,bool) or not isinstance(case_pack,int) or case_pack<=0): raise ValueError("case pack must be a positive whole-unit count")
    if maximum is not None and (isinstance(maximum,bool) or not isinstance(maximum,int) or maximum<=0): raise ValueError("maximum must be a positive whole-unit count")
    if raw==0: return {"pre_max_constrained_quantity":0,"recommended_order_quantity":0,"constraint_warning":None}
    adjusted=max(raw,moq or 0)
    if case_pack is not None: adjusted=ceil(adjusted/case_pack)*case_pack
    pre_max=ceil(adjusted)
    recommended=min(pre_max,maximum) if maximum is not None else pre_max
    warning="maximum_order_prevented_full_calculated_recommendation" if recommended<pre_max else None
    return {"pre_max_constrained_quantity":pre_max,"recommended_order_quantity":int(recommended),"constraint_warning":warning}

def scenario_calculation(protection_demand:float,safety_stock:float,on_hand:float,on_order:float,backorders:float,
                         moq:float|None=None,case_pack:int|None=None,maximum:int|None=None,recent_anomaly_context:str|None=None)->dict[str,Any]:
    from marketmind.inventory.contracts import inventory_position,target_and_unconstrained_order
    position=inventory_position(on_hand,on_order,backorders)
    target,raw=target_and_unconstrained_order(protection_demand,safety_stock,position)
    constrained=apply_operational_constraints(raw,moq,case_pack,maximum)
    return {"inventory_position":position,"target_stock":target,"unconstrained_order_quantity":raw,
            **constrained,"replenishment_needed":raw>0,"recent_anomaly_context":recent_anomaly_context}
