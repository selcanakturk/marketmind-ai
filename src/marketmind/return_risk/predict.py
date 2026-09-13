"""Notebook-independent inference contract for Customer Return Risk."""

from __future__ import annotations

import numpy as np
import pandas as pd

from marketmind.return_risk.bundle import ReturnRiskModelBundle, load_bundle
from marketmind.return_risk.cohorts import EligibilityRule, household_eligibility
from marketmind.return_risk.features import baseline_features, build_candidate_features


OUTPUT_COLUMNS = (
    "household_id", "snapshot_date", "eligibility_status", "eligibility_reason",
    "risk_score", "risk_rank", "risk_percentile", "selected_capacity", "flagged",
)


def _reason(row: pd.Series, rule: EligibilityRule) -> str:
    reasons = []
    if row.observed_history_days < rule.min_observed_history_days:
        reasons.append("observed_history_below_minimum")
    if row.basket_count < rule.min_baskets:
        reasons.append("basket_count_below_minimum")
    if row.active_span_days < rule.min_active_span_days:
        reasons.append("active_span_below_minimum")
    return "eligible" if not reasons else ";".join(reasons)


def score_return_risk(
    transactions: pd.DataFrame,
    products: pd.DataFrame,
    snapshot_at: str | pd.Timestamp,
    bundle: ReturnRiskModelBundle,
    capacity: float | None = None,
) -> pd.DataFrame:
    """Score eligible households at explicit T and report all households observed by T."""

    bundle.validate()
    snapshot = pd.Timestamp(snapshot_at)
    if pd.isna(snapshot):
        raise ValueError("snapshot_at must be explicit and valid")
    selected_capacity = bundle.default_capacity if capacity is None else float(capacity)
    if not 0 < selected_capacity <= 1:
        raise ValueError("capacity must lie in (0, 1]")

    rule = EligibilityRule(**bundle.eligibility_rule)
    eligibility = household_eligibility(transactions, snapshot, rule)
    result = eligibility.reset_index()[["household_id", "eligible"]].copy()
    result["snapshot_date"] = snapshot
    result["eligibility_status"] = np.where(result["eligible"], "eligible", "ineligible")
    reasons = eligibility.apply(_reason, axis=1, rule=rule)
    result["eligibility_reason"] = result["household_id"].map(reasons)
    result["risk_score"] = np.nan
    result["risk_rank"] = pd.Series(pd.NA, index=result.index, dtype="Int64")
    result["risk_percentile"] = np.nan
    result["selected_capacity"] = selected_capacity
    result["flagged"] = False

    features = baseline_features(build_candidate_features(transactions, products, snapshot, rule))
    if tuple(features.columns) != tuple(bundle.feature_names) or features.index.has_duplicates:
        raise ValueError("inference features violate the frozen schema")
    # Parallel tree aggregation can differ at machine epsilon; canonicalize it
    # before ranking so identical inputs always receive identical ties/ranks.
    scores = np.round(bundle.estimator.predict_proba(features)[:, 1], 12)
    if not np.isfinite(scores).all() or ((scores < 0) | (scores > 1)).any():
        raise ValueError("risk scores must be finite and in [0, 1]")
    keys = features.index.astype(str).to_numpy()
    order = np.lexsort((keys, -scores))
    ranks = np.empty(len(scores), dtype=int)
    ranks[order] = np.arange(1, len(scores) + 1)
    selected = int(np.ceil(selected_capacity * len(scores)))
    flagged = ranks <= selected
    scored = pd.DataFrame({
        "household_id": features.index, "risk_score": scores, "risk_rank": ranks,
        "risk_percentile": (len(scores) - ranks + 1) / len(scores), "flagged": flagged,
    })
    result = result.drop(columns="eligible").merge(scored, on="household_id", how="left", suffixes=("", "_scored"), validate="one_to_one")
    for column in ("risk_score", "risk_rank", "risk_percentile", "flagged"):
        result[column] = result.pop(f"{column}_scored").combine_first(result[column])
    result["risk_rank"] = result["risk_rank"].astype("Int64")
    result["flagged"] = result["flagged"].fillna(False).astype(bool)
    return result.loc[:, OUTPUT_COLUMNS].sort_values("household_id").reset_index(drop=True)


def score_from_artifact(transactions, products, snapshot_at, artifact_path, capacity=None):
    """Load a validated artifact and apply the production inference contract."""

    return score_return_risk(transactions, products, snapshot_at, load_bundle(artifact_path), capacity)
