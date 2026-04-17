import { test, expect } from '@playwright/test';

test.describe('System settings', () => {
  test('opens the platform settings page', async ({ page }) => {
    const enabled = process.env.RUN_SYSTEM_SETTINGS_TESTS === 'true';
    test.skip(!enabled, 'Set RUN_SYSTEM_SETTINGS_TESTS=true to enable system settings e2e test');

    await page.goto('http://localhost:5173/login');
    await page.fill('input[autocomplete="username"]', 'admin');
    await page.fill('input[autocomplete="current-password"]', 'admin123');
    await page.click('button[type="submit"]');

    await page.waitForURL('**/');
    await page.goto('http://localhost:5173/settings/platform');

    await expect(page.getByRole('heading', { name: '平台配置' })).toBeVisible();
    await expect(page.getByText('基础信息')).toBeVisible();
    await expect(page.locator('body')).toContainText('平台名称');
    await expect(page.getByRole('button', { name: '保存' })).toBeVisible();
  });
});
