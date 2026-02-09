'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import {
  LayoutDashboard,
  FolderKanban,
  ClipboardList,
  FileText,
  FileBarChart,
  Search,
  Settings,
  LogOut,
  Bell,
  PanelLeftClose,
  PanelLeft,
} from 'lucide-react';
import { cn } from '@/lib/cn';
import { ThemeToggle } from '@/components/theme-toggle';
import { LanguageSelector } from '@/components/LanguageSelector';

const navigation = [
  { name: 'ダッシュボード', href: '/dashboard', icon: LayoutDashboard },
  { name: '案件管理', href: '/projects', icon: FolderKanban },
  { name: 'タスク管理', href: '/tasks', icon: ClipboardList },
  { name: 'テンプレート', href: '/templates', icon: FileText },
  { name: 'レポート', href: '/reports', icon: FileBarChart },
  { name: 'ナレッジ', href: '/knowledge', icon: Search },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="min-h-screen bg-[rgb(var(--bg))]">
      {/* Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-30 flex flex-col border-r border-surface-200 dark:border-surface-800 bg-white dark:bg-surface-950 transition-all duration-300',
          collapsed ? 'w-16' : 'w-64'
        )}
      >
        {/* ロゴ */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-surface-200 dark:border-surface-800">
          {!collapsed && (
            <Link href="/dashboard" className="text-lg font-bold text-surface-900 dark:text-surface-50 truncate">
              AI Interview<span className="text-accent-500">.</span>
            </Link>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1.5 rounded-lg text-surface-400 hover:text-surface-600 dark:hover:text-surface-300 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors"
          >
            {collapsed ? <PanelLeft className="w-5 h-5" /> : <PanelLeftClose className="w-5 h-5" />}
          </button>
        </div>

        {/* ナビゲーション */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto scrollbar-thin">
          {navigation.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  'group relative flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-surface-100 dark:bg-surface-800 text-surface-900 dark:text-surface-50'
                    : 'text-surface-500 hover:bg-surface-50 dark:hover:bg-surface-900 hover:text-surface-700 dark:hover:text-surface-300'
                )}
                title={collapsed ? item.name : undefined}
              >
                {/* アクティブインジケーター */}
                {isActive && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-accent-500 rounded-r" />
                )}
                <item.icon className={cn('w-5 h-5 flex-shrink-0', isActive && 'text-accent-500')} />
                {!collapsed && <span>{item.name}</span>}
              </Link>
            );
          })}
        </nav>

        {/* フッター */}
        <div className="p-3 border-t border-surface-200 dark:border-surface-800 space-y-1">
          {!collapsed && (
            <div className="flex items-center justify-between px-3 py-1 mb-2">
              <ThemeToggle />
              <LanguageSelector compact />
            </div>
          )}
          <Link
            href="/settings"
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-surface-500 hover:bg-surface-50 dark:hover:bg-surface-900 hover:text-surface-700 dark:hover:text-surface-300 transition-colors"
            title={collapsed ? '設定' : undefined}
          >
            <Settings className="w-5 h-5 flex-shrink-0" />
            {!collapsed && <span>設定</span>}
          </Link>
          <button
            onClick={() => {
              localStorage.removeItem('access_token');
              localStorage.removeItem('refresh_token');
              window.location.href = '/login';
            }}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-surface-500 hover:bg-surface-50 dark:hover:bg-surface-900 hover:text-surface-700 dark:hover:text-surface-300 transition-colors"
            title={collapsed ? 'ログアウト' : undefined}
          >
            <LogOut className="w-5 h-5 flex-shrink-0" />
            {!collapsed && <span>ログアウト</span>}
          </button>
        </div>
      </aside>

      {/* メインコンテンツ */}
      <div className={cn('transition-all duration-300', collapsed ? 'pl-16' : 'pl-64')}>
        {/* トップバー */}
        <header className="sticky top-0 z-20 h-16 glass-strong flex items-center justify-between px-8">
          <div className="flex-1" />
          <div className="flex items-center gap-2">
            <button className="p-2 text-surface-400 hover:text-surface-600 dark:hover:text-surface-300 hover:bg-surface-100 dark:hover:bg-surface-800 rounded-lg transition-colors relative">
              <Bell className="w-5 h-5" />
            </button>
          </div>
        </header>

        {/* ページコンテンツ */}
        <main className="p-8">{children}</main>
      </div>
    </div>
  );
}
