"""Authoritative frozen configuration for production recommendations."""

from __future__ import annotations

MODEL_VERSION = "retailrocket-item-cf-v1"
SCHEMA_VERSION = "1.0"
NEIGHBOR_COUNT = 50
DEFAULT_K = 20
MAX_K = 1_000
ALLOWED_EVENTS = ("view", "addtocart", "transaction")
REQUIRED_EVENT_COLUMNS = ("timestamp", "visitorid", "itemid", "event")

FROZEN_CONFIGURATION = {
    "representation": "binary visitor-item; repeated pairs collapsed",
    "event_weighting": "none; all event types equal",
    "similarity": "exact sparse cosine",
    "neighbors": NEIGHBOR_COUNT,
    "visitor_score": "sum cosine similarity over distinct known history items",
    "self_similarity": "retained",
    "seen_items": "allowed",
    "ranking_tie_break": "numeric item ID ascending",
    "fallback": "all-event popularity through scoring snapshot",
    "recency_weighting": "none",
    "metadata_features": "none",
    "session_features": "none",
    "latent_factors": "none",
    "reranking": "none",
}

RESEARCH_METRICS = {
    "status": "historical evidence only; not recalculated during productionization",
    "validation": {"ndcg_at_10": 0.191470, "hit_rate_at_10": 0.250773,
                   "hit_rate_at_20": 0.263640, "coverage_at_20": 0.236441},
    "consumed_lockbox": {"instances": 9085, "ndcg_at_10": 0.171158,
                         "hit_rate_at_10": 0.223996, "hit_rate_at_20": 0.235223,
                         "coverage_at_20": 0.242774, "repeat_ndcg_at_10": 0.739078,
                         "novel_ndcg_at_10": 0.005979,
                         "assessment": "STRONG GENERALIZATION"},
}

LOCKBOX_STATUS = "consumed"
LOCKBOX_RESTRICTION = "permanently consumed; never fresh validation, tuning, calibration, selection, or policy evidence"
