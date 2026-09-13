"""Operational production smoke test; intentionally computes no quality metric."""
from __future__ import annotations
import json, time, tracemalloc
import pandas as pd
from marketmind.anomalies.bundle import load_artifacts
from marketmind.anomalies.predict import score_and_update

def run(path="models/anomalies/model.joblib") -> dict:
    started=time.perf_counter(); artifacts=load_artifacts(path); load_seconds=time.perf_counter()-started
    rows=[]; forecasts=[]
    for day,date in enumerate(("2016-05-23","2016-05-24")):
        for index,row in enumerate(artifacts.residual_state.series_metadata.itertuples()):
            expected=100.0+index; residual=(index%9-4)*(8.0+day)
            key={"date":date,"store_id":row.store_id,"dept_id":row.dept_id}
            rows.append({**key,"actual_sales":max(0.0,expected+residual)}); forecasts.append({**key,"expected_sales":expected})
    tracemalloc.start(); started=time.perf_counter()
    scored,updated=score_and_update(pd.DataFrame(rows),pd.DataFrame(forecasts),artifacts.residual_state,isolation_forest_bundle=artifacts.isolation_forest)
    runtime=time.perf_counter()-started; _,peak=tracemalloc.get_traced_memory(); tracemalloc.stop()
    return {"label":"PRODUCTION SMOKE TEST — NO OUTCOME METRICS","rows_scored":len(scored),
        "dates":[pd.Timestamp(v).date().isoformat() for v in sorted(scored.date.unique())],
        "defined_scores":int(scored.anomaly_score.notna().sum()),"undefined_scores":int(scored.anomaly_score.isna().sum()),
        "statistical_alert_count":int(scored.is_statistical_alert.sum()),"review_priority_count":int(scored.is_review_priority.sum()),
        "direction_distribution":scored.direction.value_counts().sort_index().to_dict(),"if_diagnostic_available":bool(scored.if_anomaly_score.notna().all()),
        "artifact_load_seconds":load_seconds,"daily_70_series_scoring_seconds":runtime/2,"multi_day_runtime_seconds":runtime,
        "peak_tracemalloc_bytes":peak,"state_update_success":updated.state_updated_through=="2016-05-24"}
if __name__ == "__main__": print(json.dumps(run(),indent=2))
