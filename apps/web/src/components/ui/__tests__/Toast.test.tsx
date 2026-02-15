/**
 * Toastコンポーネントのテスト
 * テスト対象: apps/web/src/components/ui/toast.tsx
 */

import React from 'react';
import { render } from '@testing-library/react';

// react-hot-toast のモック（virtual: true でモジュール解決をスキップ）
const mockToast = Object.assign(jest.fn(), {
  success: jest.fn(),
  error: jest.fn(),
  loading: jest.fn(),
  dismiss: jest.fn(),
});

jest.mock('react-hot-toast', () => ({
  __esModule: true,
  default: mockToast,
  Toaster: (props: any) => <div data-testid="hot-toaster" />,
}), { virtual: true });

// モック後にインポート
import { Toaster, toast } from '../toast';

describe('Toaster', () => {
  it('Toasterコンポーネントが描画される', () => {
    const { container } = render(<Toaster />);
    expect(container.firstChild).toBeInTheDocument();
  });
});

describe('toast', () => {
  it('toast関数がエクスポートされている', () => {
    expect(toast).toBeDefined();
  });

  it('toast.successが関数である', () => {
    expect(typeof toast.success).toBe('function');
  });

  it('toast.errorが関数である', () => {
    expect(typeof toast.error).toBe('function');
  });
});
