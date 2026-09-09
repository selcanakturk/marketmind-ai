"""Lightweight, label-permutation-safe clustering experiment helpers."""

from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.mixture import GaussianMixture


def _validate_matrix(values: pd.DataFrame | np.ndarray) -> np.ndarray:
    matrix = np.asarray(values, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] < 3 or matrix.shape[1] < 1:
        raise ValueError("Expected a 2D clustering matrix with at least 3 rows")
    if not np.isfinite(matrix).all():
        raise ValueError("Clustering matrix must be finite")
    return matrix


def size_summary(labels: np.ndarray) -> dict[str, object]:
    """Return sorted cluster counts and percentages."""

    unique, counts = np.unique(labels, return_counts=True)
    order = np.argsort(unique)
    counts_dict = {int(unique[i]): int(counts[i]) for i in order}
    shares_dict = {
        int(unique[i]): float(counts[i] / counts.sum()) for i in order
    }
    return {"counts": counts_dict, "shares": shares_dict, "min_share": min(shares_dict.values())}


def evaluate_kmeans(
    values: pd.DataFrame | np.ndarray, k: int, *, random_state: int = 42
) -> tuple[KMeans, np.ndarray, dict[str, object]]:
    matrix = _validate_matrix(values)
    model = KMeans(n_clusters=k, n_init=20, random_state=random_state)
    labels = model.fit_predict(matrix)
    distances = np.linalg.norm(matrix - model.cluster_centers_[labels], axis=1)
    metrics = {
        "silhouette": float(silhouette_score(matrix, labels)),
        "davies_bouldin": float(davies_bouldin_score(matrix, labels)),
        "calinski_harabasz": float(calinski_harabasz_score(matrix, labels)),
        "inertia": float(model.inertia_),
        "distance_median": float(np.median(distances)),
        "distance_p95": float(np.quantile(distances, 0.95)),
        **size_summary(labels),
    }
    return model, labels, metrics


def evaluate_gmm(
    values: pd.DataFrame | np.ndarray, k: int, *, random_state: int = 42
) -> tuple[GaussianMixture, np.ndarray, dict[str, object]]:
    matrix = _validate_matrix(values)
    model = GaussianMixture(
        n_components=k,
        covariance_type="full",
        n_init=5,
        reg_covar=1e-6,
        random_state=random_state,
    )
    labels = model.fit_predict(matrix)
    responsibilities = model.predict_proba(matrix)
    max_responsibility = responsibilities.max(axis=1)
    entropy = -(responsibilities * np.log(responsibilities.clip(1e-15))).sum(axis=1)
    metrics = {
        "bic": float(model.bic(matrix)),
        "aic": float(model.aic(matrix)),
        "silhouette": float(silhouette_score(matrix, labels)),
        "max_responsibility_median": float(np.median(max_responsibility)),
        "max_responsibility_p10": float(np.quantile(max_responsibility, 0.10)),
        "low_responsibility_share": float(np.mean(max_responsibility < 0.60)),
        "assignment_entropy_mean": float(entropy.mean()),
        **size_summary(labels),
    }
    return model, labels, metrics


def seed_stability(
    values: pd.DataFrame | np.ndarray,
    *,
    algorithm: str,
    k: int,
    seeds: tuple[int, ...] = tuple(range(10)),
) -> dict[str, float]:
    """Measure all-pairs ARI across deterministic full-data seed refits."""

    matrix = _validate_matrix(values)
    assignments = []
    for seed in seeds:
        if algorithm == "kmeans":
            labels = KMeans(n_clusters=k, n_init=20, random_state=seed).fit_predict(matrix)
        elif algorithm == "gmm":
            labels = GaussianMixture(
                n_components=k,
                covariance_type="full",
                n_init=5,
                reg_covar=1e-6,
                random_state=seed,
            ).fit_predict(matrix)
        else:
            raise ValueError("algorithm must be 'kmeans' or 'gmm'")
        assignments.append(labels)
    agreement = np.array(
        [adjusted_rand_score(assignments[i], assignments[j]) for i, j in combinations(range(len(seeds)), 2)]
    )
    return {
        "ari_mean": float(agreement.mean()),
        "ari_min": float(agreement.min()),
        "ari_max": float(agreement.max()),
    }


def cluster_profile(features: pd.DataFrame, labels: np.ndarray) -> pd.DataFrame:
    """Median original-unit profile with cluster size and share."""

    if len(features) != len(labels):
        raise ValueError("features and labels must contain the same number of rows")
    profiled = features.copy()
    profiled["cluster"] = labels
    medians = profiled.groupby("cluster", observed=True).median(numeric_only=True)
    counts = profiled.groupby("cluster", observed=True).size()
    medians.insert(0, "household_share", counts / len(profiled))
    medians.insert(0, "household_count", counts)
    return medians
