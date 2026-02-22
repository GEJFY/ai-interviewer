/**
 * Tooltipコンポーネントのテスト
 * テスト対象: apps/web/src/components/ui/tooltip.tsx
 */

import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { Tooltip } from '../tooltip';

// タイマーモック
beforeEach(() => {
  jest.useFakeTimers();
});
afterEach(() => {
  jest.useRealTimers();
});

describe('Tooltip', () => {
  it('初期状態ではツールチップが非表示であること', () => {
    render(
      <Tooltip content="ヒントテキスト">
        <span>ホバー対象</span>
      </Tooltip>
    );
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();
    expect(screen.getByText('ホバー対象')).toBeInTheDocument();
  });

  it('マウスオーバーでツールチップが表示されること', () => {
    render(
      <Tooltip content="表示テスト" delay={0}>
        <span>ホバー対象</span>
      </Tooltip>
    );

    fireEvent.mouseEnter(screen.getByText('ホバー対象').parentElement!);
    act(() => { jest.advanceTimersByTime(0); });

    expect(screen.getByRole('tooltip')).toBeInTheDocument();
    expect(screen.getByText('表示テスト')).toBeInTheDocument();
  });

  it('マウスアウトでツールチップが非表示になること', () => {
    render(
      <Tooltip content="消えるテスト" delay={0}>
        <span>ホバー対象</span>
      </Tooltip>
    );

    const wrapper = screen.getByText('ホバー対象').parentElement!;
    fireEvent.mouseEnter(wrapper);
    act(() => { jest.advanceTimersByTime(0); });
    expect(screen.getByRole('tooltip')).toBeInTheDocument();

    fireEvent.mouseLeave(wrapper);
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();
  });

  it('delay後にツールチップが表示されること', () => {
    render(
      <Tooltip content="遅延テスト" delay={500}>
        <span>ホバー対象</span>
      </Tooltip>
    );

    fireEvent.mouseEnter(screen.getByText('ホバー対象').parentElement!);

    // delay前は非表示
    act(() => { jest.advanceTimersByTime(200); });
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();

    // delay後に表示
    act(() => { jest.advanceTimersByTime(300); });
    expect(screen.getByRole('tooltip')).toBeInTheDocument();
  });

  it('position="top"でtop方向のクラスが適用されること', () => {
    render(
      <Tooltip content="上ツールチップ" position="top" delay={0}>
        <span>対象</span>
      </Tooltip>
    );

    fireEvent.mouseEnter(screen.getByText('対象').parentElement!);
    act(() => { jest.advanceTimersByTime(0); });

    const tooltip = screen.getByRole('tooltip');
    expect(tooltip.className).toContain('bottom-full');
  });

  it('position="bottom"でbottom方向のクラスが適用されること', () => {
    render(
      <Tooltip content="下ツールチップ" position="bottom" delay={0}>
        <span>対象</span>
      </Tooltip>
    );

    fireEvent.mouseEnter(screen.getByText('対象').parentElement!);
    act(() => { jest.advanceTimersByTime(0); });

    const tooltip = screen.getByRole('tooltip');
    expect(tooltip.className).toContain('top-full');
  });

  it('position="left"でleft方向のクラスが適用されること', () => {
    render(
      <Tooltip content="左ツールチップ" position="left" delay={0}>
        <span>対象</span>
      </Tooltip>
    );

    fireEvent.mouseEnter(screen.getByText('対象').parentElement!);
    act(() => { jest.advanceTimersByTime(0); });

    const tooltip = screen.getByRole('tooltip');
    expect(tooltip.className).toContain('right-full');
  });

  it('position="right"でright方向のクラスが適用されること', () => {
    render(
      <Tooltip content="右ツールチップ" position="right" delay={0}>
        <span>対象</span>
      </Tooltip>
    );

    fireEvent.mouseEnter(screen.getByText('対象').parentElement!);
    act(() => { jest.advanceTimersByTime(0); });

    const tooltip = screen.getByRole('tooltip');
    expect(tooltip.className).toContain('left-full');
  });

  it('focusイベントでもツールチップが表示されること', () => {
    render(
      <Tooltip content="フォーカステスト" delay={0}>
        <button>ボタン</button>
      </Tooltip>
    );

    fireEvent.focus(screen.getByText('ボタン').parentElement!);
    act(() => { jest.advanceTimersByTime(0); });

    expect(screen.getByRole('tooltip')).toBeInTheDocument();
  });

  it('blurイベントでツールチップが非表示になること', () => {
    render(
      <Tooltip content="ブラーテスト" delay={0}>
        <button>ボタン</button>
      </Tooltip>
    );

    const wrapper = screen.getByText('ボタン').parentElement!;
    fireEvent.focus(wrapper);
    act(() => { jest.advanceTimersByTime(0); });
    expect(screen.getByRole('tooltip')).toBeInTheDocument();

    fireEvent.blur(wrapper);
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();
  });
});
