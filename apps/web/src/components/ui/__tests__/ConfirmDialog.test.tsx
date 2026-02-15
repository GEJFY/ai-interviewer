/**
 * ConfirmDialogコンポーネントのテスト
 * テスト対象: apps/web/src/components/ui/confirm-dialog.tsx
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ConfirmDialog } from '../confirm-dialog';

describe('ConfirmDialog', () => {
  const defaultProps = {
    isOpen: true,
    onClose: jest.fn(),
    onConfirm: jest.fn(),
    title: '削除の確認',
    message: '本当に削除しますか？',
  };

  beforeEach(() => {
    defaultProps.onClose.mockClear();
    defaultProps.onConfirm.mockClear();
  });

  it('isOpen=falseの場合は何も描画されない', () => {
    render(<ConfirmDialog {...defaultProps} isOpen={false} />);
    expect(screen.queryByText('削除の確認')).not.toBeInTheDocument();
  });

  it('isOpen=trueの場合にタイトルとメッセージが描画される', () => {
    render(<ConfirmDialog {...defaultProps} />);
    expect(screen.getByText('削除の確認')).toBeInTheDocument();
    expect(screen.getByText('本当に削除しますか？')).toBeInTheDocument();
  });

  it('確認ボタンでonConfirmが呼ばれる', () => {
    render(<ConfirmDialog {...defaultProps} confirmLabel="削除" />);
    fireEvent.click(screen.getByRole('button', { name: '削除' }));
    expect(defaultProps.onConfirm).toHaveBeenCalledTimes(1);
  });

  it('キャンセルボタンでonCloseが呼ばれる', () => {
    render(<ConfirmDialog {...defaultProps} />);
    fireEvent.click(screen.getByRole('button', { name: 'キャンセル' }));
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
  });

  it('デフォルトのボタンラベルが表示される', () => {
    render(<ConfirmDialog {...defaultProps} />);
    expect(screen.getByRole('button', { name: '確認' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'キャンセル' })).toBeInTheDocument();
  });

  it('カスタムボタンラベルが表示される', () => {
    render(
      <ConfirmDialog
        {...defaultProps}
        confirmLabel="実行する"
        cancelLabel="やめる"
      />
    );
    expect(screen.getByRole('button', { name: '実行する' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'やめる' })).toBeInTheDocument();
  });

  it('isLoading時にキャンセルボタンが無効化される', () => {
    render(<ConfirmDialog {...defaultProps} isLoading />);
    expect(screen.getByRole('button', { name: 'キャンセル' })).toBeDisabled();
  });

  it('dangerバリアントが適用される', () => {
    const { container } = render(
      <ConfirmDialog {...defaultProps} variant="danger" />
    );
    // danger バリアントはred系アイコン
    expect(container.querySelector('.text-red-500')).toBeInTheDocument();
  });

  it('warningバリアントが適用される', () => {
    const { container } = render(
      <ConfirmDialog {...defaultProps} variant="warning" />
    );
    expect(container.querySelector('.text-amber-500')).toBeInTheDocument();
  });
});
