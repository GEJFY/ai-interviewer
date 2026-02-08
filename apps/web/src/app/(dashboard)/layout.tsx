'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  FolderKanban,
  ClipboardList,
  MessageSquare,
  FileText,
  FileBarChart,
  Settings,
  LogOut,
  Search,
  Bell,
} from 'lucide-react';
import { clsx } from 'clsx';

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

  return (
    <div className="min-h-screen bg-secondary-50">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 w-64 bg-white border-r border-secondary-200">
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="h-16 flex items-center px-6 border-b border-secondary-200">
            <Link href="/dashboard" className="text-xl font-bold text-primary-600">
              AI Interview
            </Link>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-4 space-y-1">
            {navigation.map((item) => {
              const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={clsx(
                    'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition',
                    isActive
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-secondary-600 hover:bg-secondary-50 hover:text-secondary-900'
                  )}
                >
                  <item.icon className="w-5 h-5" />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* User menu */}
          <div className="p-4 border-t border-secondary-200">
            <Link
              href="/settings"
              className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-secondary-600 hover:bg-secondary-50 hover:text-secondary-900 transition"
            >
              <Settings className="w-5 h-5" />
              設定
            </Link>
            <button
              onClick={() => {
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                window.location.href = '/login';
              }}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-secondary-600 hover:bg-secondary-50 hover:text-secondary-900 transition"
            >
              <LogOut className="w-5 h-5" />
              ログアウト
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="pl-64">
        {/* Top bar */}
        <header className="h-16 bg-white border-b border-secondary-200 flex items-center justify-between px-8">
          <div className="flex-1">
            {/* Breadcrumb or search could go here */}
          </div>
          <div className="flex items-center gap-4">
            <button className="p-2 text-secondary-500 hover:text-secondary-700 hover:bg-secondary-100 rounded-lg transition">
              <Bell className="w-5 h-5" />
            </button>
          </div>
        </header>

        {/* Page content */}
        <main className="p-8">{children}</main>
      </div>
    </div>
  );
}
