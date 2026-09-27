export type ResponseMeta = { module_version: string | null; artifact_version: string | null; generated_at: string; warnings: string[] }
export type ApiResponse<T> = { meta: ResponseMeta; rows: T[] }
export type ErrorDetail = { field: string; message: string }
export type ErrorEnvelope = { error: { code: string; message: string; details: ErrorDetail[] | unknown | null }; request_id: string }
export type ReadyResponse = { status: 'ready' | 'degraded'; modules: Record<ModuleKey, boolean> }
export type ModuleKey = 'forecasting' | 'segmentation' | 'return_risk' | 'recommendations' | 'anomalies' | 'inventory'
export type ModelInfo = { module: ModuleKey; ready: boolean; version: string | null; model_family: string | null; grain: string[] | null; warnings: string[]; status_reason: string | null }
export type ModelsResponse = { models: ModelInfo[] }

export type HistoryRow = { d: string; date: string; store_id: string; dept_id: string; state_id: string; sales: number }
export type CalendarRow = { d: string; date: string; event_name: string; event_type: string; snap_CA: number; snap_TX: number; snap_WI: number }
export type ForecastRequest = { history: HistoryRow[]; future_calendar: CalendarRow[] }
export type ForecastRow = { date: string; store_id: string; dept_id: string; state_id: string; horizon: number; predicted_sales: number }

export type SegmentFeatureRow = { household_id: number; recency_days: number; basket_frequency: number; monetary_value: number; avg_basket_value: number; unique_departments: number; department_spend_hhi: number; discount_share_of_gross: number; coupon_basket_rate: number; private_label_spend_share: number }
export type SegmentationRequest = { snapshot_at: string; feature_rows: SegmentFeatureRow[] }
export type SegmentRow = { household_id: number; snapshot_at: string; segment_code: string; segment_name: string; centroid_distance: number }

export type TransactionRow = { household_id: number; store_id: number | string; basket_id: number; product_id: number; sales_value: number; retail_disc: number; coupon_disc: number; coupon_match_disc: number; transaction_timestamp: string }
export type ProductRow = { product_id: number; department: string; brand?: string | null }
export type ReturnRiskRequest = { transactions: TransactionRow[]; products: ProductRow[]; snapshot_at: string; capacity?: number | null }
export type ReturnRiskRow = { household_id: number; snapshot_date: string; eligibility_status: string; eligibility_reason: string; risk_score: number | null; risk_rank: number | null; risk_percentile: number | null; selected_capacity: number; flagged: boolean }

export type RecommendationRequest = { visitor_id: number; snapshot_timestamp: string; k: number; history_item_ids: number[] }
export type RecommendationRow = { visitor_id: number; snapshot_timestamp: string; rank: number; item_id: number; score: number; recommendation_source: string; seen_before: boolean }
export type RecommendationResponse = ApiResponse<RecommendationRow> & { status: string; fallback_reason: string }

export type ActualSalesRow = { date: string; store_id: string; dept_id: string; actual_sales: number }
export type ExpectedSalesRow = { date: string; store_id: string; dept_id: string; expected_sales: number }
export type CalendarContextRow = { date: string; event_name?: string | null; event_type?: string | null; snap_CA?: number; snap_TX?: number; snap_WI?: number }
export type AnomalyRequest = { actual_sales: ActualSalesRow[]; expected_sales: ExpectedSalesRow[]; calendar_context?: CalendarContextRow[] | null; include_if_diagnostic?: boolean }
export type AnomalyRow = { date: string; store_id: string; dept_id: string; actual_sales: number; expected_sales: number; residual: number; anomaly_score: number | null; direction: string; is_statistical_alert: boolean; daily_review_rank: number | null; is_review_priority: boolean; if_anomaly_score: number | null; event_name: string | null; event_type: string | null; snap_active: number; undefined_score_reason: string | null }

export type InventoryInputRow = { snapshot_date: string; store_id: string; dept_id: string; on_hand_inventory: number; on_order_inventory: number; backorders: number; lead_time_days: number; review_period_days: number; service_level_target: number; minimum_order_quantity?: number | null; case_pack_size?: number | null; maximum_order_quantity?: number | null; uncertainty_method?: string; safety_buffer_days?: number | null; recent_anomaly_context?: string | null }
export type InventoryForecastRow = { forecast_date: string; store_id: string; dept_id: string; predicted_sales: number }
export type InventoryRequest = { inventory_inputs: InventoryInputRow[]; forecasts: InventoryForecastRow[] }
export type InventoryRow = InventoryInputRow & { inventory_position: number; protection_period_days: number; forecast_lead_time_demand: number; forecast_protection_demand: number; expected_daily_demand: number; uncertainty_method: string; safety_buffer_days: number | null; historical_residual_count: number; historical_residual_mad: number; forecast_uncertainty_scale: number; safety_stock: number; target_stock: number; unconstrained_order_quantity: number; pre_max_constrained_quantity: number; recommended_order_quantity: number; replenishment_needed: boolean; days_of_cover: number | null; constraint_warning: string | null; planning_status: string; planning_warning: string }
