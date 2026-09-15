"""Build the compact frozen inventory uncertainty artifact; no ML fitting or KPI evaluation."""
from __future__ import annotations
import argparse,json,time
from datetime import datetime,timezone
from pathlib import Path
from marketmind.inventory.bundle import InventoryBundle,STATE_COLUMNS,save_bundle
from marketmind.inventory.config import *
from marketmind.inventory.uncertainty import load_final_oos_residuals,series_distribution

def build_bundle(artifact_dir:str|Path="reports/anomalies/artifacts"):
    started=time.perf_counter(); residuals=load_final_oos_residuals(artifact_dir); summary=series_distribution(residuals)
    state=summary[["store_id","dept_id","residual_count","median_residual","residual_mad","robust_daily_scale"]].rename(columns={"median_residual":"residual_median","robust_daily_scale":"daily_robust_scale"})
    state["residual_count"]=state.residual_count.astype(int)
    state["residual_source_start"]=residuals.date.min().date().isoformat(); state["residual_source_end"]=residuals.date.max().date().isoformat(); state=state[list(STATE_COLUMNS)]
    provenance={"source":"finalized legitimate point-in-time OOS forecast residual corpus","source_artifacts":["reports/anomalies/artifacts/oos_residual_blocks.csv","reports/anomalies/artifacts/lockbox_robust_scores_authentic.csv"],"rows":13720,"series":70,"dates":196,"start":"2015-02-02","end":"2016-05-22","consumed_lockbox_role":"historical forecast-error evidence only"}
    frozen={"mad_multiplier":MAD_MULTIPLIER,"primary_method":PRIMARY_SAFETY_STOCK_METHOD,"optional_method":OPTIONAL_SAFETY_STOCK_METHOD,"forecast_horizon":MAX_FORECAST_HORIZON,"service_level_range":[SERVICE_LEVEL_MIN,SERVICE_LEVEL_MAX],"constraint_order":list(CONSTRAINT_ORDER)}
    bundle=InventoryBundle(state,provenance,frozen); bundle.validate()
    return bundle,{"source_residual_rows":13720,"series_count":70,"residual_count_per_series":196,"date_coverage":["2015-02-02","2016-05-22"],"zero_mad_series_count":int((state.residual_mad==0).sum()),"build_seconds":time.perf_counter()-started}

def export(bundle,stats,output_dir:str|Path="models/inventory"):
    root=Path(output_dir); root.mkdir(parents=True,exist_ok=True); save_bundle(bundle,root/"inventory_bundle.joblib"); bundle.uncertainty_state.to_csv(root/"uncertainty_state.csv",index=False)
    metadata={"version":MODEL_VERSION,"schema_version":SCHEMA_VERSION,"module":"inventory_decision_support","planning_grain":list(PLANNING_GRAIN),"forecast_dependency":"unchanged Phase 1 HGBR-4 production forecast","forecast_horizon":28,"residual_source":bundle.provenance,"residual_rows":13720,"residual_series":70,"residual_dates":196,"mad_multiplier":MAD_MULTIPLIER,"primary_safety_stock_method":PRIMARY_SAFETY_STOCK_METHOD,"service_level_range":[SERVICE_LEVEL_MIN,SERVICE_LEVEL_MAX],"optional_buffer_method":OPTIONAL_SAFETY_STOCK_METHOD,"protection_period_rule":"lead_time_days + review_period_days","maximum_protection_period":28,"constraint_order":list(CONSTRAINT_ORDER),"price_policy":"excluded; no EOQ or cost optimization","anomaly_policy":"optional informational context only; never changes quantities","inventory_history_available":False,"historical_inventory_kpi_available":False,"robust_normal_limitation":ROBUST_NORMAL_WARNING,"created_at":datetime.now(timezone.utc).isoformat()}
    (root/"metadata.json").write_text(json.dumps(metadata,indent=2)+"\n"); stats={**stats,"artifact_sizes_bytes":{"inventory_bundle.joblib":(root/"inventory_bundle.joblib").stat().st_size,"uncertainty_state.csv":(root/"uncertainty_state.csv").stat().st_size}}
    (root/"build_summary.json").write_text(json.dumps(stats,indent=2)+"\n")

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--artifact-dir",type=Path,default=Path("reports/anomalies/artifacts")); p.add_argument("--output-dir",type=Path,default=Path("models/inventory")); a=p.parse_args(); bundle,stats=build_bundle(a.artifact_dir); export(bundle,stats,a.output_dir); print("Built 70-series inventory uncertainty bundle; no inventory KPI calculated.")
if __name__=="__main__": main()
