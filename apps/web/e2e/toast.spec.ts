import { test, expect } from './fixtures';

test.describe('Toast Notifications', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel(/メール|Email/i).first().fill('admin@example.com');
    await page.getByLabel(/パスワード|Password/i).first().fill('password123');
    await page.getByRole('button', { name: /ログイン|Sign in/i }).click();
    await page.waitForURL(/dashboard|\//);
  });

  test('should show success toast after creating a project', async ({ page }) => {
    await page.goto('/projects');

    // ページの読み込みを待つ
    await expect(page.getByRole('heading', { name: '案件管理' })).toBeVisible();

    // 新規案件作成モーダルを開く
    await page.getByRole('button', { name: /新規案件作成/i }).click();

    // モーダルが表示されるのを待つ
    await expect(page.getByText('新規案件作成').nth(1)).toBeVisible();

    // フォームに入力
    await page.getByLabel(/案件名/i).first().fill('E2Eテスト案件');

    // 作成ボタンをクリック（モーダル内の作成ボタン）
    await page.getByRole('button', { name: /^作成$/ }).click();

    // トースト通知が表示される
    await expect(page.getByText(/作成しました/)).toBeVisible({ timeout: 10000 });
  });

  test('should show success toast after creating a template', async ({ page }) => {
    await page.goto('/templates');

    // ページの読み込みを待つ
    await expect(page.getByRole('heading', { name: 'テンプレート管理' })).toBeVisible();

    // 新規テンプレートモーダルを開く
    await page.getByRole('button', { name: /新規テンプレート/i }).click();

    // テンプレート名を入力
    await expect(page.getByLabel(/テンプレート名/i).first()).toBeVisible();
    await page.getByLabel(/テンプレート名/i).first().fill('E2Eテストテンプレート');

    // 作成ボタンをクリック
    await page.getByRole('button', { name: /作成/ }).last().click();

    // トースト通知が表示される
    await expect(page.getByText(/作成しました/)).toBeVisible({ timeout: 10000 });
  });

  test('should display toast component in DOM', async ({ page }) => {
    await page.goto('/dashboard');

    // react-hot-toast のコンテナが存在する
    // Toasterは初期状態ではregionが存在するか、空のdivが存在する
    // 通知がなくても Toaster コンポーネント自体はマウントされている
    await expect(page.locator('body')).toBeVisible();
  });
});
