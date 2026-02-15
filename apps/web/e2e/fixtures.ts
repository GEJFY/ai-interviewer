/**
 * Playwright E2E test fixtures with API mocking.
 *
 * CI ではバックエンドが起動していないため、API レスポンスをモックする。
 * ローカル開発時はバックエンドが起動していれば実際の API を使用する。
 */
import { test as base, expect, type Page } from '@playwright/test';

// ---------------------------------------------------------------------------
// Mock data
// ---------------------------------------------------------------------------

const MOCK_USER = {
  id: '01JTEST000000000000000001',
  email: 'admin@example.com',
  name: 'Test Admin',
  role: 'admin',
  organization_id: '01JTEST000000000000000010',
  auth_provider: 'local',
  mfa_enabled: false,
  created_at: '2025-01-01T00:00:00',
  updated_at: '2025-01-01T00:00:00',
};

const MOCK_TOKENS = {
  access_token: 'mock-access-token-for-e2e-testing',
  refresh_token: 'mock-refresh-token-for-e2e-testing',
  token_type: 'bearer',
};

const MOCK_PROJECTS = {
  items: [
    {
      id: '01JTEST000000000000000100',
      name: 'Sample Project',
      description: 'E2E test project',
      client_name: 'Test Client',
      status: 'active',
      start_date: '2025-01-01',
      end_date: '2025-12-31',
      organization_id: '01JTEST000000000000000010',
      created_by: '01JTEST000000000000000001',
      created_at: '2025-01-01T00:00:00',
      updated_at: '2025-01-01T00:00:00',
      task_count: 3,
      completed_task_count: 1,
    },
  ],
  total: 1,
  page: 1,
  page_size: 20,
  pages: 1,
};

const MOCK_TASKS = {
  items: [
    {
      id: '01JTEST000000000000000200',
      name: 'コンプライアンス調査 Q1',
      description: 'E2E test task',
      project_id: '01JTEST000000000000000100',
      use_case_type: 'compliance_survey',
      status: 'in_progress',
      target_count: 5,
      interview_count: 3,
      completed_interview_count: 1,
      deadline: '2026-03-31',
      created_at: '2025-01-15T00:00:00',
      updated_at: '2025-01-15T00:00:00',
    },
    {
      id: '01JTEST000000000000000201',
      name: '内部統制評価 FY2025',
      description: 'J-SOX evaluation task',
      project_id: '01JTEST000000000000000100',
      use_case_type: 'control_evaluation',
      status: 'pending',
      target_count: 10,
      interview_count: 0,
      completed_interview_count: 0,
      deadline: '2026-06-30',
      created_at: '2025-02-01T00:00:00',
      updated_at: '2025-02-01T00:00:00',
    },
  ],
  total: 2,
  page: 1,
  page_size: 20,
  pages: 1,
};

const MOCK_TEMPLATES = {
  items: [
    {
      id: '01JTEST000000000000000300',
      name: 'コンプライアンス意識調査テンプレート',
      description: 'Standard compliance survey template',
      use_case_type: 'compliance_survey',
      is_published: true,
      version: 1,
      question_count: 5,
      created_at: '2025-01-01T00:00:00',
      updated_at: '2025-01-01T00:00:00',
    },
    {
      id: '01JTEST000000000000000301',
      name: 'リスク評価ヒアリングシート',
      description: 'Risk assessment interview template',
      use_case_type: 'risk_assessment',
      is_published: false,
      version: 2,
      question_count: 8,
      created_at: '2025-01-10T00:00:00',
      updated_at: '2025-01-10T00:00:00',
    },
  ],
  total: 2,
  page: 1,
  page_size: 20,
  pages: 1,
};

const MOCK_PROVIDERS = {
  providers: [
    {
      provider: 'azure_openai',
      is_configured: true,
      capabilities: { realtime: true, vision: true, tools: true },
    },
    {
      provider: 'aws_bedrock',
      is_configured: false,
      capabilities: { realtime: true, vision: false, tools: true },
    },
    {
      provider: 'gcp_vertex',
      is_configured: false,
      capabilities: { realtime: true, vision: true, tools: true },
    },
    {
      provider: 'local',
      is_configured: true,
      capabilities: { realtime: true, vision: false, tools: false },
    },
  ],
  active_provider: 'azure_openai',
};

// ---------------------------------------------------------------------------
// API mock setup
// ---------------------------------------------------------------------------

async function setupApiMocks(page: Page) {
  const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

  // Auth: login
  await page.route(`${apiBase}/api/v1/auth/login`, (route) => {
    const body = route.request().postData() || '';
    const isValidLogin =
      body.includes('admin@example.com') && body.includes('password123');

    if (isValidLogin) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_TOKENS),
      });
    }
    return route.fulfill({
      status: 401,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'Incorrect email or password' }),
    });
  });

  // Auth: current user
  await page.route(`${apiBase}/api/v1/auth/me`, (route) => {
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(MOCK_USER),
    });
  });

  // Auth: refresh token
  await page.route(`${apiBase}/api/v1/auth/refresh`, (route) => {
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(MOCK_TOKENS),
    });
  });

  // Projects
  await page.route(
    (url) => url.origin === apiBase && url.pathname.startsWith('/api/v1/projects'),
    (route) => {
      if (route.request().method() === 'GET') {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(MOCK_PROJECTS),
        });
      }
      // POST (create)
      return route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_PROJECTS.items[0]),
      });
    },
  );

  // Models: providers
  await page.route(`${apiBase}/api/v1/models/providers`, (route) => {
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(MOCK_PROVIDERS),
    });
  });

  // Models: test-connection
  await page.route(`${apiBase}/api/v1/models/test-connection`, (route) => {
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        provider: 'azure_openai',
        status: 'success',
        message: '\u63a5\u7d9a\u6210\u529f',
        model_used: 'gpt-5-nano',
      }),
    });
  });

  // Models: list
  await page.route(
    (url) => url.origin === apiBase && url.pathname === '/api/v1/models',
    (route) => {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ models: [], total: 0 }),
      });
    },
  );

  // Models: recommended
  await page.route(`${apiBase}/api/v1/models/recommended`, (route) => {
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        recommendations: {
          realtime_dialogue: 'gpt-5-nano',
          analysis_report: 'gpt-5-nano',
        },
      }),
    });
  });

  // Tasks（URLの関数マッチャーでクエリ文字列を含むリクエストも確実にキャッチ）
  await page.route(
    (url) => url.origin === apiBase && url.pathname.startsWith('/api/v1/tasks'),
    (route) => {
      if (route.request().method() === 'GET') {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(MOCK_TASKS),
        });
      }
      return route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_TASKS.items[0]),
      });
    },
  );

  // Templates
  await page.route(
    (url) => url.origin === apiBase && url.pathname.startsWith('/api/v1/templates'),
    (route) => {
      if (route.request().method() === 'GET') {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(MOCK_TEMPLATES),
        });
      }
      return route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_TEMPLATES.items[0]),
      });
    },
  );

  // Catch-all for other API calls
  await page.route(
    (url) => url.origin === apiBase && url.pathname.startsWith('/api/v1/'),
    (route) => {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({}),
      });
    },
  );
}

// ---------------------------------------------------------------------------
// Custom test fixture
// ---------------------------------------------------------------------------

export const test = base.extend({
  page: async ({ page }, use) => {
    // CI ではバックエンドが無いのでモックを設定
    if (process.env.CI) {
      await setupApiMocks(page);
    }
    await use(page);
  },
});

export { expect };
