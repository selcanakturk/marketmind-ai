export const API_BASE_URL = (import.meta.env.VITE_MARKETMIND_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '')
export const STATUS_TIMEOUT_MS = 10_000
export const INFERENCE_TIMEOUT_MS = 60_000
