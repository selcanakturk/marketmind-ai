"""Compact serializable inventory uncertainty bundle."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from marketmind.inventory.config import MAD_MULTIPLIER,MODEL_VERSION,SCHEMA_VERSION

STATE_COLUMNS=("store_id","dept_id","residual_count","residual_median","residual_mad","daily_robust_scale","residual_source_start","residual_source_end")

@dataclass
class InventoryBundle:
    uncertainty_state:pd.DataFrame
    provenance:dict
    frozen_config:dict
    model_version:str=MODEL_VERSION
    schema_version:str=SCHEMA_VERSION
    def validate(self)->None:
        state=self.uncertainty_state
        if tuple(state.columns)!=STATE_COLUMNS or len(state)!=70 or state[["store_id","dept_id"]].duplicated().any(): raise ValueError("uncertainty state must contain exactly 70 unique series and frozen schema")
        if not (state.residual_count==196).all(): raise ValueError("each series must contain 196 legitimate OOS residuals")
        numeric=state[["residual_count","residual_median","residual_mad","daily_robust_scale"]].to_numpy(float)
        if not np.isfinite(numeric).all() or (state.residual_mad<0).any() or not np.allclose(state.daily_robust_scale,MAD_MULTIPLIER*state.residual_mad): raise ValueError("invalid uncertainty statistics")
        if self.model_version!=MODEL_VERSION or self.schema_version!=SCHEMA_VERSION: raise ValueError("inventory artifact version mismatch")

def save_bundle(bundle:InventoryBundle,path:str|Path)->None:
    bundle.validate(); target=Path(path); target.parent.mkdir(parents=True,exist_ok=True); joblib.dump(bundle,target,compress=3)
def load_bundle(path:str|Path)->InventoryBundle:
    result=joblib.load(Path(path))
    if not isinstance(result,InventoryBundle): raise TypeError("artifact is not InventoryBundle")
    result.validate(); return result
