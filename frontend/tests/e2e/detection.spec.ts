import { test, expect } from '@playwright/test';

test.describe('One-off detection workflow', () => {
  test('submits detection request and views result', async ({ page }) => {
    test.skip(true, 'Detection UI not implemented yet');

    await page.goto('http://localhost:5173/login');
    await page.fill('input[autocomplete="username"]', 'admin');
    await page.fill('input[autocomplete="current-password"]', 'admin123');
    await page.click('button[type="submit"]');

    await page.waitForURL('**/');
    await page.goto('http://localhost:5173/detection');

    await page.fill('[data-test="detection-target-input"] input', 'https://example.com');
    await page.selectOption('[data-test="detection-protocol-select"] select', 'HTTPS');
    await page.click('button:has-text("开始拨测")');

    await expect(page.getByText('拨测已提交')).toBeVisible();
  });
});
