/**
 * 認証ストアのテスト
 * テスト対象: apps/web/src/lib/auth.ts
 */

import { act } from '@testing-library/react';

// api-client モック
const mockLogin = jest.fn();
const mockMe = jest.fn();
const mockRegister = jest.fn();

jest.mock('../api-client', () => ({
  __esModule: true,
  default: {
    auth: {
      login: (...args: unknown[]) => mockLogin(...args),
      me: () => mockMe(),
      register: (...args: unknown[]) => mockRegister(...args),
    },
  },
}));

// localStorage モック
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: jest.fn((key: string) => store[key] || null),
    setItem: jest.fn((key: string, value: string) => { store[key] = value; }),
    removeItem: jest.fn((key: string) => { delete store[key]; }),
    clear: jest.fn(() => { store = {}; }),
  };
})();
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

import { useAuth } from '../auth';

describe('useAuth', () => {
  beforeEach(() => {
    // ストアをリセット
    const { logout } = useAuth.getState();
    logout();
    jest.clearAllMocks();
    localStorageMock.clear();
  });

  describe('login', () => {
    it('ログイン成功時にユーザーとisAuthenticatedを設定すること', async () => {
      const mockUser = {
        id: '1',
        email: 'test@example.com',
        name: 'テスト',
        role: 'admin',
        organization_id: null,
        mfa_enabled: false,
      };
      mockLogin.mockResolvedValueOnce({
        access_token: 'token123',
        refresh_token: 'refresh123',
      });
      mockMe.mockResolvedValueOnce(mockUser);

      await act(async () => {
        await useAuth.getState().login('test@example.com', 'password');
      });

      const state = useAuth.getState();
      expect(state.user).toEqual(mockUser);
      expect(state.isAuthenticated).toBe(true);
      expect(state.isLoading).toBe(false);
    });

    it('ログイン成功時にlocalStorageにトークンを保存すること', async () => {
      mockLogin.mockResolvedValueOnce({
        access_token: 'access-abc',
        refresh_token: 'refresh-def',
      });
      mockMe.mockResolvedValueOnce({ id: '1', email: 'a@b.com', name: 'A', role: 'viewer', organization_id: null, mfa_enabled: false });

      await act(async () => {
        await useAuth.getState().login('a@b.com', 'pass');
      });

      expect(localStorageMock.setItem).toHaveBeenCalledWith('access_token', 'access-abc');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('refresh_token', 'refresh-def');
    });

    it('ログイン失敗時にエラーをthrowしisLoadingをリセットすること', async () => {
      mockLogin.mockRejectedValueOnce(new Error('認証失敗'));

      await expect(
        act(async () => {
          await useAuth.getState().login('bad@example.com', 'wrong');
        })
      ).rejects.toThrow('認証失敗');

      expect(useAuth.getState().isLoading).toBe(false);
      expect(useAuth.getState().isAuthenticated).toBe(false);
    });
  });

  describe('logout', () => {
    it('ユーザーとトークンをクリアすること', async () => {
      // まずログイン状態にする
      mockLogin.mockResolvedValueOnce({ access_token: 'a', refresh_token: 'b' });
      mockMe.mockResolvedValueOnce({ id: '1', email: 'a@b.com', name: 'A', role: 'viewer', organization_id: null, mfa_enabled: false });
      await act(async () => {
        await useAuth.getState().login('a@b.com', 'pass');
      });

      act(() => {
        useAuth.getState().logout();
      });

      const state = useAuth.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('refresh_token');
    });
  });

  describe('fetchUser', () => {
    it('トークンなしの場合に状態をクリアすること', async () => {
      localStorageMock.getItem.mockReturnValueOnce(null);

      await act(async () => {
        await useAuth.getState().fetchUser();
      });

      expect(useAuth.getState().user).toBeNull();
      expect(useAuth.getState().isAuthenticated).toBe(false);
    });

    it('トークンありの場合にユーザーを取得すること', async () => {
      const mockUser = { id: '2', email: 'user@test.com', name: 'User', role: 'admin', organization_id: null, mfa_enabled: true };
      localStorageMock.getItem.mockReturnValueOnce('valid-token');
      mockMe.mockResolvedValueOnce(mockUser);

      await act(async () => {
        await useAuth.getState().fetchUser();
      });

      expect(useAuth.getState().user).toEqual(mockUser);
      expect(useAuth.getState().isAuthenticated).toBe(true);
    });
  });

  describe('setUser', () => {
    it('ユーザーを直接設定できること', () => {
      const user = { id: '3', email: 'set@test.com', name: 'Set', role: 'viewer', organization_id: null, mfa_enabled: false };

      act(() => {
        useAuth.getState().setUser(user);
      });

      expect(useAuth.getState().user).toEqual(user);
      expect(useAuth.getState().isAuthenticated).toBe(true);
    });

    it('nullを設定するとisAuthenticatedがfalseになること', () => {
      act(() => {
        useAuth.getState().setUser(null);
      });

      expect(useAuth.getState().isAuthenticated).toBe(false);
    });
  });
});
