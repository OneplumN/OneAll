import { test, expect } from '@playwright/test';

test.describe('Audit log viewer', () => {
  test('shows audit log table with filters', async ({ page }) => {
    const enabled = process.env.RUN_AUDIT_LOG_TESTS === 'true';
    test.skip(!enabled, 'Set RUN_AUDIT_LOG_TESTS=true to enable audit log e2e test');

    await page.goto('http://localhost:5173/login');
    await page.fill('input[autocomplete="username"]', 'admin');
    await page.fill('input[autocomplete="current-password"]', 'admin123');
    await page.click('button[type="submit"]');

    await page.goto('http://localhost:5173/settings/audit-log');

    await expect(page.getByText('操作与访问日志')).toBeVisible();
    await expect(page.locator('[data-test="audit-log-table"]')).toBeVisible();
    await expect(page.locator('[data-test="audit-log-pagination"]')).toBeVisible();
  });
});
