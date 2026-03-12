import { test, expect } from '@playwright/test';

test.describe('Dashboard overview', () => {
  test('displays summary metrics and charts', async ({ page }) => {
    const enabled = process.env.RUN_DASHBOARD_TESTS === 'true';
    test.skip(!enabled, 'Set RUN_DASHBOARD_TESTS=true to enable dashboard e2e test');

    await page.goto('http://localhost:5173/login');
    await page.fill('input[autocomplete="username"]', 'admin');
    await page.fill('input[autocomplete="current-password"]', 'admin123');
    await page.click('button[type="submit"]');

    await page.waitForURL('**/');
    await expect(page.getByText('实时监控概览')).toBeVisible();
    await expect(page.locator('[data-test="overview-metric-card"]').first()).toBeVisible();
    await expect(page.locator('[data-test="alert-summary"]')).toBeVisible();
    await expect(page.locator('[data-test="todo-list"]')).toBeVisible();
  });
});
