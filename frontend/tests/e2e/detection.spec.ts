import { test, expect } from '@playwright/test';

test.describe('One-off detection workflow', () => {
  test('opens the one-off domain detection page', async ({ page }) => {
    const enabled = process.env.RUN_ONEOFF_TESTS === 'true';
    test.skip(!enabled, 'Set RUN_ONEOFF_TESTS=true to enable one-off detection e2e test');

    await page.goto('http://localhost:5173/login');
    await page.fill('input[autocomplete="username"]', 'admin');
    await page.fill('input[autocomplete="current-password"]', 'admin123');
    await page.click('button[type="submit"]');

    await page.waitForURL('**/');
    await page.goto('http://localhost:5173/oneoff/domain');

    await expect(page.getByRole('heading', { name: '域名拨测' })).toBeVisible();
    await expect(page.getByText('检测配置')).toBeVisible();
    await expect(page.getByRole('button', { name: '立即检测' })).toBeVisible();
    await expect(page.getByText('检测结果')).toBeVisible();
  });
});
