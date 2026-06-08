import { test, expect } from '@playwright/test'

/**
 * Smoke test — proves the React app + backend JWT flow + Beranda + case list
 * all wire together. Doesn't simulate the full clinical workflow (that's
 * covered by 255 pytest cases on the backend).
 *
 * Preconditions:
 *   - Backend running at http://localhost:8000
 *   - Frontend running at http://localhost:5173
 *   - `python manage.py create_test_users` has been run
 */

const HTA_EMAIL = 'hta@test.local'
const PASSWORD = 'TestPass123!'

test.describe('DeciBridge smoke', () => {
  test('HTA Analyst can log in, see dashboard, navigate to Kasus', async ({ page }) => {
    // 1. Login page renders in Indonesian.
    await page.goto('/')
    await expect(page).toHaveTitle(/DeciBridge/i)

    // 2. Fill login form.
    await page.getByLabel(/email/i).fill(HTA_EMAIL)
    await page.getByLabel(/sandi|password/i).fill(PASSWORD)
    await page.getByRole('button', { name: /masuk|login/i }).click()

    // 3. Land on Beranda (dashboard) with the user's name visible.
    await expect(page.getByText(/Selamat datang/i)).toBeVisible({ timeout: 15_000 })

    // 4. Stat boxes (5 case statuses) are visible.
    await expect(page.getByText(/Draft/).first()).toBeVisible()
    await expect(page.getByText(/Dalam Tinjauan/).first()).toBeVisible()

    // 5. Click "Kasus" in left nav.
    await page.getByRole('link', { name: /^Kasus$/ }).click()

    // 6. Daftar Kasus page loads.
    await expect(page.getByRole('heading', { name: /Daftar Kasus/i })).toBeVisible({
      timeout: 10_000,
    })

    // 7. Top-right version chip shows v1.0.0.
    await expect(page.getByText(/^v1\.0\.0$/)).toBeVisible()
  })
})
