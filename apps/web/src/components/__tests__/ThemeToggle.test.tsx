/**
 * ThemeToggleコンポーネントのテスト
 * テスト対象: apps/web/src/components/theme-toggle.tsx
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';

// next-themes モック
const mockSetTheme = jest.fn();
let mockTheme = 'light';

jest.mock('next-themes', () => ({
  useTheme: () => ({
    theme: mockTheme,
    setTheme: mockSetTheme,
  }),
}));

import { ThemeToggle } from '../theme-toggle';

describe('ThemeToggle', () => {
  beforeEach(() => {
    mockTheme = 'light';
    mockSetTheme.mockClear();
  });

  it('ボタンがレンダリングされること', () => {
    render(<ThemeToggle />);
    const button = screen.getByRole('button', { name: 'テーマ切替' });
    expect(button).toBeInTheDocument();
  });

  it('ライトテーマ時にクリックでdarkに切り替えること', () => {
    mockTheme = 'light';
    render(<ThemeToggle />);
    const button = screen.getByRole('button', { name: 'テーマ切替' });
    fireEvent.click(button);
    expect(mockSetTheme).toHaveBeenCalledWith('dark');
  });

  it('ダークテーマ時にクリックでlightに切り替えること', () => {
    mockTheme = 'dark';
    render(<ThemeToggle />);
    const button = screen.getByRole('button', { name: 'テーマ切替' });
    fireEvent.click(button);
    expect(mockSetTheme).toHaveBeenCalledWith('light');
  });

  it('aria-labelが設定されていること', () => {
    render(<ThemeToggle />);
    const button = screen.getByRole('button', { name: 'テーマ切替' });
    expect(button).toHaveAttribute('aria-label', 'テーマ切替');
  });
});
