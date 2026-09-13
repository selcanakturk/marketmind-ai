"""Training-only binary item-item cosine collaborative filtering."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
import time

import numpy as np
import pandas as pd
from scipy import sparse

NEIGHBOR_CONFIGS = (50, 100, 200)


@dataclass
class ItemCFModel:
    """Sparse top-neighbor item cosine graph with stable ID mappings."""

    item_ids: np.ndarray
    visitor_ids: np.ndarray
    interaction_matrix: sparse.csr_matrix
    neighbors: dict[int, tuple[np.ndarray, np.ndarray]]
    max_neighbors: int
    build_seconds: float

    @cached_property
    def item_to_index(self):
        return {int(item): index for index, item in enumerate(self.item_ids)}


def build_binary_interactions(events: pd.DataFrame) -> tuple[sparse.csr_matrix, np.ndarray, np.ndarray]:
    """Collapse repeated events to one binary visitor-item interaction."""

    required = {"visitorid", "itemid"}
    if not required.issubset(events):
        raise ValueError(f"events missing columns: {sorted(required.difference(events))}")
    pairs = events[["visitorid", "itemid"]].drop_duplicates().sort_values(["visitorid", "itemid"])
    visitors = np.sort(pairs.visitorid.unique())
    items = np.sort(pairs.itemid.unique())
    visitor_index = pd.Series(np.arange(len(visitors)), index=visitors)
    item_index = pd.Series(np.arange(len(items)), index=items)
    rows = pairs.visitorid.map(visitor_index).to_numpy()
    columns = pairs.itemid.map(item_index).to_numpy()
    matrix = sparse.csr_matrix((np.ones(len(pairs), dtype=np.float32), (rows, columns)), shape=(len(visitors), len(items)))
    return matrix, visitors, items


def fit_item_cf(events: pd.DataFrame, max_neighbors: int = 200) -> ItemCFModel:
    """Build exact sparse cosine co-occurrence and retain only top neighbors."""

    if max_neighbors not in NEIGHBOR_CONFIGS:
        raise ValueError(f"max_neighbors must be one of {NEIGHBOR_CONFIGS}")
    started = time.perf_counter()
    matrix, visitors, items = build_binary_interactions(events)
    counts = np.asarray(matrix.sum(axis=0)).ravel()
    cooccurrence = (matrix.T @ matrix).tocsr()
    neighbors = {}
    for source in range(len(items)):
        start, end = cooccurrence.indptr[source:source + 2]
        indices = cooccurrence.indices[start:end]
        values = cooccurrence.data[start:end] / np.sqrt(counts[source] * counts[indices])
        order = np.lexsort((items[indices], -values))[:max_neighbors]
        neighbors[source] = (indices[order].astype(np.int32), values[order].astype(np.float32))
    return ItemCFModel(items, visitors, matrix, neighbors, max_neighbors, time.perf_counter() - started)


def recommend(
    model: ItemCFModel,
    history_items,
    popularity_items,
    *,
    neighbors: int,
    k: int = 20,
) -> tuple[list[int], dict[str, float]]:
    """Sum cosine neighbors, then deterministically fill with popularity."""

    if neighbors not in NEIGHBOR_CONFIGS or neighbors > model.max_neighbors:
        raise ValueError("unsupported neighborhood configuration")
    if k <= 0:
        raise ValueError("k must be positive")
    item_to_index = model.item_to_index
    scores: dict[int, float] = {}
    for item in sorted(set(int(value) for value in history_items)):
        source = item_to_index.get(item)
        if source is None:
            continue
        indices, similarities = model.neighbors[source]
        for candidate, similarity in zip(indices[:neighbors], similarities[:neighbors]):
            if similarity > 0:
                candidate_id = int(model.item_ids[candidate])
                scores[candidate_id] = scores.get(candidate_id, 0.0) + float(similarity)
    collaborative = sorted(scores, key=lambda item: (-scores[item], item))
    ranking = collaborative[:k]
    selected = set(ranking)
    if len(ranking) < k:
        for item in popularity_items:
            item = int(item)
            if item in item_to_index and item not in selected:
                ranking.append(item)
                selected.add(item)
                if len(ranking) == k:
                    break
    diagnostics = {
        "collaboratively_scored_candidates": len(scores),
        "collaborative_items_in_topk": min(k, len(collaborative)),
        "complete_popularity_fallback": float(not scores),
    }
    return ranking, diagnostics
