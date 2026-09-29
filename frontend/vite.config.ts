import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
  test: { environment: './src/test/node-abort-jsdom-environment.ts', setupFiles: './src/test/setup.ts', css: true }
})
