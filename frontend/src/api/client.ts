import { API_BASE_URL, INFERENCE_TIMEOUT_MS, STATUS_TIMEOUT_MS } from './config'
import type { AnomalyRequest, AnomalyRow, ApiResponse, ErrorEnvelope, ForecastRequest, ForecastRow, InventoryRequest, InventoryRow, ModelsResponse, ReadyResponse, RecommendationRequest, RecommendationResponse, ReturnRiskRequest, ReturnRiskRow, SegmentationRequest, SegmentRow } from '../types/api'

export class ApiError extends Error {
  constructor(public status: number | null, public code: string, message: string, public details: unknown = null, public requestId = '') { super(message); this.name = 'ApiError' }
}

type RequestOptions = RequestInit & { timeoutMs?: number }
export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const controller = new AbortController()
  const external = options.signal
  const abort = () => controller.abort(external?.reason)
  external?.addEventListener('abort', abort, { once: true })
  if (external?.aborted) abort()
  const timer = window.setTimeout(() => controller.abort(new DOMException('Request timed out', 'TimeoutError')), options.timeoutMs ?? STATUS_TIMEOUT_MS)
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, { ...options, signal: controller.signal, headers: { 'Content-Type': 'application/json', ...options.headers } })
    const requestId = response.headers.get('X-Request-ID') ?? ''
    const contentType = response.headers.get('content-type') ?? ''
    const body: unknown = contentType.includes('application/json') ? await response.json() : null
    if (!response.ok) {
      const envelope = body as Partial<ErrorEnvelope> | null
      throw new ApiError(response.status, envelope?.error?.code ?? `HTTP_${response.status}`, envelope?.error?.message ?? 'The service could not complete the request.', envelope?.error?.details, requestId || envelope?.request_id || '')
    }
    return body as T
  } catch (error) {
    if (error instanceof ApiError) throw error
    if (controller.signal.aborted) throw new ApiError(null, external?.aborted ? 'REQUEST_CANCELLED' : 'REQUEST_TIMEOUT', external?.aborted ? 'Request cancelled.' : 'The service did not respond before the timeout.')
    throw new ApiError(null, 'NETWORK_ERROR', 'Could not reach the MarketMind API.')
  } finally {
    window.clearTimeout(timer); external?.removeEventListener('abort', abort)
  }
}

const post = <T>(path: string, body: unknown, signal?: AbortSignal) => apiRequest<T>(path, { method: 'POST', body: JSON.stringify(body), signal, timeoutMs: INFERENCE_TIMEOUT_MS })
export const api = {
  health: (signal?: AbortSignal) => apiRequest<{ status: string }>('/health', { signal }),
  ready: (signal?: AbortSignal) => apiRequest<ReadyResponse>('/ready', { signal }),
  models: (signal?: AbortSignal) => apiRequest<ModelsResponse>('/api/v1/models', { signal }),
  forecast: (body: ForecastRequest, signal?: AbortSignal) => post<ApiResponse<ForecastRow>>('/api/v1/forecast', body, signal),
  segments: (body: SegmentationRequest, signal?: AbortSignal) => post<ApiResponse<SegmentRow>>('/api/v1/segments', body, signal),
  returnRisk: (body: ReturnRiskRequest, signal?: AbortSignal) => post<ApiResponse<ReturnRiskRow>>('/api/v1/return-risk', body, signal),
  recommendations: (body: RecommendationRequest, signal?: AbortSignal) => post<RecommendationResponse>('/api/v1/recommendations', body, signal),
  anomalies: (body: AnomalyRequest, signal?: AbortSignal) => post<ApiResponse<AnomalyRow>>('/api/v1/anomalies', body, signal),
  inventory: (body: InventoryRequest, signal?: AbortSignal) => post<ApiResponse<InventoryRow>>('/api/v1/inventory/recommend', body, signal),
}
