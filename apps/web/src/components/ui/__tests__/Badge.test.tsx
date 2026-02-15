/**
 * Badgeコンポーネントのテスト
 * テスト対象: apps/web/src/components/ui/badge.tsx
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { Badge } from '../badge';

describe('Badge', () => {
  it('デフォルトvariantで描画される', () => {
    render(<Badge>デフォルト</Badge>);
    expect(screen.getByText('デフォルト')).toBeInTheDocument();
  });

  it('全variantが描画される', () => {
    const variants = ['default', 'accent', 'success', 'warning', 'danger', 'info'] as const;
    variants.forEach((variant) => {
      const { unmount } = render(<Badge variant={variant}>{variant}</Badge>);
      expect(screen.getByText(variant)).toBeInTheDocument();
      unmount();
    });
  });

  it('successバリアントにemeraldクラスが含まれる', () => {
    render(<Badge variant="success">成功</Badge>);
    expect(screen.getByText('成功').className).toContain('emerald');
  });

  it('dangerバリアントにredクラスが含まれる', () => {
    render(<Badge variant="danger">エラー</Badge>);
    expect(screen.getByText('エラー').className).toContain('red');
  });

  it('smサイズが描画される', () => {
    render(<Badge size="sm">小</Badge>);
    expect(screen.getByText('小').className).toContain('text-xs');
  });

  it('mdサイズが描画される', () => {
    render(<Badge size="md">中</Badge>);
    expect(screen.getByText('中').className).toContain('text-sm');
  });

  it('カスタムclassNameが適用される', () => {
    render(<Badge className="my-badge">カスタム</Badge>);
    expect(screen.getByText('カスタム').className).toContain('my-badge');
  });
});
