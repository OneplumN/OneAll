import { test, expect } from '@playwright/test';

test.describe('System settings', () => {
  test('allows updating global configuration', async ({ page }) => {
    test.skip(true, 'System settings UI pending');

    await page.goto('http://localhost:5173/login');
    await page.fill('input[autocomplete="username"]', 'admin');
    await page.fill('input[autocomplete="current-password"]', 'admin123');
    await page.click('button[type="submit"]');

    await page.waitForURL('**/');
    await page.goto('http://localhost:5173/settings/system');

    await page.fill('[data-test="settings-alert-threshold"] input', '120');
    await page.click('button:has-text("保存设置")');
    await expect(page.getByText('保存成功')).toBeVisible();
  });
});
