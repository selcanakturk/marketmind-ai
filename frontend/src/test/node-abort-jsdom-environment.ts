import type { Environment } from 'vitest'
import { builtinEnvironments } from 'vitest/environments'

const environment: Environment = {
  name: 'node-abort-jsdom',
  transformMode: 'web',
  async setup(global, options) {
    // Node 24 fetch enforces that AbortSignal comes from its own realm. Vitest
    // 3's jsdom environment replaces both constructors with jsdom's versions.
    const NodeAbortController = global.AbortController
    const NodeAbortSignal = global.AbortSignal
    const result = await builtinEnvironments.jsdom.setup(global, options)
    global.AbortController = NodeAbortController
    global.AbortSignal = NodeAbortSignal
    return result
  },
}

export default environment
