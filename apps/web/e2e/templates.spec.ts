import { test, expect } from './fixtures';

test.describe('Template Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel(/メール|Email/i).first().fill('admin@example.com');
    await page.getByLabel(/パスワード|Password/i).first().fill('password123');
    await page.getByRole('button', { name: /ログイン|Sign in/i }).click();
    await page.waitForURL(/dashboard|\//);
  });

  test('should display templates page with heading', async ({ page }) => {
    await page.goto('/templates');
    await expect(page.getByRole('heading', { name: 'テンプレート管理' })).toBeVisible();
  });

  test('should open create template modal', async ({ page }) => {
    await page.goto('/templates');
    await page.getByRole('button', { name: /新規作成/i }).click();

    // モーダルが表示される
    await expect(page.getByText('テンプレート名').first()).toBeVisible();
  });

  test('should show template list or empty state', async ({ page }) => {
    await page.goto('/templates');
    const emptyState = page.getByText('テンプレートがありません');
    const templateCard = page.locator('a[href*="/templates/"]').first();

    // テンプレート一覧またはエンプティステートのどちらかが表示
    await expect(emptyState.or(templateCard)).toBeVisible();
  });

  test('should navigate to template detail', async ({ page }) => {
    await page.goto('/templates');
    const templateLink = page.locator('a[href*="/templates/"]').first();
    if (await templateLink.isVisible()) {
      await templateLink.click();
      await expect(page).toHaveURL(/templates\/.+/);
    }
  });
});
