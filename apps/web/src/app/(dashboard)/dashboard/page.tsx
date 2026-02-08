'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import {
  FolderKanban,
  ClipboardList,
  MessageSquare,
  FileText,
  ArrowRight,
  TrendingUp,
  Clock,
  CheckCircle2,
} from 'lucide-react';
import api from '@/lib/api-client';

export default function DashboardPage() {
  const { data: projects } = useQuery({
    queryKey: ['projects', { pageSize: 5 }],
    queryFn: () => api.projects.list({ pageSize: 5 }),
  });

  const { data: tasks } = useQuery({
    queryKey: ['tasks', { pageSize: 5 }],
    queryFn: () => api.tasks.list({ pageSize: 5 }),
  });

  return (
    <div className="space-y-8">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-secondary-900">ダッシュボード</h1>
        <p className="text-secondary-600 mt-1">
          インタビュー業務の概要を確認できます
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl p-6 border border-secondary-100 shadow-sm">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-primary-100 rounded-lg">
              <FolderKanban className="w-6 h-6 text-primary-600" />
            </div>
            <div>
              <p className="text-sm text-secondary-500">アクティブ案件</p>
              <p className="text-2xl font-bold text-secondary-900">
                {projects?.total || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 border border-secondary-100 shadow-sm">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-amber-100 rounded-lg">
              <ClipboardList className="w-6 h-6 text-amber-600" />
            </div>
            <div>
              <p className="text-sm text-secondary-500">進行中タスク</p>
              <p className="text-2xl font-bold text-secondary-900">
                {tasks?.total || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 border border-secondary-100 shadow-sm">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-green-100 rounded-lg">
              <CheckCircle2 className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-secondary-500">完了インタビュー</p>
              <p className="text-2xl font-bold text-secondary-900">0</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 border border-secondary-100 shadow-sm">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-purple-100 rounded-lg">
              <FileText className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-secondary-500">生成レポート</p>
              <p className="text-2xl font-bold text-secondary-900">0</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent items */}
      <div className="grid lg:grid-cols-2 gap-8">
        {/* Recent projects */}
        <div className="bg-white rounded-xl border border-secondary-100 shadow-sm">
          <div className="px-6 py-4 border-b border-secondary-100 flex justify-between items-center">
            <h2 className="font-semibold text-secondary-900">最近の案件</h2>
            <Link
              href="/projects"
              className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
            >
              すべて見る
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="divide-y divide-secondary-100">
            {projects?.items?.length > 0 ? (
              projects.items.map((project: any) => (
                <Link
                  key={project.id}
                  href={`/projects/${project.id}`}
                  className="flex items-center gap-4 px-6 py-4 hover:bg-secondary-50 transition"
                >
                  <div className="p-2 bg-secondary-100 rounded-lg">
                    <FolderKanban className="w-5 h-5 text-secondary-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-secondary-900 truncate">
                      {project.name}
                    </p>
                    <p className="text-sm text-secondary-500">
                      {project.client_name || '—'}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-secondary-500">
                      {project.task_count} タスク
                    </p>
                  </div>
                </Link>
              ))
            ) : (
              <div className="px-6 py-8 text-center text-secondary-500">
                案件がありません
              </div>
            )}
          </div>
        </div>

        {/* Recent tasks */}
        <div className="bg-white rounded-xl border border-secondary-100 shadow-sm">
          <div className="px-6 py-4 border-b border-secondary-100 flex justify-between items-center">
            <h2 className="font-semibold text-secondary-900">最近のタスク</h2>
            <Link
              href="/tasks"
              className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
            >
              すべて見る
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="divide-y divide-secondary-100">
            {tasks?.items?.length > 0 ? (
              tasks.items.map((task: any) => (
                <Link
                  key={task.id}
                  href={`/tasks/${task.id}`}
                  className="flex items-center gap-4 px-6 py-4 hover:bg-secondary-50 transition"
                >
                  <div className="p-2 bg-secondary-100 rounded-lg">
                    <ClipboardList className="w-5 h-5 text-secondary-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-secondary-900 truncate">
                      {task.name}
                    </p>
                    <p className="text-sm text-secondary-500">
                      {task.use_case_type}
                    </p>
                  </div>
                  <div className="text-right">
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                        task.status === 'completed'
                          ? 'bg-green-100 text-green-700'
                          : task.status === 'in_progress'
                          ? 'bg-amber-100 text-amber-700'
                          : 'bg-secondary-100 text-secondary-700'
                      }`}
                    >
                      {task.status}
                    </span>
                  </div>
                </Link>
              ))
            ) : (
              <div className="px-6 py-8 text-center text-secondary-500">
                タスクがありません
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Quick actions */}
      <div className="bg-white rounded-xl border border-secondary-100 shadow-sm p-6">
        <h2 className="font-semibold text-secondary-900 mb-4">クイックアクション</h2>
        <div className="flex flex-wrap gap-4">
          <Link
            href="/projects/new"
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition"
          >
            <FolderKanban className="w-5 h-5" />
            新規案件作成
          </Link>
          <Link
            href="/templates"
            className="flex items-center gap-2 px-4 py-2 border border-secondary-300 text-secondary-700 rounded-lg hover:bg-secondary-50 transition"
          >
            <FileText className="w-5 h-5" />
            テンプレート管理
          </Link>
        </div>
      </div>
    </div>
  );
}
