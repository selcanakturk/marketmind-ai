"""Frozen production configuration for inventory decision support."""
MAX_FORECAST_HORIZON=28
MAD_MULTIPLIER=1.4826
SERVICE_LEVEL_MIN=0.50
SERVICE_LEVEL_MAX=0.999
PRIMARY_SAFETY_STOCK_METHOD="robust_normal"
OPTIONAL_SAFETY_STOCK_METHOD="user_buffer_days"
PLANNING_GRAIN=("store_id","dept_id")
MODEL_VERSION="inventory-decision-support-v1"
SCHEMA_VERSION="1.0"
CONSTRAINT_ORDER=("minimum_order_quantity","case_pack_ceiling","whole_unit_ceiling","maximum_order_cap")
REQUIRED_INPUT_COLUMNS=("snapshot_date","store_id","dept_id","on_hand_inventory","on_order_inventory","backorders","lead_time_days","review_period_days","service_level_target")
OPTIONAL_INPUT_COLUMNS=("minimum_order_quantity","case_pack_size","maximum_order_quantity","uncertainty_method","safety_buffer_days","recent_anomaly_context")
OUTPUT_COLUMNS=("snapshot_date","store_id","dept_id","on_hand_inventory","on_order_inventory","backorders","inventory_position","lead_time_days","review_period_days","protection_period_days","forecast_lead_time_demand","forecast_protection_demand","expected_daily_demand","uncertainty_method","safety_buffer_days","historical_residual_count","historical_residual_mad","forecast_uncertainty_scale","service_level_target","safety_stock","target_stock","unconstrained_order_quantity","minimum_order_quantity","case_pack_size","pre_max_constrained_quantity","maximum_order_quantity","recommended_order_quantity","replenishment_needed","days_of_cover","constraint_warning","recent_anomaly_context","planning_status","planning_warning")
ROBUST_NORMAL_WARNING="Safety stock uses the frozen robust-normal planning approximation; historical forecast errors showed positive serial dependence, particularly at longer horizons."
ZERO_MAD_WARNING="zero historical forecast-error MAD; statistical safety buffer is zero"
BUFFER_WARNING="user buffer-days mode; service_level_target did not determine safety stock"
