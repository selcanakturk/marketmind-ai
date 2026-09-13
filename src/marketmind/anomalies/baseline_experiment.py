"""Run the frozen robust-residual baseline without anomaly-lockbox access."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from marketmind.anomalies.policy import fixed_threshold, severity_rank, top_n_per_day
from marketmind.anomalies.residuals import forecast_residual_block
from marketmind.anomalies.scoring import score_blocks_strict
from marketmind.anomalies.splits import DEVELOPMENT_BLOCKS, VALIDATION_BLOCK
from marketmind.anomalies.synthetic import engineered_cases


def _score_summary(frame: pd.DataFrame) -> dict:
    score = frame.anomaly_score.dropna()
    residual = frame.residual
    return {
        "block": frame.block.iloc[0], "rows": len(frame), "defined_scores": len(score),
        "undefined_rate": float(frame.anomaly_score.isna().mean()), "score_median": float(score.median()),
        "score_iqr": float(score.quantile(.75) - score.quantile(.25)),
        "score_p01": float(score.quantile(.01)), "score_p05": float(score.quantile(.05)),
        "score_p95": float(score.quantile(.95)), "score_p99": float(score.quantile(.99)),
        "max_absolute_score": float(score.abs().max()), "positive_scores": int((score > 0).sum()),
        "negative_scores": int((score < 0).sum()), "mae": float(residual.abs().mean()),
        "mean_residual": float(residual.mean()), "median_residual": float(residual.median()),
    }


def _policy_summary(frame: pd.DataFrame, name: str, mask: pd.Series) -> dict:
    alerts = frame.loc[mask].copy()
    series_counts = alerts.groupby(["store_id", "dept_id"]).size().sort_values(ascending=False)
    date_counts = alerts.groupby("date").size().sort_values(ascending=False)
    total = len(alerts)
    return {
        "block": frame.block.iloc[0], "policy": name, "alerts": total, "alert_rate": total / len(frame),
        "spikes": int((alerts.anomaly_score > 0).sum()), "drops": int((alerts.anomaly_score < 0).sum()),
        "series_with_alerts": int(len(series_counts)), "zero_alert_series": 70 - len(series_counts),
        "max_alerts_one_series": int(series_counts.max()) if total else 0,
        "top5_series_share": float(series_counts.head(5).sum() / total) if total else 0,
        "top10_series_share": float(series_counts.head(10).sum() / total) if total else 0,
        "max_alerts_one_date": int(date_counts.max()) if total else 0,
        "zero_alert_days": 28 - len(date_counts), "alerts_per_day_median": float(date_counts.reindex(frame.date.unique(), fill_value=0).median()),
    }


def _consecutive(frame: pd.DataFrame, mask: pd.Series, policy: str) -> dict:
    alerts = frame.loc[mask, ["store_id", "dept_id", "date"]].sort_values(["store_id", "dept_id", "date"])
    lengths = []
    participating = 0
    for _, group in alerts.groupby(["store_id", "dept_id"]):
        dates = pd.to_datetime(group.date).sort_values()
        run = 1
        for delta in dates.diff().dt.days.iloc[1:]:
            if delta == 1:
                run += 1
            else:
                if run >= 2:
                    lengths.append(run); participating += run
                run = 1
        if run >= 2:
            lengths.append(run); participating += run
    return {"block": frame.block.iloc[0], "policy": policy, "participating_rows": participating,
            "runs": len(lengths), "run_lengths": "|".join(map(str, lengths)), "longest_run": max(lengths, default=0)}


def generate_oos(data_dir: Path, artifact_dir: Path):
    blocks, provenance = [], []
    for block in (*DEVELOPMENT_BLOCKS, VALIDATION_BLOCK):
        residuals, record = forecast_residual_block(data_dir, block)
        blocks.append(residuals); provenance.append(record)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    pd.concat(blocks, ignore_index=True).to_csv(artifact_dir / "oos_residual_blocks.csv", index=False)
    pd.DataFrame(provenance).to_csv(artifact_dir / "forecast_block_provenance.csv", index=False)
    return blocks


def run_development(blocks: list[pd.DataFrame], artifact_dir: Path):
    seed, development, validation = blocks[0], blocks[1:5], blocks[5]
    scored_dev = pd.concat(score_blocks_strict(development, seed), ignore_index=True)
    summaries = pd.DataFrame([_score_summary(frame) for _, frame in scored_dev.groupby("block", sort=False)])
    summaries.to_csv(artifact_dir / "development_score_summary.csv", index=False)
    comparisons, consecutive = [], []
    for _, frame in scored_dev.groupby("block", sort=False):
        for threshold in (3, 4):
            name = f"absolute_score_gte_{threshold}"
            mask = fixed_threshold(frame, threshold)
            comparisons.append(_policy_summary(frame, name, mask)); consecutive.append(_consecutive(frame, mask, name))
        for n in (5, 10):
            comparisons.append(_policy_summary(frame, f"top_{n}_per_day", top_n_per_day(frame, n)))
    pd.DataFrame(comparisons).to_csv(artifact_dir / "development_threshold_comparison.csv", index=False)
    pd.DataFrame(consecutive).to_csv(artifact_dir / "development_consecutive_alerts.csv", index=False)
    synthetic = engineered_cases(scored_dev, 3)
    synthetic["detected_at_4"] = synthetic.score_after.abs() >= 4
    synthetic.to_csv(artifact_dir / "synthetic_development_results.csv", index=False)
    # Persist uninspected validation forecast separately; scoring is forbidden until policy freeze exists.
    validation.to_csv(artifact_dir / "validation_residuals_prepolicy.csv", index=False)
    scored_dev.to_csv(artifact_dir / "development_scores.csv", index=False)


def run_validation(artifact_dir: Path, selected_threshold: int, selected_capacity: int):
    freeze_path = artifact_dir / "development_policy_freeze.json"
    if not freeze_path.exists():
        raise RuntimeError("development policy must be frozen before validation inspection")
    freeze = json.loads(freeze_path.read_text())
    if freeze["selected_threshold"] != selected_threshold or freeze["selected_capacity"] != selected_capacity:
        raise ValueError("arguments do not match frozen development policy")
    all_residuals = pd.read_csv(artifact_dir / "oos_residual_blocks.csv", parse_dates=["date"])
    seed_dev_names = [block.name for block in DEVELOPMENT_BLOCKS]
    prior = all_residuals[all_residuals.block.isin(seed_dev_names)]
    validation = all_residuals[all_residuals.block == VALIDATION_BLOCK.name]
    from marketmind.anomalies.scoring import score_block
    scored = score_block(validation, prior)
    pd.DataFrame([_score_summary(scored)]).to_csv(artifact_dir / "validation_score_summary.csv", index=False)
    rows = []
    for threshold in (3, 4):
        rows.append(_policy_summary(scored, f"absolute_score_gte_{threshold}", fixed_threshold(scored, threshold)))
    for n in (5, 10):
        rows.append(_policy_summary(scored, f"top_{n}_per_day", top_n_per_day(scored, n)))
    pd.DataFrame(rows).to_csv(artifact_dir / "validation_policy_comparison.csv", index=False)
    selected = scored.loc[fixed_threshold(scored, selected_threshold)].copy()
    selected["severity_rank"] = severity_rank(scored).loc[selected.index]
    selected.to_csv(artifact_dir / "validation_alerts_selected.csv", index=False)
    pd.DataFrame([_consecutive(scored, fixed_threshold(scored, selected_threshold), f"absolute_score_gte_{selected_threshold}")]).to_csv(artifact_dir / "validation_consecutive_alerts.csv", index=False)
    synthetic = engineered_cases(scored, selected_threshold)
    synthetic.to_csv(artifact_dir / "synthetic_validation_results.csv", index=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("development", "validation"))
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw/m5"))
    parser.add_argument("--artifact-dir", type=Path, default=Path("reports/anomalies/artifacts"))
    parser.add_argument("--threshold", type=int)
    parser.add_argument("--capacity", type=int)
    args = parser.parse_args()
    if args.mode == "development":
        run_development(generate_oos(args.data_dir, args.artifact_dir), args.artifact_dir)
    else:
        run_validation(args.artifact_dir, args.threshold, args.capacity)


if __name__ == "__main__":
    main()
