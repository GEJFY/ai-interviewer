import { test, expect } from './fixtures';

test.describe('Project Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel(/メール|Email/i).first().fill('admin@example.com');
    await page.getByLabel(/パスワード|Password/i).first().fill('password123');
    await page.getByRole('button', { name: /ログイン|Sign in/i }).click();
    await page.waitForURL(/dashboard|\//);
  });

  test('should display projects page', async ({ page }) => {
    await page.goto('/projects');
    await expect(page.getByRole('heading', { name: '案件管理' })).toBeVisible();
  });

  test('should open new project modal', async ({ page }) => {
    await page.goto('/projects');
    await page.getByRole('button', { name: /新規案件作成/i }).click();

    // モーダルが表示されること
    await expect(page.getByText('案件名').first()).toBeVisible();
  });

  test('should navigate to project detail', async ({ page }) => {
    await page.goto('/projects');

    // 最初のプロジェクトリンクをクリック（存在すれば）
    const projectLink = page.locator('a[href*="/projects/"]').first();
    if (await projectLink.isVisible()) {
      await projectLink.click();
      await expect(page).toHaveURL(/projects\/.+/);
    }
  });
});
