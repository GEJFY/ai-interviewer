'use client';

import toast, { Toaster as HotToaster } from 'react-hot-toast';

/**
 * プロジェクトのデザインシステムに合わせたToaster設定
 */
export function Toaster() {
  return (
    <HotToaster
      position="top-right"
      gutter={8}
      toastOptions={{
        duration: 3000,
        className:
          'text-sm font-medium border !bg-white dark:!bg-surface-850 !text-surface-900 dark:!text-surface-50 !border-surface-200 dark:!border-surface-700 !shadow-lg',
        success: {
          duration: 3000,
          iconTheme: {
            primary: '#10b981',
            secondary: '#fff',
          },
        },
        error: {
          duration: 5000,
          iconTheme: {
            primary: '#ef4444',
            secondary: '#fff',
          },
        },
      }}
    />
  );
}

export { toast };
