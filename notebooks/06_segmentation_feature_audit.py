"""Phase 2 Step 1 empirical segmentation feature audit.

This is a notebook-style script (``# %%`` cells) so the audit is easy to run in
Jupyter-compatible editors while remaining diffable and executable in CI.
It writes only reviewable figures; it does not persist a modeling matrix.
"""

# %% Imports and authentic data
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyreadr

from marketmind.segmentation.snapshot import build_household_snapshot

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "complete_journey"
FIGURES = ROOT / "reports" / "segmentation" / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

transactions = pyreadr.read_r(str(RAW / "transactions.rds"))[None]
products = pyreadr.read_r(str(RAW / "products.rda"))["products"]

# %% Candidate snapshot eligibility
candidate_rows = []
for snapshot in (
    "2017-08-31 23:59:59",
    "2017-09-30 23:59:59",
    "2017-10-31 23:59:59",
):
    result = build_household_snapshot(
        transactions, products, snapshot_at=snapshot
    )
    candidate_rows.append({"snapshot": snapshot, **vars(result.eligibility)})
candidate_audit = pd.DataFrame(candidate_rows)
print(candidate_audit.to_string(index=False))

# %% Frozen snapshot and descriptive audit
snapshot = build_household_snapshot(
    transactions,
    products,
    snapshot_at="2017-09-30 23:59:59",
)
features = snapshot.features
quantiles = features.describe(
    percentiles=[0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99]
).T
diagnostics = pd.DataFrame(
    {
        "missing_share": features.isna().mean(),
        "zero_share": features.eq(0).mean(),
        "skew": features.skew(),
    }
)
print(quantiles.to_string())
print(diagnostics.to_string())

# %% Distribution panels (visual transforms are display-only)
display_values = features.copy()
for column in (
    "recency_days",
    "basket_frequency",
    "monetary_value",
    "avg_basket_value",
    "active_days",
    "median_days_between_shops",
    "unique_products",
):
    display_values[column] = np.log1p(display_values[column])

columns = list(features.columns)
fig, axes = plt.subplots(5, 3, figsize=(13, 15))
for ax, column in zip(axes.flat, columns):
    ax.hist(display_values[column].dropna(), bins=35, color="#315b7d", alpha=0.9)
    suffix = " (log1p display)" if not display_values[column].equals(features[column]) else ""
    ax.set_title(column.replace("_", " ") + suffix, fontsize=9)
    ax.tick_params(labelsize=7)
fig.suptitle("Complete Journey household feature distributions at 2017-09-30", y=1.0)
fig.tight_layout()
fig.savefig(FIGURES / "candidate_feature_distributions.png", dpi=160, bbox_inches="tight")
plt.close(fig)

# %% Spearman redundancy audit
corr = features.corr(method="spearman")
fig, ax = plt.subplots(figsize=(11, 9))
image = ax.imshow(corr, vmin=-1, vmax=1, cmap="coolwarm")
ax.set_xticks(range(len(corr)), corr.columns, rotation=90, fontsize=7)
ax.set_yticks(range(len(corr)), corr.index, fontsize=7)
fig.colorbar(image, ax=ax, shrink=0.75, label="Spearman correlation")
ax.set_title("Candidate feature redundancy audit")
fig.tight_layout()
fig.savefig(FIGURES / "candidate_feature_spearman.png", dpi=160, bbox_inches="tight")
plt.close(fig)

strong_pairs = []
for i, left in enumerate(corr.columns):
    for right in corr.columns[i + 1 :]:
        value = corr.loc[left, right]
        if abs(value) >= 0.75:
            strong_pairs.append((left, right, value))
print(pd.DataFrame(strong_pairs, columns=["feature_a", "feature_b", "spearman"]).to_string(index=False))
