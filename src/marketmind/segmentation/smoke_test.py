"""Reload and smoke-test the exported segmentation artifact independently."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from marketmind.segmentation.assignment import assign_from_transactions
from marketmind.segmentation.bundle import load_bundle
from marketmind.segmentation.config import (
    REFERENCE_CLUSTER_COUNTS,
    REFERENCE_ELIGIBLE_HOUSEHOLDS,
    REFERENCE_SNAPSHOT,
    SEGMENT_CODES,
)
from marketmind.segmentation.train import load_sources


def smoke_test(model_path: str | Path, data_dir: str | Path) -> dict[str, object]:
    bundle = load_bundle(model_path)
    transactions, products = load_sources(data_dir)
    assignments = assign_from_transactions(
        bundle,
        transactions,
        products,
        snapshot_date=REFERENCE_SNAPSHOT,
    )
    eligible = assignments.query("eligibility_status == 'eligible'")
    ineligible = assignments.query("eligibility_status == 'insufficient_history'")
    counts = {
        int(k): int(v)
        for k, v in eligible["cluster_id"].value_counts().sort_index().items()
    }
    if len(eligible) != REFERENCE_ELIGIBLE_HOUSEHOLDS or counts != REFERENCE_CLUSTER_COUNTS:
        raise AssertionError("reference assignment counts do not reproduce")
    if set(eligible["segment_code"]) != set(SEGMENT_CODES):
        raise AssertionError("semantic mapping did not reproduce")
    if ineligible[["cluster_id", "segment_code", "segment_name", "distance_to_centroid"]].notna().any().any():
        raise AssertionError("insufficient-history households received an assignment")
    distances = eligible["distance_to_centroid"].to_numpy(float)
    if not np.isfinite(distances).all() or (distances < 0).any():
        raise AssertionError("invalid centroid distances")
    return {
        "observed_households": len(assignments),
        "eligible_households": len(eligible),
        "insufficient_history_households": len(ineligible),
        "cluster_counts": counts,
        "semantic_codes": sorted(set(eligible["segment_code"])),
        "distance_median": float(np.median(distances)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=Path("models/segmentation/model.joblib"))
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw/complete_journey"))
    args = parser.parse_args()
    result = smoke_test(args.model, args.data_dir)
    print("Segmentation artifact smoke test passed")
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
