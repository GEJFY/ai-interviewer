import { test, expect } from './fixtures';

test.describe('Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel(/メール|Email/i).first().fill('admin@example.com');
    await page.getByLabel(/パスワード|Password/i).first().fill('password123');
    await page.getByRole('button', { name: /ログイン|Sign in/i }).click();
    await page.waitForURL(/dashboard|\//);
  });

  test('should navigate to all sidebar sections', async ({ page }) => {
    // ダッシュボード
    await page.goto('/dashboard');
    await expect(page.locator('h1').first()).toBeVisible();

    // 案件管理
    await page.goto('/projects');
    await expect(page.getByRole('heading', { name: '案件管理' })).toBeVisible();

    // タスク管理
    await page.goto('/tasks');
    await expect(page.getByRole('heading', { name: 'タスク管理' })).toBeVisible();

    // テンプレート管理
    await page.goto('/templates');
    await expect(page.getByRole('heading', { name: 'テンプレート管理' })).toBeVisible();

    // レポート
    await page.goto('/reports');
    await expect(page.getByRole('heading', { name: 'レポート' })).toBeVisible();

    // ナレッジ
    await page.goto('/knowledge');
    await expect(page.getByRole('heading', { name: 'ナレッジ検索' })).toBeVisible();

    // 設定
    await page.goto('/settings');
    await expect(page.getByRole('heading', { name: '設定', exact: true }).first()).toBeVisible();
  });

  test('should show sidebar navigation links', async ({ page }) => {
    await page.goto('/dashboard');

    // サイドバーのナビゲーションリンクが表示される（デスクトップ幅）
    await page.setViewportSize({ width: 1280, height: 720 });
    const sidebar = page.locator('aside, nav').first();
    await expect(sidebar).toBeVisible();
  });

  test('should show mobile hamburger menu on narrow viewport', async ({ page }) => {
    await page.goto('/dashboard');

    // モバイル幅に変更
    await page.setViewportSize({ width: 375, height: 667 });

    // ハンバーガーメニューボタンが表示される
    const menuButton = page.locator('button').filter({ has: page.locator('svg') }).first();
    await expect(menuButton).toBeVisible();
  });

  test('should display breadcrumb on detail pages', async ({ page }) => {
    await page.goto('/projects');

    // プロジェクト詳細に遷移
    const projectLink = page.locator('a[href*="/projects/"]').first();
    if (await projectLink.isVisible()) {
      await projectLink.click();
      await expect(page).toHaveURL(/projects\/.+/);

      // パンくずリストが表示される
      const breadcrumb = page.locator('nav[aria-label="パンくずリスト"]');
      await expect(breadcrumb).toBeVisible();
      await expect(breadcrumb.getByText('案件管理')).toBeVisible();
    }
  });
});
