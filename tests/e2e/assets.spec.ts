import { test, expect } from '@playwright/test';

test.describe('资产中心', () => {
  test('展示资产列表并触发同步', async ({ page }) => {
    test.skip(true, '资产中心界面尚未实现');

    await page.goto('http://localhost:5173/login');
    await page.fill('input[autocomplete="username"]', 'admin');
    await page.fill('input[autocomplete="current-password"]', 'admin123');
    await page.click('button[type="submit"]');

    await page.waitForURL('**/');
    await page.goto('http://localhost:5173/assets/domain');

    await page.click('button:has-text("同步资产")');
    await expect(page.getByText('同步任务已触发')).toBeVisible();
  });
});
