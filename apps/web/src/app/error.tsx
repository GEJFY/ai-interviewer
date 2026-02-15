'use client';

import { AlertTriangle } from 'lucide-react';

export default function RootError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[rgb(var(--bg))] p-4">
      <div className="max-w-md w-full text-center">
        <div className="p-4 bg-red-500/10 rounded-2xl w-fit mx-auto mb-6">
          <AlertTriangle className="w-10 h-10 text-red-500" />
        </div>
        <h1 className="text-2xl font-bold text-surface-900 dark:text-surface-50 mb-2">
          エラーが発生しました
        </h1>
        <p className="text-surface-500 dark:text-surface-400 mb-6">
          {error.message || '予期しないエラーが発生しました。'}
        </p>
        <div className="flex gap-3 justify-center">
          <button
            onClick={reset}
            className="px-6 py-2.5 bg-accent-500 hover:bg-accent-600 text-white rounded-lg font-medium transition-colors"
          >
            もう一度試す
          </button>
          <a
            href="/"
            className="px-6 py-2.5 border border-surface-300 dark:border-surface-600 rounded-lg font-medium text-surface-700 dark:text-surface-300 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors"
          >
            ホームに戻る
          </a>
        </div>
      </div>
    </div>
  );
}
