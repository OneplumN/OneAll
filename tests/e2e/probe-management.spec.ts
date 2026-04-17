import { test, expect } from '@playwright/test';

test.describe('Probe management', () => {
  test('allows creating probe node', async ({ page }) => {
    const enabled = process.env.RUN_PROBE_TESTS === 'true';
    test.skip(!enabled, 'Set RUN_PROBE_TESTS=true to enable probe management e2e test');

    await page.goto('http://localhost:5173/login');

    await page.fill('input[autocomplete="username"]', 'admin');
    await page.fill('input[autocomplete="current-password"]', 'admin123');
    await page.click('button[type="submit"]');

    await page.waitForURL('**/');
    await page.goto('http://localhost:5173/probes');

    await page.click('text=新增探针');
    await page.locator('[data-test="probe-name-input"] input').fill('probe-beijing');
    await page.locator('[data-test="probe-location-input"] input').fill('北京亦庄');
    await page.click('button:has-text("保存")');

    await expect(page.getByText('probe-beijing')).toBeVisible();
  });
});
