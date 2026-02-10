import { test, expect } from './fixtures';

test.describe('Authentication Flow', () => {
  test('should display login page', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByRole('heading', { name: /ログイン|Sign in/i })).toBeVisible();
  });

  test('should show validation errors for empty form', async ({ page }) => {
    await page.goto('/login');
    await page.getByRole('button', { name: /ログイン|Sign in/i }).click();
    // バリデーションエラーが表示されること
    await expect(page.locator('.text-red-500, [role="alert"]').first()).toBeVisible();
  });

  test('should redirect to dashboard after login', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel(/メール|Email/i).first().fill('admin@example.com');
    await page.getByLabel(/パスワード|Password/i).first().fill('password123');
    await page.getByRole('button', { name: /ログイン|Sign in/i }).click();

    // ダッシュボードにリダイレクトされること
    await expect(page).toHaveURL(/dashboard|\/$/);
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel(/メール|Email/i).first().fill('invalid@example.com');
    await page.getByLabel(/パスワード|Password/i).first().fill('wrongpassword');
    await page.getByRole('button', { name: /ログイン|Sign in/i }).click();

    // エラーメッセージが表示されること
    await expect(page.locator('.text-red-500, [role="alert"]').first()).toBeVisible();
  });
});
