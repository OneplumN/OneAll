import { test, expect } from '@playwright/test';

test.describe('One-off detection with CMDB validation', () => {
  test('shows CMDB warning banner for unknown domain', async ({ page }) => {
    test.skip(true, 'Detection CMDB UI pending');

    await page.goto('http://localhost:5173/login');
    await page.fill('input[autocomplete="username"]', 'admin');
    await page.fill('input[autocomplete="current-password"]', 'admin123');
    await page.click('button[type="submit"]');

    await page.waitForURL('**/');
    await page.goto('http://localhost:5173/detection');

    await page.fill('[data-test="detection-target-input"] input', 'https://unknown.example');
    await expect(page.getByTestId('cmdb-warning-banner')).toBeVisible();
  });
});
