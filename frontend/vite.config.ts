/// <reference types="vitest" />
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'node:path'

export default defineConfig(({ command }) => ({
  plugins: [react()],
  // Production build is served by Django + WhiteNoise from STATIC_URL
  // ("/static/"), so built asset references must point there. The dev server
  // (`command === 'serve'`) must stay at "/" so client-side deep links and
  // refreshes resolve locally — otherwise every /cases/:id refresh 404s.
  base: command === 'build' ? '/static/' : '/',
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    host: '127.0.0.1',
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 70,
        statements: 80,
      },
    },
  },
}))
