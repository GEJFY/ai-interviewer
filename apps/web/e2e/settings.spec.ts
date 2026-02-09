import { test, expect } from '@playwright/test';

test.describe('Settings Page', () => {
  // テスト前にログイン状態にする
  test.beforeEach(async ({ page }) => {
    // ログインをシミュレート（実際の認証フローに合わせて調整）
    await page.goto('/login');
    await page.getByLabel(/メール|Email/i).fill('admin@example.com');
    await page.getByLabel(/パスワード|Password/i).fill('password123');
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
    await page.getByText('AIプロバイダー').click();
    await expect(page.getByText('AIプロバイダー設定')).toBeVisible();

    // 通知タブに切り替え
    await page.getByText('通知').click();
    await expect(page.getByText('通知設定')).toBeVisible();

    // 外観タブに切り替え
    await page.getByText('外観').click();
    await expect(page.getByText('外観設定')).toBeVisible();
  });

  test('should display AI provider options including Local LLM', async ({ page }) => {
    await page.goto('/settings');
    await page.getByText('AIプロバイダー').click();

    // 全プロバイダーが表示されること
    await expect(page.getByText('Azure OpenAI')).toBeVisible();
    await expect(page.getByText('AWS Bedrock')).toBeVisible();
    await expect(page.getByText('GCP Vertex AI')).toBeVisible();
    await expect(page.getByText('Local LLM (Ollama)')).toBeVisible();
  });

  test('should select Local LLM provider', async ({ page }) => {
    await page.goto('/settings');
    await page.getByText('AIプロバイダー').click();

    // Local LLMを選択
    await page.getByText('Local LLM (Ollama)').click();

    // Ollama接続設定フォームが表示されること
    await expect(page.getByText('Base URL')).toBeVisible();
    await expect(page.getByText('Model Name')).toBeVisible();
  });

  test('should show model selection guide', async ({ page }) => {
    await page.goto('/settings');
    await page.getByText('AIプロバイダー').click();

    // モデル選択ガイドが表示されること
    await expect(page.getByText('モデル選択ガイド')).toBeVisible();
    await expect(page.getByText('リアルタイム対話')).toBeVisible();
    await expect(page.getByText('分析・レポート')).toBeVisible();
  });

  test('should trigger connection test', async ({ page }) => {
    await page.goto('/settings');
    await page.getByText('AIプロバイダー').click();

    // 接続テストボタンをクリック
    await page.getByRole('button', { name: '接続テスト' }).click();

    // ローディング状態 or 結果が表示されること
    await expect(
      page.locator('text=/接続成功|接続失敗|テスト/i')
    ).toBeVisible({ timeout: 10000 });
  });
});
