import { defineConfig, devices } from '@playwright/test'

/**
 * Minimal Playwright config — single happy-path smoke test.
 *
 * Requires Backend (runserver on :8000) + Frontend (vite on :5173) running
 * BEFORE invoking `npx playwright test`. The 6 test users from
 * `python manage.py create_test_users` must exist.
 *
 * To run the smoke test:
 *   1. Backend:    python manage.py runserver
 *   2. Frontend:   npm run dev
 *   3. (separate) npx playwright test
 *
 * Full E2E coverage of every tab is intentionally out of scope for the MVP —
 * the 255 pytest cases cover business logic. This smoke test exists only to
 * prove the React app boots and the JWT login path works end-to-end.
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    actionTimeout: 10_000,
    navigationTimeout: 20_000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
})
