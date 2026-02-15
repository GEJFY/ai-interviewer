/**
 * EmptyStateコンポーネントのテスト
 * テスト対象: apps/web/src/components/ui/empty-state.tsx
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { FolderKanban, Search } from 'lucide-react';
import { EmptyState } from '../empty-state';

describe('EmptyState', () => {
  it('タイトルと説明が描画される', () => {
    render(
      <EmptyState
        icon={FolderKanban}
        title="データがありません"
        description="新しいデータを追加してください"
      />
    );
    expect(screen.getByText('データがありません')).toBeInTheDocument();
    expect(screen.getByText('新しいデータを追加してください')).toBeInTheDocument();
  });

  it('アイコンが描画される', () => {
    const { container } = render(
      <EmptyState
        icon={FolderKanban}
        title="テスト"
        description="説明"
      />
    );
    expect(container.querySelector('svg')).toBeInTheDocument();
  });

  it('actionボタン（onClick）が描画されクリックできる', () => {
    const handleClick = jest.fn();
    render(
      <EmptyState
        icon={FolderKanban}
        title="空です"
        description="作成しましょう"
        action={{ label: '新規作成', onClick: handleClick }}
      />
    );
    const button = screen.getByRole('button', { name: '新規作成' });
    expect(button).toBeInTheDocument();
    fireEvent.click(button);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('actionリンク（href）が描画される', () => {
    render(
      <EmptyState
        icon={FolderKanban}
        title="空です"
        description="一覧へ"
        action={{ label: '一覧に戻る', href: '/projects' }}
      />
    );
    const link = screen.getByRole('link', { name: '一覧に戻る' });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/projects');
  });

  it('actionなしの場合ボタンが表示されない', () => {
    render(
      <EmptyState
        icon={FolderKanban}
        title="空です"
        description="説明"
      />
    );
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('searchバリアントでスタイルが変わる', () => {
    const { container } = render(
      <EmptyState
        icon={Search}
        title="検索結果なし"
        description="別のキーワードを試してください"
        variant="search"
      />
    );
    // searchバリアントはblue系のスタイル
    expect(container.querySelector('.bg-blue-500\\/10')).toBeInTheDocument();
  });
});
