/**
 * APIクライアントのテスト
 * テスト対象: apps/web/src/lib/api-client.ts
 */

// axios.create のモック
const mockInstance = {
  interceptors: {
    request: { use: jest.fn() },
    response: { use: jest.fn() },
  },
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
  request: jest.fn(),
};

jest.mock('axios', () => ({
  __esModule: true,
  default: {
    create: jest.fn(() => mockInstance),
    post: jest.fn(),
  },
}));

describe('api-client', () => {
  beforeEach(() => {
    jest.resetModules();
  });

  it('axiosインスタンスがbaseURL付きで作成されること', () => {
    // resetModules後に再取得してモック呼び出しを確認
    const axios = require('axios').default;
    require('../api-client');
    expect(axios.create).toHaveBeenCalledWith(
      expect.objectContaining({
        baseURL: expect.stringContaining('/api/v1'),
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
        }),
      })
    );
  });

  it('リクエストインターセプターが登録されること', () => {
    const { apiClient } = require('../api-client');
    expect(apiClient.interceptors.request.use).toHaveBeenCalled();
  });

  it('レスポンスインターセプターが登録されること', () => {
    const { apiClient } = require('../api-client');
    expect(apiClient.interceptors.response.use).toHaveBeenCalled();
  });

  describe('api オブジェクト', () => {
    it('auth名前空間が定義されていること', () => {
      const { api } = require('../api-client');
      expect(api.auth).toBeDefined();
      expect(typeof api.auth.login).toBe('function');
      expect(typeof api.auth.register).toBe('function');
      expect(typeof api.auth.me).toBe('function');
      expect(typeof api.auth.changePassword).toBe('function');
      expect(typeof api.auth.listUsers).toBe('function');
      expect(typeof api.auth.adminResetPassword).toBe('function');
      expect(typeof api.auth.ssoAzure).toBe('function');
    });

    it('projects名前空間が定義されていること', () => {
      const { api } = require('../api-client');
      expect(api.projects).toBeDefined();
      expect(typeof api.projects.list).toBe('function');
      expect(typeof api.projects.get).toBe('function');
      expect(typeof api.projects.create).toBe('function');
    });

    it('interviews名前空間が定義されていること', () => {
      const { api } = require('../api-client');
      expect(api.interviews).toBeDefined();
      expect(typeof api.interviews.list).toBe('function');
      expect(typeof api.interviews.start).toBe('function');
      expect(typeof api.interviews.complete).toBe('function');
    });

    it('models名前空間が定義されていること', () => {
      const { api } = require('../api-client');
      expect(api.models).toBeDefined();
      expect(typeof api.models.list).toBe('function');
      expect(typeof api.models.recommended).toBe('function');
      expect(typeof api.models.testConnection).toBe('function');
    });
  });
});
