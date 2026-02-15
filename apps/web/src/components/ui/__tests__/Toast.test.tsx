/**
 * Toastコンポーネントのテスト
 * テスト対象: apps/web/src/components/ui/toast.tsx
 */

import React from 'react';
import { render } from '@testing-library/react';

// react-hot-toast のモック
// jest.mock はファイル先頭にホイスティングされるため、
// モック定義は factory 内で完結させる必要がある
jest.mock('react-hot-toast', () => {
  const fn = Object.assign(jest.fn(), {
    success: jest.fn(),
    error: jest.fn(),
    loading: jest.fn(),
    dismiss: jest.fn(),
  });
  return {
    __esModule: true,
    default: fn,
    Toaster: (props: any) => <div data-testid="hot-toaster" />,
  };
}, { virtual: true });

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
