import { test, expect } from '@playwright/test';

test.describe('Monitoring request submission', () => {
  test('submits periodic monitoring request', async ({ page }) => {
    test.skip(true, 'Monitoring request UI pending');

    await page.goto('http://localhost:5173/login');
    await page.fill('input[autocomplete="username"]', 'admin');
    await page.fill('input[autocomplete="current-password"]', 'admin123');
    await page.click('button[type="submit"]');

    await page.waitForURL('**/');
    await page.goto('http://localhost:5173/monitoring/request');

    await page.fill('[data-test="monitoring-target"] input', 'https://example.com');
    await page.fill('[data-test="monitoring-system-name"] input', '核心系统');
    await page.selectOption('[data-test="monitoring-frequency"] select', '15');
    await page.click('button:has-text("提交申请")');

    await expect(page.getByText('申请已提交')).toBeVisible();
  });
});
