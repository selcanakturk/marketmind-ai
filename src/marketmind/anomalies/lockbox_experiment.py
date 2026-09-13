"""First and only authorized evaluation of the frozen anomaly lockbox."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from marketmind.anomalies.isolation_forest import CONFIGURATIONS
from marketmind.anomalies.isolation_forest_experiment import _run_block
from marketmind.anomalies.policy import fixed_threshold, severity_rank
from marketmind.anomalies.residuals import forecast_residual_block
from marketmind.anomalies.scoring import score_block
from marketmind.anomalies.splits import ANOMALY_LOCKBOX
from marketmind.anomalies.synthetic import engineered_cases

ROBUST_THRESHOLD = 3
REVIEW_CAPACITY = 5
IF_CONFIG = "IF-3"
REFERENCE_BLOCKS = (
    "development_1_scale_seed", "development_2", "development_3",
    "development_4", "development_5", "validation",
)
AUTHENTIC_FILE = "lockbox_robust_scores_authentic.csv"
SYNTHETIC_FILE = "lockbox_synthetic_confirmation.csv"


def build_reference(residuals: pd.DataFrame) -> pd.DataFrame:
    reference = residuals[residuals.block.isin(REFERENCE_BLOCKS)].copy()
    if len(reference) != 11760 or reference.d.str.removeprefix("d_").astype(int).max() > 1913:
        raise ValueError("pre-lockbox OOS reference must contain exactly 11,760 rows through d_1913")
    return reference


def freeze_authentic(data_dir: Path, artifact_dir: Path) -> None:
    if (artifact_dir / SYNTHETIC_FILE).exists():
        raise RuntimeError("synthetic artifact exists before authentic freeze")
    residuals = pd.read_csv(artifact_dir / "oos_residual_blocks.csv", parse_dates=["date"])
    reference = build_reference(residuals)
    lockbox, provenance = forecast_residual_block(data_dir, ANOMALY_LOCKBOX, authorize_final_lockbox=True)
    scored = score_block(lockbox, reference)
    scored["is_statistical_alert"] = fixed_threshold(scored, ROBUST_THRESHOLD)
    scored["daily_review_rank"] = severity_rank(scored)
    scored["is_daily_review_candidate"] = scored.daily_review_rank.le(REVIEW_CAPACITY).fillna(False)
    scored.to_csv(artifact_dir / AUTHENTIC_FILE, index=False)
    state = reference.groupby(["store_id", "dept_id"])["residual"].agg(prior_residual_count="count", prior_residual_median="median").reset_index()
    mad = reference.groupby(["store_id", "dept_id"])["residual"].apply(lambda x: float(np.median(np.abs(x - np.median(x))))).rename("prior_residual_mad").reset_index()
    state = state.merge(mad, on=["store_id", "dept_id"]); state["prior_robust_scale"] = 1.4826 * state.prior_residual_mad
    state.to_csv(artifact_dir / "lockbox_pre_reference_state.csv", index=False)
    (artifact_dir / "lockbox_forecast_provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")


def complete_evaluation(data_dir: Path, artifact_dir: Path) -> None:
    metadata_path = artifact_dir / "lockbox_evaluation_metadata.json"
    if metadata_path.exists() and json.loads(metadata_path.read_text()).get("lockbox_status") == "consumed":
        raise RuntimeError("anomaly lockbox is permanently consumed; post-lockbox updates are prohibited")
    authentic_path = artifact_dir / AUTHENTIC_FILE
    if not authentic_path.exists():
        raise RuntimeError("authentic lockbox scores must be frozen before synthetic or IF analysis")
    scored = pd.read_csv(authentic_path, parse_dates=["date"])
    if len(scored) != 1960 or scored.d.str.removeprefix("d_").astype(int).min() != 1914:
        raise ValueError("authentic lockbox artifact violates the frozen boundary")
    residuals = pd.read_csv(artifact_dir / "oos_residual_blocks.csv", parse_dates=["date"])
    reference = build_reference(residuals)
    calendar = pd.read_csv(data_dir / "calendar.csv")
    robust_synthetic = engineered_cases(scored, ROBUST_THRESHOLD)
    if_result, if_synthetic, resource = _run_block(IF_CONFIG, scored, reference, calendar)
    if not np.allclose(if_synthetic.injected_actual_sales, robust_synthetic.injected_actual_sales):
        raise RuntimeError("robust and IF synthetic protocols diverged")
    if_synthetic["synthetic"] = True
    if_synthetic.to_csv(artifact_dir / SYNTHETIC_FILE, index=False)
    final = scored.copy(); final["if_score"] = if_result.if_score
    columns = ["d", "date", "store_id", "dept_id", "state_id", "actual_sales", "expected_sales", "residual",
               "prior_residual_median", "prior_residual_mad", "prior_robust_scale", "anomaly_score", "direction",
               "is_statistical_alert", "daily_review_rank", "is_daily_review_candidate", "if_score"]
    final.loc[:, columns].to_csv(artifact_dir / "lockbox_anomaly_evaluation.csv", index=False)
    provenance = json.loads((artifact_dir / "lockbox_forecast_provenance.json").read_text())
    metadata = {
        "evaluation_completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "forecast_training_cutoff": "d_1913", "scored_start": "d_1914", "scored_end": "d_1941",
        "forecast_provenance": provenance, "robust_reference_blocks": list(REFERENCE_BLOCKS),
        "robust_reference_row_count": len(reference), "robust_threshold": ROBUST_THRESHOLD,
        "review_capacity": "top 5 absolute robust scores per day", "if_config": IF_CONFIG,
        "if_parameters": CONFIGURATIONS[IF_CONFIG], "if_resource_profile": resource,
        "ordering_guarantees": "authentic robust artifact before synthetic; fixed whole-block scale; score desc then store/dept ties",
        "configuration_mutable": False, "lockbox_status": "consumed",
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("mode", choices=("authentic", "complete"))
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw/m5")); parser.add_argument("--artifact-dir", type=Path, default=Path("reports/anomalies/artifacts")); args = parser.parse_args()
    (freeze_authentic if args.mode == "authentic" else complete_evaluation)(args.data_dir, args.artifact_dir)


if __name__ == "__main__": main()
