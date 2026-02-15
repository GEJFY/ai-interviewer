/**
 * Buttonコンポーネントのテスト
 * テスト対象: apps/web/src/components/ui/button.tsx
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '../button';

describe('Button', () => {
  it('デフォルトのvariantで描画される', () => {
    render(<Button>テスト</Button>);
    const button = screen.getByRole('button', { name: 'テスト' });
    expect(button).toBeInTheDocument();
  });

  it('全variantが描画される', () => {
    const variants = ['primary', 'secondary', 'outline', 'ghost', 'danger', 'accent'] as const;
    variants.forEach((variant) => {
      const { unmount } = render(<Button variant={variant}>{variant}</Button>);
      expect(screen.getByRole('button', { name: variant })).toBeInTheDocument();
      unmount();
    });
  });

  it('全sizeが描画される', () => {
    const sizes = ['sm', 'md', 'lg'] as const;
    sizes.forEach((size) => {
      const { unmount } = render(<Button size={size}>{size}</Button>);
      expect(screen.getByRole('button', { name: size })).toBeInTheDocument();
      unmount();
    });
  });

  it('クリックイベントが発火する', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>クリック</Button>);
    fireEvent.click(screen.getByRole('button', { name: 'クリック' }));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('ローディング中はスピナーが表示され無効化される', () => {
    render(<Button isLoading>保存</Button>);
    const button = screen.getByRole('button', { name: '保存' });
    expect(button).toBeDisabled();
    // Loader2 SVGが表示される
    expect(button.querySelector('.animate-spin')).toBeInTheDocument();
  });

  it('disabled時はクリックが無効化される', () => {
    const handleClick = jest.fn();
    render(<Button disabled onClick={handleClick}>無効</Button>);
    const button = screen.getByRole('button', { name: '無効' });
    expect(button).toBeDisabled();
    fireEvent.click(button);
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('leftIconが描画される', () => {
    render(
      <Button leftIcon={<span data-testid="left-icon">+</span>}>
        追加
      </Button>
    );
    expect(screen.getByTestId('left-icon')).toBeInTheDocument();
  });

  it('rightIconが描画される', () => {
    render(
      <Button rightIcon={<span data-testid="right-icon">→</span>}>
        次へ
      </Button>
    );
    expect(screen.getByTestId('right-icon')).toBeInTheDocument();
  });

  it('isLoading時はleftIconの代わりにスピナーが表示される', () => {
    render(
      <Button isLoading leftIcon={<span data-testid="left-icon">+</span>}>
        追加
      </Button>
    );
    expect(screen.queryByTestId('left-icon')).not.toBeInTheDocument();
  });
});
