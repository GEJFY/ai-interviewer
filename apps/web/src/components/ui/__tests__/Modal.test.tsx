/**
 * Modalコンポーネントのテスト
 * テスト対象: apps/web/src/components/ui/modal.tsx
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Modal, ModalBody, ModalFooter } from '../modal';

describe('Modal', () => {
  const defaultProps = {
    isOpen: true,
    onClose: jest.fn(),
    title: 'テストモーダル',
    children: <div>モーダル内容</div>,
  };

  beforeEach(() => {
    defaultProps.onClose.mockClear();
  });

  it('isOpen=falseの場合は何も描画されない', () => {
    render(
      <Modal isOpen={false} onClose={defaultProps.onClose} title="非表示">
        <div>非表示内容</div>
      </Modal>
    );
    expect(screen.queryByText('非表示')).not.toBeInTheDocument();
  });

  it('isOpen=trueの場合にタイトルと内容が描画される', () => {
    render(<Modal {...defaultProps} />);
    expect(screen.getByText('テストモーダル')).toBeInTheDocument();
    expect(screen.getByText('モーダル内容')).toBeInTheDocument();
  });

  it('オーバーレイクリックでonCloseが呼ばれる', () => {
    render(<Modal {...defaultProps} />);
    // backdrop-blur-sm を持つオーバーレイをクリック
    const overlay = document.querySelector('.backdrop-blur-sm');
    expect(overlay).not.toBeNull();
    fireEvent.click(overlay!);
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
  });

  it('閉じるボタンでonCloseが呼ばれる', () => {
    render(<Modal {...defaultProps} />);
    // X ボタンは title 横のボタン
    const closeButtons = document.querySelectorAll('button');
    // title があるとき、最初のbuttonがXボタン
    const xButton = Array.from(closeButtons).find(
      (btn) => btn.querySelector('svg') !== null
    );
    expect(xButton).toBeDefined();
    fireEvent.click(xButton!);
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
  });

  it('モーダルコンテンツクリックでonCloseが呼ばれない', () => {
    render(<Modal {...defaultProps} />);
    fireEvent.click(screen.getByText('モーダル内容'));
    expect(defaultProps.onClose).not.toHaveBeenCalled();
  });

  it('titleなしの場合はヘッダーが表示されない', () => {
    render(
      <Modal isOpen={true} onClose={defaultProps.onClose}>
        <div>タイトルなし</div>
      </Modal>
    );
    expect(screen.getByText('タイトルなし')).toBeInTheDocument();
    // タイトルヘッダーがない
    expect(screen.queryByRole('heading')).not.toBeInTheDocument();
  });
});

describe('ModalBody', () => {
  it('子要素が描画される', () => {
    render(<ModalBody>ボディ内容</ModalBody>);
    expect(screen.getByText('ボディ内容')).toBeInTheDocument();
  });

  it('カスタムclassNameが適用される', () => {
    render(<ModalBody className="space-y-4">カスタム</ModalBody>);
    expect(screen.getByText('カスタム').className).toContain('space-y-4');
  });
});

describe('ModalFooter', () => {
  it('子要素が描画される', () => {
    render(<ModalFooter>フッター内容</ModalFooter>);
    expect(screen.getByText('フッター内容')).toBeInTheDocument();
  });

  it('borderとflexスタイルが適用される', () => {
    const { container } = render(<ModalFooter>フッターボタン</ModalFooter>);
    const footer = container.firstChild as HTMLElement;
    expect(footer.className).toContain('border-t');
    expect(footer.className).toContain('flex');
  });
});
