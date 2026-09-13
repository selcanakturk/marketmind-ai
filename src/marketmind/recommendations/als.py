"""Controlled implicit-ALS recommender with deterministic fallback."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property

import implicit
import numpy as np
import pandas as pd
from scipy import sparse

from marketmind.recommendations.item_cf import build_binary_interactions

ALS_CONFIGS = {
    "ALS-1": {"factors": 32, "regularization": 0.01, "iterations": 15, "alpha": 1.0},
    "ALS-2": {"factors": 64, "regularization": 0.01, "iterations": 15, "alpha": 1.0},
    "ALS-3": {"factors": 64, "regularization": 0.05, "iterations": 20, "alpha": 1.0},
}
RANDOM_SEED = 42


@dataclass
class ALSBundle:
    estimator: implicit.als.AlternatingLeastSquares
    interaction_matrix: sparse.csr_matrix
    visitor_ids: np.ndarray
    item_ids: np.ndarray
    config_name: str

    @cached_property
    def visitor_to_index(self):
        return {int(value): index for index, value in enumerate(self.visitor_ids)}

    @cached_property
    def item_to_index(self):
        return {int(value): index for index, value in enumerate(self.item_ids)}

    def validate(self):
        if self.config_name not in ALS_CONFIGS:
            raise ValueError("unknown ALS configuration")
        if not np.isfinite(self.estimator.user_factors).all() or not np.isfinite(self.estimator.item_factors).all():
            raise ValueError("ALS factors must be finite")
        if self.estimator.user_factors.shape[0] != len(self.visitor_ids):
            raise ValueError("ALS visitor mapping is misaligned")
        if self.estimator.item_factors.shape[0] != len(self.item_ids):
            raise ValueError("ALS item mapping is misaligned")


def fit_als(events: pd.DataFrame, config_name: str) -> ALSBundle:
    """Fit one predeclared implicit ALS configuration on binary pairs."""

    if config_name not in ALS_CONFIGS:
        raise ValueError(f"config_name must be one of {tuple(ALS_CONFIGS)}")
    matrix, visitors, items = build_binary_interactions(events)
    params = ALS_CONFIGS[config_name]
    estimator = implicit.als.AlternatingLeastSquares(
        factors=params["factors"], regularization=params["regularization"],
        iterations=params["iterations"], alpha=params["alpha"],
        random_state=RANDOM_SEED, num_threads=1,
    )
    estimator.fit(matrix, show_progress=False)
    bundle = ALSBundle(estimator, matrix, visitors, items, config_name)
    bundle.validate()
    return bundle


def _stable_pairs(item_indices, scores, item_ids):
    pairs = [(int(item_ids[index]), float(score)) for index, score in zip(item_indices, scores) if np.isfinite(score)]
    return sorted(pairs, key=lambda value: (-value[1], value[0]))


def recommend_als(
    bundle: ALSBundle,
    visitor_id,
    candidate_items,
    popularity_items,
    *,
    k: int = 20,
) -> tuple[list[int], dict[str, float]]:
    """Recommend trained-factor items and fill unknown capacity by popularity."""

    bundle.validate()
    if k <= 0:
        raise ValueError("k must be positive")
    candidate_set = set(int(value) for value in candidate_items)
    user_index = bundle.visitor_to_index.get(int(visitor_id))
    latent_pairs = []
    if user_index is not None:
        indices, scores = bundle.estimator.recommend(
            user_index, bundle.interaction_matrix[user_index], N=k,
            filter_already_liked_items=False, recalculate_user=False,
        )
        latent_pairs = [pair for pair in _stable_pairs(indices, scores, bundle.item_ids) if pair[0] in candidate_set]
    ranking = [item for item, _ in latent_pairs[:k]]
    chosen = set(ranking)
    if len(ranking) < k:
        for item in popularity_items:
            item = int(item)
            if item in candidate_set and item not in chosen:
                ranking.append(item)
                chosen.add(item)
                if len(ranking) == k:
                    break
    if len(ranking) != len(set(ranking)) or not set(ranking).issubset(candidate_set):
        raise ValueError("ALS ranking violates candidate or uniqueness contract")
    return ranking, {
        "received_als_recommendations": float(bool(latent_pairs)),
        "complete_popularity_fallback": float(not latent_pairs),
        "latent_items_in_topk": min(k, len(latent_pairs)),
    }
