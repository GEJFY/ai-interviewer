/**
 * Breadcrumbコンポーネントのテスト
 * テスト対象: apps/web/src/components/ui/breadcrumb.tsx
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { Breadcrumb } from '../breadcrumb';

describe('Breadcrumb', () => {
  it('アイテムが描画される', () => {
    render(
      <Breadcrumb
        items={[
          { label: 'ホーム', href: '/' },
          { label: '案件管理', href: '/projects' },
          { label: '案件詳細' },
        ]}
      />
    );
    expect(screen.getByText('ホーム')).toBeInTheDocument();
    expect(screen.getByText('案件管理')).toBeInTheDocument();
    expect(screen.getByText('案件詳細')).toBeInTheDocument();
  });

  it('最後のアイテムはリンクにならない', () => {
    render(
      <Breadcrumb
        items={[
          { label: '一覧', href: '/projects' },
          { label: '詳細' },
        ]}
      />
    );
    // 最後のアイテムはspanで描画（リンクなし）
    const lastItem = screen.getByText('詳細');
    expect(lastItem.tagName).toBe('SPAN');
  });

  it('中間のアイテムはリンクになる', () => {
    render(
      <Breadcrumb
        items={[
          { label: 'ホーム', href: '/' },
          { label: '一覧', href: '/list' },
          { label: '詳細' },
        ]}
      />
    );
    const homeLink = screen.getByText('ホーム');
    expect(homeLink.tagName).toBe('A');
    expect(homeLink).toHaveAttribute('href', '/');

    const listLink = screen.getByText('一覧');
    expect(listLink.tagName).toBe('A');
    expect(listLink).toHaveAttribute('href', '/list');
  });

  it('セパレーターが表示される', () => {
    const { container } = render(
      <Breadcrumb
        items={[
          { label: 'A', href: '/a' },
          { label: 'B', href: '/b' },
          { label: 'C' },
        ]}
      />
    );
    // ChevronRight SVGが2つ（3アイテム - 1）表示される
    const separators = container.querySelectorAll('svg');
    expect(separators.length).toBe(2);
  });

  it('nav要素にaria-labelが設定される', () => {
    render(
      <Breadcrumb items={[{ label: 'テスト' }]} />
    );
    expect(screen.getByLabelText('パンくずリスト')).toBeInTheDocument();
  });

  it('カスタムclassNameが適用される', () => {
    render(
      <Breadcrumb items={[{ label: 'テスト' }]} className="my-breadcrumb" />
    );
    const nav = screen.getByLabelText('パンくずリスト');
    expect(nav.className).toContain('my-breadcrumb');
  });
});
