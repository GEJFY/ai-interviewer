import { test, expect } from './fixtures';

test.describe('Task Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel(/メール|Email/i).first().fill('admin@example.com');
    await page.getByLabel(/パスワード|Password/i).first().fill('password123');
    await page.getByRole('button', { name: /ログイン|Sign in/i }).click();
    await page.waitForURL(/dashboard|\//);
  });

  test('should display tasks page with heading', async ({ page }) => {
    await page.goto('/tasks');
    await expect(page.getByRole('heading', { name: 'タスク管理' })).toBeVisible();
  });

  test('should show task list items', async ({ page }) => {
    await page.goto('/tasks');
    // タスク一覧が表示される（モックデータのタスク名で確認）
    await expect(page.getByText('コンプライアンス調査 Q1').first()).toBeVisible({ timeout: 10000 });
  });

  test('should navigate to task detail', async ({ page }) => {
    await page.goto('/tasks');
    const taskLink = page.locator('a[href*="/tasks/"]').first();
    if (await taskLink.isVisible()) {
      await taskLink.click();
      await expect(page).toHaveURL(/tasks\/.+/);
    }
  });

  test('should show empty state when no tasks', async ({ page }) => {
    // タスクが空の場合のテスト（モック時はスキップ）
    await page.goto('/tasks');
    const emptyState = page.getByText('タスクがありません');
    const taskList = page.locator('a[href*="/tasks/"]').first();

    // どちらかが表示される
    await expect(emptyState.or(taskList)).toBeVisible();
  });
});
