'use client';

import { AlertTriangle, RotateCcw, LayoutDashboard } from 'lucide-react';
import Link from 'next/link';

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex items-center justify-center min-h-[60vh] p-4">
      <div className="max-w-md w-full text-center">
        <div className="p-4 bg-red-500/10 rounded-2xl w-fit mx-auto mb-6">
          <AlertTriangle className="w-10 h-10 text-red-500" />
        </div>
        <h2 className="text-xl font-bold text-surface-900 dark:text-surface-50 mb-2">
          表示中にエラーが発生しました
        </h2>
        <p className="text-sm text-surface-500 dark:text-surface-400 mb-6">
          {error.message || 'ページの読み込み中にエラーが発生しました。'}
        </p>
        <div className="flex gap-3 justify-center">
          <button
            onClick={reset}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-accent-500 hover:bg-accent-600 text-white rounded-lg font-medium transition-colors text-sm"
          >
            <RotateCcw className="w-4 h-4" />
            もう一度試す
          </button>
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 px-5 py-2.5 border border-surface-300 dark:border-surface-600 rounded-lg font-medium text-surface-700 dark:text-surface-300 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors text-sm"
          >
            <LayoutDashboard className="w-4 h-4" />
            ダッシュボードに戻る
          </Link>
        </div>
      </div>
    </div>
  );
}
