import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('should display login page', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByRole('heading', { name: /ログイン|Sign in/i })).toBeVisible();
  });

  test('should show validation errors for empty form', async ({ page }) => {
    await page.goto('/login');
    await page.getByRole('button', { name: /ログイン|Sign in/i }).click();
    // バリデーションエラーが表示されること
    await expect(page.locator('text=/メール|email/i')).toBeVisible();
  });

  test('should redirect to dashboard after login', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel(/メール|Email/i).fill('admin@example.com');
    await page.getByLabel(/パスワード|Password/i).fill('password123');
    await page.getByRole('button', { name: /ログイン|Sign in/i }).click();

    // ダッシュボードにリダイレクトされること
    await expect(page).toHaveURL(/dashboard|\/$/);
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel(/メール|Email/i).fill('invalid@example.com');
    await page.getByLabel(/パスワード|Password/i).fill('wrongpassword');
    await page.getByRole('button', { name: /ログイン|Sign in/i }).click();

    // エラーメッセージが表示されること
    await expect(page.locator('text=/エラー|error|invalid/i')).toBeVisible();
  });
});
