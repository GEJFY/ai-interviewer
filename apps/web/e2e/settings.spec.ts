import { test, expect } from './fixtures';

test.describe('Settings Page', () => {
  // テスト前にログイン状態にする
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel(/メール|Email/i).first().fill('admin@example.com');
    await page.getByLabel(/パスワード|Password/i).first().fill('password123');
    await page.getByRole('button', { name: /ログイン|Sign in/i }).click();
    await page.waitForURL(/dashboard|\//);
  });

  test('should display settings page', async ({ page }) => {
    await page.goto('/settings');
    await expect(page.getByRole('heading', { name: /設定|Settings/i })).toBeVisible();
  });

  test('should switch between tabs', async ({ page }) => {
    await page.goto('/settings');

    // AIプロバイダータブに切り替え
    await page.getByRole('tab', { name: /AIプロバイダー/i }).or(page.getByText('AIプロバイダー').first()).click();
    await expect(page.getByText('AIプロバイダー設定').first()).toBeVisible();

    // 通知タブに切り替え
    await page.getByRole('tab', { name: /通知/i }).or(page.getByText('通知').first()).click();
    await expect(page.getByText('通知設定').first()).toBeVisible();

    // 外観タブに切り替え
    await page.getByRole('tab', { name: /外観/i }).or(page.getByText('外観').first()).click();
    await expect(page.getByText('外観設定').first()).toBeVisible();
  });

  test('should display AI provider options including Local LLM', async ({ page }) => {
    await page.goto('/settings');
    await page.getByRole('tab', { name: /AIプロバイダー/i }).or(page.getByText('AIプロバイダー').first()).click();

    // 全プロバイダーが表示されること
    await expect(page.getByText('Azure OpenAI').first()).toBeVisible();
    await expect(page.getByText('AWS Bedrock').first()).toBeVisible();
    await expect(page.getByText('GCP Vertex AI').first()).toBeVisible();
    await expect(page.getByText('Local LLM (Ollama)').first()).toBeVisible();
  });

  test('should select Local LLM provider', async ({ page }) => {
    await page.goto('/settings');
    await page.getByRole('tab', { name: /AIプロバイダー/i }).or(page.getByText('AIプロバイダー').first()).click();

    // Local LLMを選択
    await page.getByText('Local LLM (Ollama)').first().click();

    // Ollama接続設定フォームが表示されること
    await expect(page.getByText('Base URL').first()).toBeVisible();
    await expect(page.getByText('Model Name').first()).toBeVisible();
  });

  test('should show model selection guide', async ({ page }) => {
    await page.goto('/settings');
    await page.getByRole('tab', { name: /AIプロバイダー/i }).or(page.getByText('AIプロバイダー').first()).click();

    // モデル選択ガイドが表示されること
    await expect(page.getByText('モデル選択ガイド').first()).toBeVisible();
    await expect(page.getByText('リアルタイム対話').first()).toBeVisible();
    await expect(page.getByText('分析・レポート').first()).toBeVisible();
  });

  test('should trigger connection test', async ({ page }) => {
    await page.goto('/settings');
    await page.getByRole('tab', { name: /AIプロバイダー/i }).or(page.getByText('AIプロバイダー').first()).click();

    // 接続テストボタンをクリック
    await page.getByRole('button', { name: /接続テスト/i }).click();

    // ローディング状態 or 結果が表示されること
    await expect(
      page.locator('[data-testid="connection-result"], .text-green-500, .text-red-500').first()
    ).toBeVisible({ timeout: 10000 });
  });
});
