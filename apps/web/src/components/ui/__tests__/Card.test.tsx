/**
 * Cardコンポーネントのテスト
 * テスト対象: apps/web/src/components/ui/card.tsx
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { Card, CardHeader, CardContent, CardFooter } from '../card';

describe('Card', () => {
  it('デフォルトvariantで描画される', () => {
    render(<Card data-testid="card">コンテンツ</Card>);
    const card = screen.getByTestId('card');
    expect(card).toBeInTheDocument();
    expect(card).toHaveTextContent('コンテンツ');
  });

  it('glassバリアントが適用される', () => {
    render(<Card variant="glass" data-testid="card">ガラス</Card>);
    const card = screen.getByTestId('card');
    expect(card.className).toContain('glass');
  });

  it('elevatedバリアントが適用される', () => {
    render(<Card variant="elevated" data-testid="card">持ち上げ</Card>);
    const card = screen.getByTestId('card');
    expect(card.className).toContain('shadow-lg');
  });

  it('hover有効時にホバースタイルが適用される', () => {
    render(<Card hover data-testid="card">ホバー</Card>);
    const card = screen.getByTestId('card');
    expect(card.className).toContain('hover:border-accent-500/30');
  });

  it('カスタムclassNameが適用される', () => {
    render(<Card className="custom-class" data-testid="card">カスタム</Card>);
    const card = screen.getByTestId('card');
    expect(card.className).toContain('custom-class');
  });
});

describe('CardHeader', () => {
  it('ヘッダーが描画される', () => {
    render(<CardHeader data-testid="header">ヘッダー</CardHeader>);
    expect(screen.getByTestId('header')).toHaveTextContent('ヘッダー');
  });
});

describe('CardContent', () => {
  it('コンテンツが描画される', () => {
    render(<CardContent data-testid="content">内容</CardContent>);
    expect(screen.getByTestId('content')).toHaveTextContent('内容');
  });
});

describe('CardFooter', () => {
  it('フッターが描画される', () => {
    render(<CardFooter data-testid="footer">フッター</CardFooter>);
    const footer = screen.getByTestId('footer');
    expect(footer).toHaveTextContent('フッター');
    expect(footer.className).toContain('border-t');
  });
});
