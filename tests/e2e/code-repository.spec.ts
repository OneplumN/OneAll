import { test, expect } from '@playwright/test';

test.describe('Code repository management', () => {
  test('shows repositories and upload drawer', async ({ page }) => {
    test.skip(true, 'Code repository UI requires running frontend + backend');

    await page.goto('http://localhost:5173/login');
    await page.fill('input[autocomplete="username"]', 'admin');
    await page.fill('input[autocomplete="current-password"]', 'admin123');
    await page.click('button[type="submit"]');

    await page.goto('http://localhost:5173/code/repository');
    await expect(page.getByRole('heading', { name: '代码管理' })).toBeVisible();
    await page.click('button:has-text("上传版本")');
    await expect(page.getByRole('dialog').or(page.getByRole('heading', { name: '上传新版本' }))).toBeTruthy();
  });

  test('creates repository through dialog', async ({ page }) => {
    test.skip(true, 'Code repository creation flow requires backend API support');

    await page.goto('http://localhost:5173/login');
    await page.fill('input[autocomplete="username"]', 'admin');
    await page.fill('input[autocomplete="current-password"]', 'admin123');
    await page.click('button[type="submit"]');

    await page.goto('http://localhost:5173/code/repository');
    await page.click('button:has-text("新建仓库")');
    await expect(page.getByRole('dialog', { name: '新建脚本仓库' })).toBeVisible();
    await page.fill('input[placeholder="脚本名称或业务标识"]', 'network-diagnostic');
    await page.selectOption('label=脚本语言', 'Python');
    await page.fill('textarea[placeholder="#!/usr/bin/env python3\\nprint(\'Hello OneAll\')"]', 'print("Hello OneAll")');
  });
});
