/**
 * Inputコンポーネントのテスト
 * テスト対象: apps/web/src/components/ui/input.tsx
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Input } from '../input';

describe('Input', () => {
  it('ラベルが描画される', () => {
    render(<Input label="メールアドレス" />);
    expect(screen.getByLabelText('メールアドレス')).toBeInTheDocument();
  });

  it('ラベルとinputがhtmlForで接続される', () => {
    render(<Input label="ユーザー名" />);
    const input = screen.getByLabelText('ユーザー名');
    expect(input.tagName).toBe('INPUT');
  });

  it('エラーメッセージが表示される', () => {
    render(<Input label="名前" error="必須項目です" />);
    expect(screen.getByText('必須項目です')).toBeInTheDocument();
  });

  it('ヘルパーテキストが表示される', () => {
    render(<Input label="パスワード" helperText="8文字以上入力してください" />);
    expect(screen.getByText('8文字以上入力してください')).toBeInTheDocument();
  });

  it('エラーがある場合ヘルパーテキストは非表示', () => {
    render(
      <Input
        label="テスト"
        error="エラーです"
        helperText="ヘルパー"
      />
    );
    expect(screen.getByText('エラーです')).toBeInTheDocument();
    expect(screen.queryByText('ヘルパー')).not.toBeInTheDocument();
  });

  it('disabled状態が適用される', () => {
    render(<Input label="無効" disabled />);
    expect(screen.getByLabelText('無効')).toBeDisabled();
  });

  it('値の変更が検知される', () => {
    const handleChange = jest.fn();
    render(<Input label="入力" onChange={handleChange} />);
    fireEvent.change(screen.getByLabelText('入力'), { target: { value: 'テスト値' } });
    expect(handleChange).toHaveBeenCalled();
  });

  it('placeholderが表示される', () => {
    render(<Input placeholder="入力してください" />);
    expect(screen.getByPlaceholderText('入力してください')).toBeInTheDocument();
  });
});
