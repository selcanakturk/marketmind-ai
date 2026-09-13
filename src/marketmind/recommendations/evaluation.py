"""Explicit single-target full-catalog ranking metrics."""

from __future__ import annotations

import math

import pandas as pd


def _rank(recommendations, target, k: int) -> int | None:
    if k <= 0:
        raise ValueError("k must be positive")
    ranked = list(recommendations)[:k]
    if len(ranked) != len(set(ranked)):
        raise ValueError("recommendations must not contain duplicate items")
    return ranked.index(target) + 1 if target in ranked else None


def recall_at_k(recommendations, target, k: int) -> float:
    """Single-target Recall@K: one iff the target occurs in the first K."""

    return float(_rank(recommendations, target, k) is not None)


def hit_rate_at_k(recommendations, target, k: int) -> float:
    """Single-target HitRate@K; numerically identical to per-instance recall."""

    return recall_at_k(recommendations, target, k)


def ndcg_at_k(recommendations, target, k: int) -> float:
    """Single-target binary NDCG@K with ideal DCG equal to one."""

    rank = _rank(recommendations, target, k)
    return 0.0 if rank is None else 1.0 / math.log2(rank + 1)


def mrr_at_k(recommendations, target, k: int) -> float:
    """Truncated reciprocal rank for one relevant target item."""

    rank = _rank(recommendations, target, k)
    return 0.0 if rank is None else 1.0 / rank


def precision_at_k(recommendations, target, k: int) -> float:
    """Single-target Precision@K with a fixed display-list denominator K."""

    return recall_at_k(recommendations, target, k) / k


def instance_metrics(recommendations, target, ks=(5, 10, 20)) -> dict[str, float]:
    """Return explicit metric columns for one single-target instance."""

    result = {}
    for k in ks:
        result[f"hit_rate_at_{k}"] = hit_rate_at_k(recommendations, target, k)
        result[f"recall_at_{k}"] = result[f"hit_rate_at_{k}"]
        result[f"ndcg_at_{k}"] = ndcg_at_k(recommendations, target, k)
        result[f"mrr_at_{k}"] = mrr_at_k(recommendations, target, k)
        result[f"precision_at_{k}"] = precision_at_k(recommendations, target, k)
    return result


def aggregate_metrics(frame: pd.DataFrame) -> dict[str, float]:
    """Macro-average every recognized per-instance metric column."""

    columns = [column for column in frame if "_at_" in column]
    if not columns:
        raise ValueError("no per-instance metric columns found")
    return {column: float(frame[column].mean()) for column in columns}


def catalog_coverage(recommendations, eligible_catalog, k: int) -> tuple[int, float]:
    """Unique first-K recommended items divided by the eligible catalog."""

    catalog = set(eligible_catalog)
    if not catalog:
        raise ValueError("eligible catalog must be nonempty")
    recommended = {item for ranking in recommendations for item in list(ranking)[:k]}
    if not recommended.issubset(catalog):
        raise ValueError("recommendations contain an ineligible item")
    return len(recommended), len(recommended) / len(catalog)
