"""Central frozen configuration for the MarketMind segmentation engine."""

MODEL_VERSION = "segmentation-kmeans3-2017-09-v1"
SCHEMA_VERSION = "1.0"
REFERENCE_SNAPSHOT = "2017-09-30 23:59:59"
REFERENCE_ELIGIBLE_HOUSEHOLDS = 2247

ELIGIBILITY_MIN_HISTORY_DAYS = 90
ELIGIBILITY_MIN_BASKETS = 5
ELIGIBILITY_MIN_ACTIVE_SPAN_DAYS = 30

FEATURE_ORDER: tuple[str, ...] = (
    "recency_days",
    "basket_frequency",
    "monetary_value",
    "avg_basket_value",
    "unique_departments",
    "department_spend_hhi",
    "discount_share_of_gross",
    "coupon_basket_rate",
    "private_label_spend_share",
)
LOG_FEATURES: tuple[str, ...] = (
    "recency_days",
    "basket_frequency",
    "monetary_value",
    "avg_basket_value",
)
UNCHANGED_FEATURES: tuple[str, ...] = (
    "unique_departments",
    "department_spend_hhi",
    "discount_share_of_gross",
    "coupon_basket_rate",
    "private_label_spend_share",
)
BOUNDED_RATIO_FEATURES: tuple[str, ...] = (
    "department_spend_hhi",
    "discount_share_of_gross",
    "coupon_basket_rate",
    "private_label_spend_share",
)

KMEANS_PARAMETERS = {
    "n_clusters": 3,
    "init": "k-means++",
    "n_init": 20,
    "max_iter": 300,
    "tol": 0.0001,
    "algorithm": "lloyd",
    "random_state": 42,
}

SEGMENTS = {
    "HIGH_ENGAGEMENT_BROAD": {
        "display_name": "High-Engagement Broad Shoppers",
        "description": "Recent, frequent, high-spend households purchasing across a broad assortment.",
    },
    "PROMOTION_BASKET_BUILDERS": {
        "display_name": "Promotion-Oriented Basket Builders",
        "description": "Moderate-frequency households with larger baskets and stronger observed discount/coupon use.",
    },
    "LOWER_ENGAGEMENT_FOCUSED": {
        "display_name": "Lower-Engagement Focused Shoppers",
        "description": "Less-recent, lower-frequency and lower-spend households with narrower assortments.",
    },
}
SEGMENT_CODES = tuple(SEGMENTS)

REFERENCE_CLUSTER_COUNTS = {0: 293, 1: 1077, 2: 877}
REFERENCE_INTERNAL_METRICS = {
    "silhouette": 0.20312844392672355,
    "davies_bouldin": 1.5647334449404775,
    "calinski_harabasz": 559.6854955211734,
}

ASSIGNMENT_OUTPUT_COLUMNS = (
    "household_id",
    "snapshot_date",
    "eligibility_status",
    "cluster_id",
    "segment_code",
    "segment_name",
    "distance_to_centroid",
)
