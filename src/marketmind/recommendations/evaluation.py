"""Explicit single-target full-catalog ranking metrics."""

from __future__ import annotations

import math


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
