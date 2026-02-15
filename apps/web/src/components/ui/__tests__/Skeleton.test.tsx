/**
 * Skeletonコンポーネントのテスト
 * テスト対象: apps/web/src/components/ui/skeleton.tsx
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { Skeleton, SkeletonCard, SkeletonListItem } from '../skeleton';

describe('Skeleton', () => {
  it('animate-pulseクラスが適用される', () => {
    const { container } = render(<Skeleton />);
    const el = container.firstChild as HTMLElement;
    expect(el.className).toContain('animate-pulse');
  });

  it('カスタムclassNameが適用される', () => {
    const { container } = render(<Skeleton className="h-8 w-1/2" />);
    const el = container.firstChild as HTMLElement;
    expect(el.className).toContain('h-8');
    expect(el.className).toContain('w-1/2');
  });

  it('rounded-lgクラスが適用される', () => {
    const { container } = render(<Skeleton />);
    const el = container.firstChild as HTMLElement;
    expect(el.className).toContain('rounded-lg');
  });
});

describe('SkeletonCard', () => {
  it('カード型スケルトンが描画される', () => {
    const { container } = render(<SkeletonCard />);
    const el = container.firstChild as HTMLElement;
    expect(el.className).toContain('rounded-xl');
    expect(el.className).toContain('border');
  });

  it('animate-pulse要素が含まれる', () => {
    const { container } = render(<SkeletonCard />);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });
});

describe('SkeletonListItem', () => {
  it('デフォルトで1つのアイテムが描画される', () => {
    const { container } = render(<SkeletonListItem />);
    const items = container.querySelectorAll('.animate-pulse');
    expect(items.length).toBe(1);
  });

  it('指定した数のアイテムが描画される', () => {
    const { container } = render(<SkeletonListItem count={5} />);
    const items = container.querySelectorAll('.animate-pulse');
    expect(items.length).toBe(5);
  });

  it('カスタムclassNameが適用される', () => {
    const { container } = render(<SkeletonListItem className="my-skeleton" />);
    const el = container.firstChild as HTMLElement;
    expect(el.className).toContain('my-skeleton');
  });
});
