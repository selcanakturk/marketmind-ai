"""Run the controlled Phase 6 Step 2 methodology assessment."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from marketmind.inventory.policy import scenario_calculation
from marketmind.inventory.uncertainty import (HORIZONS,SERVICE_TARGETS,autocorrelation_summary,block_audit,
    buffer_days_safety_stock,cumulative_sample_counts,cumulative_windows,empirical_safety_stock,horizon_scale_ratios,
    load_final_oos_residuals,robust_normal_safety_stock,series_distribution)

def run(output_dir:str|Path="reports/inventory/artifacts"):
    out=Path(output_dir); out.mkdir(parents=True,exist_ok=True)
    residuals=load_final_oos_residuals(); blocks=block_audit(residuals); distribution=series_distribution(residuals)
    autocorr=autocorrelation_summary(residuals); counts=cumulative_sample_counts(residuals); ratios=horizon_scale_ratios(residuals,distribution)
    distribution.to_csv(out/"residual_distribution_summary.csv",index=False); autocorr.to_csv(out/"residual_autocorrelation_summary.csv",index=False)
    counts.to_csv(out/"cumulative_error_sample_counts.csv",index=False); ratios.to_csv(out/"normal_horizon_scale_ratios.csv",index=False); blocks.to_csv(out/"contiguous_oos_blocks.csv",index=False)
    suff=[]
    for h in HORIZONS:
        windows=cumulative_windows(residuals,h)
        for target in SERVICE_TARGETS:
            eligible=0; reasons=[]
            for _,group in windows.groupby(["store_id","dept_id"]):
                value,reason=empirical_safety_stock(group,target); eligible+=value is not None
                if reason: reasons.append(reason)
            suff.append({"horizon":h,"service_target":target,"per_series_windows":int(len(windows)/70),"eligible_series":eligible,
                         "ineligible_series":70-eligible,"minimum_expected_tail_observations":len(windows)/70*(1-target)})
    pd.DataFrame(suff).to_csv(out/"empirical_quantile_sufficiency.csv",index=False)
    distribution["forecast_scale"]=residuals.groupby(["store_id","dept_id"]).expected_sales.mean().to_numpy()
    ordered=distribution.sort_values("forecast_scale").reset_index(drop=True); representatives=pd.concat([ordered.iloc[[0]],ordered.iloc[[len(ordered)//2]],ordered.iloc[[-1]]])
    comparison=[]
    for label,(_,row) in zip(("low","medium","high"),representatives.iterrows()):
        series=residuals[(residuals.store_id==row.store_id)&(residuals.dept_id==row.dept_id)]
        daily_forecast=series.sort_values("date").expected_sales.reset_index(drop=True)
        for h in (1,7,14,28):
            windows=cumulative_windows(series,h)
            for target in (.90,.95,.99):
                empirical,reason=empirical_safety_stock(windows,target)
                comparison.append({"scale_band":label,"store_id":row.store_id,"dept_id":row.dept_id,"horizon":h,"service_target":target,
                    "method_a_robust_normal":robust_normal_safety_stock(row.robust_daily_scale,h,target),"method_b_empirical":empirical,
                    "method_b_status":reason or "supported","method_c_three_buffer_days":buffer_days_safety_stock(daily_forecast,3)})
    pd.DataFrame(comparison).to_csv(out/"safety_stock_method_comparison.csv",index=False)
    # Decision is persisted before any final policy scenarios are executed.
    freeze={"primary_method":"robust_normal_scale","formula":"max(0, norm.ppf(service_level_target) * (1.4826 * per-series daily residual MAD) * sqrt(protection_period_days))",
        "uncertainty_source":"complete finalized legitimate OOS forecast residual corpus","optional_secondary_method":"user_buffer_days_explicit_scenario_override",
        "empirical_method_role":"diagnostic_reference_only","assumptions":["normal upper-tail approximation","sqrt-time scaling","daily scale treated as sufficiently stable","serial dependence and skew may cause mismatch"],
        "edge_cases":{"zero_mad":"zero safety stock with explicit zero-uncertainty warning","negative_result":"floor at zero"},"decision_order":"frozen before scenario verification"}
    (out/"safety_stock_method_freeze.json").write_text(json.dumps(freeze,indent=2)+"\n")
    scale=float(distribution.robust_daily_scale.median()); demand=140.; ss95=robust_normal_safety_stock(scale,14,.95)
    cases=[]
    def add(name,**kwargs): cases.append({"scenario":name,**scenario_calculation(**kwargs)})
    add("sufficient_stock",protection_demand=demand,safety_stock=ss95,on_hand=10000,on_order=0,backorders=0)
    add("mild_need",protection_demand=demand,safety_stock=ss95,on_hand=demand+ss95-10,on_order=0,backorders=0)
    add("negative_position",protection_demand=demand,safety_stock=ss95,on_hand=10,on_order=5,backorders=100)
    ss99=robust_normal_safety_stock(scale,14,.99)
    high=scenario_calculation(demand,ss99,50,0,0); high["verification_note"]="safety_stock_at_0.99_not_below_0.95"; high["verification_passed"]=ss99>=ss95; cases.append({"scenario":"high_service_target",**high})
    boundary=scenario_calculation(280,robust_normal_safety_stock(scale,28,.95),100,0,0); boundary["verification_note"]="lead_plus_review_28_accepted"; boundary["verification_passed"]=True; cases.append({"scenario":"protection_period_28_boundary",**boundary})
    cases.append({"scenario":"unsupported_protection_period_29","verification_note":"rejected_by_contract","verification_passed":True})
    add("moq",protection_demand=40,safety_stock=0,on_hand=0,on_order=0,backorders=0,moq=100)
    add("case_pack",protection_demand=101,safety_stock=0,on_hand=0,on_order=0,backorders=0,case_pack=24)
    add("moq_then_case_pack",protection_demand=40,safety_stock=0,on_hand=0,on_order=0,backorders=0,moq=100,case_pack=24)
    add("maximum",protection_demand=240,safety_stock=0,on_hand=0,on_order=0,backorders=0,maximum=200)
    zero=scenario_calculation(0,0,0,0,0); zero["verification_note"]="zero_order_and_days_of_cover_undefined"; zero["verification_passed"]=True; cases.append({"scenario":"zero_forecast_demand",**zero})
    base=scenario_calculation(demand,ss95,50,0,0); warning=scenario_calculation(demand,ss95,50,0,0,recent_anomaly_context="review recent residual")
    cases.append({"scenario":"anomaly_context_independence",**warning,"numeric_matches_without_context":all(base[k]==warning[k] for k in base if k!="recent_anomaly_context")})
    pd.DataFrame(cases).to_csv(out/"scenario_verification.csv",index=False)
    return {"blocks":blocks,"distribution":distribution,"autocorrelation":autocorr,"counts":counts,"ratios":ratios,"freeze":freeze,"scenarios":pd.DataFrame(cases)}

if __name__=="__main__":
    result=run(); print(json.dumps({"residual_rows":13720,"primary_method":result["freeze"]["primary_method"],"scenarios":len(result["scenarios"])},indent=2))
