import json

import joblib
import numpy as np
import pandas as pd
import pytest

from marketmind.anomalies.bundle import AnomalyArtifacts, RobustResidualState, load_artifacts, save_artifacts
from marketmind.anomalies.config import IF_PARAMETERS, MAD_MULTIPLIER, REVIEW_CAPACITY_PER_DAY, ROBUST_THRESHOLD
from marketmind.anomalies.predict import score_and_update, score_batch, update_state


def make_state(zero_mad=False):
    rows=[]; histories={}
    for i in range(70):
        store=f"STORE_{i+1:02d}"; dept="DEPT_1"; rows.append(("CA",store,dept))
        values=np.zeros(28) if zero_mad and i == 0 else np.tile([-1.0, 1.0], 14)
        histories[(store,dept)] = values
    return RobustResidualState(histories, pd.DataFrame(rows,columns=["state_id","store_id","dept_id"]), "2020-01-01", 1, "test")


def inputs(residuals, date="2020-01-02"):
    actual=[]; forecast=[]
    for i,residual in enumerate(residuals):
        key={"date":date,"store_id":f"STORE_{i+1:02d}","dept_id":"DEPT_1"}
        forecast.append({**key,"expected_sales":10.0}); actual.append({**key,"actual_sales":10.0+residual})
    return pd.DataFrame(actual),pd.DataFrame(forecast)


def test_frozen_config():
    assert MAD_MULTIPLIER == 1.4826 and ROBUST_THRESHOLD == 3.0 and REVIEW_CAPACITY_PER_DAY == 5
    assert IF_PARAMETERS == {"n_estimators":300,"max_samples":1024,"contamination":"auto","max_features":1.0,"bootstrap":False,"random_state":42,"n_jobs":1}


def test_residual_direction_threshold_boundary_and_top_five():
    state=make_state(); boundary=3*MAD_MULTIPLIER
    actual,forecast=inputs([boundary,-boundary,0,1,2,3,4])
    scored=score_batch(actual,forecast,state)
    assert np.allclose(scored.residual.sort_values(), np.sort([boundary,-boundary,0,1,2,3,4]))
    boundary_rows=scored[np.isclose(scored.anomaly_score.abs(),3)]
    assert boundary_rows.is_statistical_alert.all() and set(boundary_rows.direction)=={"spike","drop"}
    assert scored.is_review_priority.sum()==5 and scored.daily_review_rank.dropna().nunique()==7


def test_zero_mad_is_undefined_and_not_ranked():
    actual,forecast=inputs([5,1,2,3,4,5,6])
    scored=score_batch(actual,forecast,make_state(True))
    row=scored.loc[scored.store_id=="STORE_01"].iloc[0]
    assert np.isnan(row.anomaly_score) and row.direction=="undefined" and row.undefined_score_reason=="zero_mad"
    assert not row.is_statistical_alert and not row.is_review_priority and pd.isna(row.daily_review_rank)


def test_tie_ranking_and_row_order_invariance():
    actual,forecast=inputs([2]*7)
    first=score_batch(actual,forecast,make_state())
    second=score_batch(actual.sample(frac=1,random_state=4),forecast.sample(frac=1,random_state=8),make_state())
    pd.testing.assert_frame_equal(first,second)
    assert first.loc[first.is_review_priority,"store_id"].tolist()==["STORE_01","STORE_02","STORE_03","STORE_04","STORE_05"]


def test_no_self_contamination_and_explicit_update():
    state=make_state(); actual,forecast=inputs([100]*7)
    scored=score_batch(actual,forecast,state)
    assert len(state.histories[("STORE_01","DEPT_1")])==28
    assert scored.loc[0,"anomaly_score"] == pytest.approx(100/MAD_MULTIPLIER)
    updated=update_state(state,scored)
    assert len(updated.histories[("STORE_01","DEPT_1")])==29 and len(state.histories[("STORE_01","DEPT_1")])==28


def test_chronological_multiday_update():
    state=make_state(); a1,f1=inputs([100]*7); a2,f2=inputs([1]*7,"2020-01-03")
    scored,updated=score_and_update(pd.concat([a2,a1]),pd.concat([f2,f1]),state)
    first=scored[scored.date==pd.Timestamp("2020-01-02")].iloc[0]
    second=scored[scored.date==pd.Timestamp("2020-01-03")].iloc[0]
    assert first.anomaly_score==pytest.approx(100/MAD_MULTIPLIER)
    assert second.anomaly_score != pytest.approx(1/MAD_MULTIPLIER)
    assert updated.state_updated_through=="2020-01-03" and len(updated.histories[("STORE_01","DEPT_1")])==30


@pytest.mark.parametrize("mutation",["duplicate","negative","nonfinite","mismatch","unknown"])
def test_input_validation(mutation):
    actual,forecast=inputs([1]*7); state=make_state()
    if mutation=="duplicate": actual=pd.concat([actual,actual.iloc[[0]]])
    elif mutation=="negative": actual.loc[0,"actual_sales"]=-1
    elif mutation=="nonfinite": forecast.loc[0,"expected_sales"]=np.inf
    elif mutation=="mismatch": forecast.loc[0,"dept_id"]="FOODS_2"
    else: actual.loc[0,"dept_id"]="UNKNOWN"; forecast.loc[0,"dept_id"]="UNKNOWN"
    with pytest.raises(ValueError): score_batch(actual,forecast,state)


def test_if_is_optional_secondary_and_serialization_roundtrip(tmp_path):
    production=load_artifacts("models/anomalies/model.joblib")
    full_actual=pd.DataFrame([{"date":"2016-05-23","store_id":r.store_id,"dept_id":r.dept_id,"actual_sales":10.0} for r in production.residual_state.series_metadata.itertuples()])
    full_forecast=full_actual.rename(columns={"actual_sales":"expected_sales"})
    primary=score_batch(full_actual,full_forecast,production.residual_state)
    diagnostic=score_batch(full_actual,full_forecast,production.residual_state,isolation_forest_bundle=production.isolation_forest)
    pd.testing.assert_frame_equal(primary.drop(columns="if_anomaly_score"),diagnostic.drop(columns="if_anomaly_score"))
    assert diagnostic.if_anomaly_score.notna().all()
    path=tmp_path/"artifact.joblib"; save_artifacts(production,path); loaded=load_artifacts(path)
    again=score_batch(full_actual,full_forecast,loaded.residual_state,isolation_forest_bundle=loaded.isolation_forest)
    pd.testing.assert_frame_equal(diagnostic,again)


def test_metadata_consumed_and_summary_contains_no_quality_metrics():
    metadata=json.load(open("models/anomalies/metadata.json")); summary=json.load(open("models/anomalies/training_summary.json"))
    assert metadata["lockbox_status"]=="consumed"
    forbidden={"precision","recall","f1","detection_rate","accuracy","ndcg"}
    assert not forbidden.intersection(summary)
