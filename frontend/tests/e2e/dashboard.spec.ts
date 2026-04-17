import { test, expect } from '@playwright/test';

test.describe('Dashboard overview', () => {
  test('opens the monitoring overview page', async ({ page }) => {
    const enabled = process.env.RUN_MONITORING_OVERVIEW_TESTS === 'true';
    test.skip(!enabled, 'Set RUN_MONITORING_OVERVIEW_TESTS=true to enable monitoring overview e2e test');

    await page.goto('http://localhost:5173/login');
    await page.fill('input[autocomplete="username"]', 'admin');
    await page.fill('input[autocomplete="current-password"]', 'admin123');
    await page.click('button[type="submit"]');

    await page.waitForURL('**/');
    await page.goto('http://localhost:5173/monitoring/overview');

    await expect(page.getByRole('heading', { name: '拨测可视化' })).toBeVisible();
    await expect(page.getByRole('heading', { name: '拨测蜂窝总览' })).toBeVisible();
    await expect(page.locator('body')).toContainText(/选择系统查看明细|暂无系统拨测数据/);
  });
});
