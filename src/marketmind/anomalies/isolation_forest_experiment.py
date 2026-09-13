"""Orchestrate the one controlled Isolation Forest challenger."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from marketmind.anomalies.isolation_forest import (
    CONFIGURATIONS, FEATURE_COLUMNS, anomaly_score, build_features, fit_isolation_forest,
)
from marketmind.anomalies.policy import fixed_threshold, top_n_per_day
from marketmind.anomalies.scoring import score_block
from marketmind.anomalies.synthetic import engineered_cases


DEVELOPMENT_NAMES = ("development_2", "development_3", "development_4", "development_5")
PRIOR_ORDER = ("development_1_scale_seed", *DEVELOPMENT_NAMES)


def prior_corpus(residuals: pd.DataFrame, block_name: str) -> pd.DataFrame:
    """Return only complete OOS blocks strictly preceding the requested block."""
    allowed = (*DEVELOPMENT_NAMES, "validation")
    if block_name not in allowed:
        raise ValueError("IF runner block is unknown or lockbox-inaccessible")
    index = allowed.index(block_name)
    prior_names = PRIOR_ORDER[: index + 1]
    prior = residuals[residuals.block.isin(prior_names)].copy()
    if (prior.block == block_name).any() or (prior.d.str.removeprefix("d_").astype(int) >= residuals.loc[residuals.block == block_name, "d"].str.removeprefix("d_").astype(int).min()).any():
        raise ValueError("IF training corpus must precede the scored block")
    return prior


def _load_inputs(artifact_dir: Path, calendar_path: Path):
    residuals = pd.read_csv(artifact_dir / "oos_residual_blocks.csv", parse_dates=["date"])
    if residuals.d.str.removeprefix("d_").astype(int).max() > 1913:
        raise ValueError("Isolation Forest runner cannot access anomaly-lockbox rows")
    calendar = pd.read_csv(calendar_path)
    return residuals, calendar


def _top5_indices(frame: pd.DataFrame, column: str) -> set[int]:
    work = frame.copy()
    work["anomaly_score"] = work[column]
    return set(work.index[top_n_per_day(work, 5)])


def _synthetic_features(cases: pd.DataFrame, calendar: pd.DataFrame) -> pd.DataFrame:
    frame = cases.rename(columns={"injected_actual_sales": "actual_sales", "score_after": "anomaly_score"}).copy()
    frame["residual"] = frame.actual_sales - frame.expected_sales
    if not np.allclose(frame.anomaly_score, (frame.residual - frame.prior_residual_median) / frame.prior_robust_scale):
        raise ValueError("synthetic robust feature was not recomputed correctly")
    if "state_id" not in frame:
        frame["state_id"] = frame.store_id.str.split("_").str[0]
    return build_features(frame, calendar)


def _run_block(config_name, block, prior, calendar):
    training_features = build_features(prior, calendar, training_corpus=True)
    model, fit_seconds, model_bytes = fit_isolation_forest(training_features, config_name)
    train_score = anomaly_score(model, training_features)
    features = build_features(block, calendar)
    score_started = time.perf_counter()
    score = anomaly_score(model, features)
    score_seconds = time.perf_counter() - score_started
    result = block.copy(); result["if_score"] = score
    result["if_train_p95"] = np.quantile(train_score, .95); result["if_train_p98"] = np.quantile(train_score, .98)
    result["robust_threshold_alert"] = fixed_threshold(result, 3)
    result["robust_top5"] = result.index.isin(_top5_indices(result, "anomaly_score"))
    result["if_top5"] = result.index.isin(_top5_indices(result, "if_score"))
    synthetic = engineered_cases(block, 3)
    synthetic_score = anomaly_score(model, _synthetic_features(synthetic, calendar))
    synthetic["config"] = config_name; synthetic["if_score_after"] = synthetic_score
    original_scores = result[["block", "store_id", "dept_id", "date", "if_score"]]
    synthetic = synthetic.merge(original_scores, on=["block", "store_id", "dept_id", "date"], how="left", validate="many_to_one")
    synthetic["if_score_before"] = synthetic.pop("if_score")
    synthetic["if_score_increase"] = synthetic.if_score_after - synthetic.if_score_before
    synthetic["enters_training_top5pct"] = synthetic.if_score_after >= np.quantile(train_score, .95)
    synthetic["enters_training_top2pct"] = synthetic.if_score_after >= np.quantile(train_score, .98)
    return result, synthetic, {"fit_seconds": fit_seconds, "score_seconds": score_seconds,
        "model_bytes": model_bytes, "training_rows": len(prior),
        "training_feature_bytes": int(training_features.memory_usage(index=True, deep=True).sum())}


def run_development(artifact_dir: Path, calendar_path: Path):
    residuals, calendar = _load_inputs(artifact_dir, calendar_path)
    scores, synthetics, summaries, overlaps = [], [], [], []
    for config_name in CONFIGURATIONS:
        for index, block_name in enumerate(DEVELOPMENT_NAMES, start=1):
            prior = prior_corpus(residuals, block_name)
            raw = residuals[residuals.block == block_name].copy()
            block = score_block(raw, prior)
            result, synthetic, resource = _run_block(config_name, block, prior, calendar)
            result["config"] = config_name; scores.append(result); synthetics.append(synthetic)
            top = result[result.if_top5]
            overlap = int((result.if_top5 & result.robust_top5).sum())
            summaries.append({"config": config_name, "block": block_name, **resource,
                "score_median": result.if_score.median(), "score_iqr": result.if_score.quantile(.75)-result.if_score.quantile(.25),
                "score_p95": result.if_score.quantile(.95), "score_p98": result.if_score.quantile(.98),
                "score_p99": result.if_score.quantile(.99), "score_max": result.if_score.max(),
                "top5_series": top[["store_id","dept_id"]].drop_duplicates().shape[0],
                "top5_top5series_share": top.groupby(["store_id","dept_id"]).size().nlargest(5).sum()/len(top)})
            overlaps.append({"config": config_name, "block": block_name, "if_top5_rows": len(top),
                "robust_top5_overlap": overlap, "overlap_rate": overlap/len(top),
                "robust_threshold_overlap": int((result.if_top5 & result.robust_threshold_alert).sum()),
                "if_top5_spikes": int((top.anomaly_score>0).sum()), "if_top5_drops": int((top.anomaly_score<0).sum())})
    artifact_dir.mkdir(parents=True, exist_ok=True)
    pd.concat(scores, ignore_index=True).to_csv(artifact_dir/"if_development_scores.csv",index=False)
    pd.concat(synthetics, ignore_index=True).to_csv(artifact_dir/"if_development_synthetic.csv",index=False)
    pd.DataFrame(summaries).to_csv(artifact_dir/"if_config_results.csv",index=False)
    pd.DataFrame(overlaps).to_csv(artifact_dir/"if_overlap_analysis.csv",index=False)


def run_validation(artifact_dir: Path, calendar_path: Path):
    selection_path = artifact_dir / "if_selected_config.json"
    if not selection_path.exists():
        raise RuntimeError("IF configuration must be frozen before validation")
    selection = json.loads(selection_path.read_text()); config = selection["selected_config"]
    residuals, calendar = _load_inputs(artifact_dir, calendar_path)
    prior = prior_corpus(residuals, "validation")
    block = score_block(residuals[residuals.block == "validation"].copy(), prior)
    result, synthetic, resource = _run_block(config, block, prior, calendar)
    result["config"] = config; result.to_csv(artifact_dir/"if_validation_scores.csv",index=False)
    synthetic.to_csv(artifact_dir/"if_validation_synthetic.csv",index=False)
    pd.DataFrame([{**resource,"config":config,"rows":len(result),"score_median":result.if_score.median(),
        "score_iqr":result.if_score.quantile(.75)-result.if_score.quantile(.25),"score_p95":result.if_score.quantile(.95),
        "score_p98":result.if_score.quantile(.98),"score_p99":result.if_score.quantile(.99),"score_max":result.if_score.max()}]).to_csv(artifact_dir/"if_validation_summary.csv",index=False)
    pd.DataFrame([{"if_top5_rows":int(result.if_top5.sum()),"robust_top5_overlap":int((result.if_top5&result.robust_top5).sum()),
        "robust_top5_overlap_rate":float((result.if_top5&result.robust_top5).sum()/result.if_top5.sum()),
        "robust_threshold_overlap":int((result.if_top5&result.robust_threshold_alert).sum()),
        "robust_threshold_total":int(result.robust_threshold_alert.sum()),
        "if_top5_series":int(result.loc[result.if_top5,["store_id","dept_id"]].drop_duplicates().shape[0])}]).to_csv(artifact_dir/"if_validation_overlap.csv",index=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("mode",choices=("development","validation"))
    parser.add_argument("--artifact-dir",type=Path,default=Path("reports/anomalies/artifacts")); parser.add_argument("--calendar",type=Path,default=Path("data/raw/m5/calendar.csv")); args=parser.parse_args()
    (run_development if args.mode=="development" else run_validation)(args.artifact_dir,args.calendar)


if __name__ == "__main__": main()
