const configuredBase = import.meta.env.VITE_MARKETMIND_API_BASE_URL?.trim()
if (import.meta.env.PROD && (!configuredBase || /^https?:\/\/(localhost|127\.0\.0\.1)(?::|\/|$)/i.test(configuredBase))) {
  throw new Error('Production requires an explicit non-local VITE_MARKETMIND_API_BASE_URL.')
}
export const API_BASE_URL = (configuredBase || 'http://localhost:8000').replace(/\/$/, '')
export const STATUS_TIMEOUT_MS = 10_000
export const INFERENCE_TIMEOUT_MS = 60_000
