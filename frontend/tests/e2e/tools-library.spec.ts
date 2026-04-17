import { test, expect } from '@playwright/test';

test.describe('Tools library flows', () => {
  test('tools library displays tool list and creation dialog', async ({ page }) => {
    test.skip(true, 'Tool library UI requires running frontend + backend');

    await page.goto('http://localhost:5173/login');
    await page.fill('input[autocomplete="username"]', 'admin');
    await page.fill('input[autocomplete="current-password"]', 'admin123');
    await page.click('button[type="submit"]');

    await page.goto('http://localhost:5173/tools/library');
    await expect(page.getByRole('heading', { name: '工具库' })).toBeVisible();
    await page.click('button:has-text("新增工具")');
    await expect(page.getByRole('dialog', { name: '新建工具' })).toBeVisible();
  });
});
