/**
 * cn ユーティリティのテスト
 * テスト対象: apps/web/src/lib/cn.ts
 */

import { cn } from '../cn';

describe('cn', () => {
  it('クラス名をマージすること', () => {
    expect(cn('foo', 'bar')).toBe('foo bar');
  });

  it('条件クラスを処理すること (clsx)', () => {
    expect(cn('base', false && 'hidden', true && 'visible')).toBe('base visible');
  });

  it('Tailwindコンフリクトを解決すること (twMerge)', () => {
    // p-2 と p-4 が競合 → p-4 が優先
    expect(cn('p-2', 'p-4')).toBe('p-4');
  });

  it('空入力で空文字を返すこと', () => {
    expect(cn()).toBe('');
  });

  it('undefined/null値を無視すること', () => {
    expect(cn('foo', undefined, null, 'bar')).toBe('foo bar');
  });
});
