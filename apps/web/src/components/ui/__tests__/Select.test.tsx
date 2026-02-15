/**
 * Selectコンポーネントのテスト
 * テスト対象: apps/web/src/components/ui/select.tsx
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Select } from '../select';

const mockOptions = [
  { value: 'opt1', label: 'オプション1' },
  { value: 'opt2', label: 'オプション2' },
  { value: 'opt3', label: 'オプション3' },
];

describe('Select', () => {
  it('ラベルが描画される', () => {
    render(<Select label="カテゴリ" options={mockOptions} />);
    expect(screen.getByLabelText('カテゴリ')).toBeInTheDocument();
  });

  it('全オプションが描画される', () => {
    render(<Select label="選択" options={mockOptions} />);
    expect(screen.getByText('オプション1')).toBeInTheDocument();
    expect(screen.getByText('オプション2')).toBeInTheDocument();
    expect(screen.getByText('オプション3')).toBeInTheDocument();
  });

  it('プレースホルダーが描画される', () => {
    render(<Select label="種類" options={mockOptions} placeholder="選択してください" />);
    expect(screen.getByText('選択してください')).toBeInTheDocument();
  });

  it('onChange が発火する', () => {
    const handleChange = jest.fn();
    render(<Select label="テスト" options={mockOptions} onChange={handleChange} />);
    fireEvent.change(screen.getByLabelText('テスト'), { target: { value: 'opt2' } });
    expect(handleChange).toHaveBeenCalled();
  });

  it('エラーメッセージが表示される', () => {
    render(<Select label="必須" options={mockOptions} error="選択必須です" />);
    expect(screen.getByText('選択必須です')).toBeInTheDocument();
  });

  it('ヘルパーテキストが表示される', () => {
    render(<Select label="種類" options={mockOptions} helperText="一つ選択してください" />);
    expect(screen.getByText('一つ選択してください')).toBeInTheDocument();
  });

  it('エラーがある場合ヘルパーテキストは非表示', () => {
    render(
      <Select
        label="テスト"
        options={mockOptions}
        error="エラー"
        helperText="ヘルパー"
      />
    );
    expect(screen.getByText('エラー')).toBeInTheDocument();
    expect(screen.queryByText('ヘルパー')).not.toBeInTheDocument();
  });

  it('disabled状態が適用される', () => {
    render(<Select label="無効" options={mockOptions} disabled />);
    expect(screen.getByLabelText('無効')).toBeDisabled();
  });
});
