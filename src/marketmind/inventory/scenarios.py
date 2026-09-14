"""Named verification scenarios; values are explicitly hypothetical, never M5 facts."""

SCENARIO_MATRIX = (
    "sufficient_stock", "mild_replenishment_need", "negative_position_from_backorders",
    "high_service_target", "protection_period_at_28_day_boundary",
    "unsupported_protection_period_over_28_days", "minimum_order_adjustment",
    "case_pack_adjustment", "maximum_order_constraint", "zero_expected_demand",
)
SCENARIO_INPUT_NOTICE = "SCENARIO INPUT — not observed M5 inventory truth"
