'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import {
  FolderKanban,
  ClipboardList,
  MessageSquare,
  FileText,
  ArrowRight,
  CheckCircle2,
  Plus,
} from 'lucide-react';
import { cn } from '@/lib/cn';
import { USE_CASE_LABELS } from '@/lib/constants';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tooltip } from '@/components/ui/tooltip';
import { EmptyState } from '@/components/ui/empty-state';
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

  const { data: interviews } = useQuery({
    queryKey: ['interviews', { status: 'completed' }],
    queryFn: () => api.interviews.list({ status: 'completed' }),
  });

  const { data: reports } = useQuery({
    queryKey: ['reports'],
    queryFn: () => api.reports.list(),
  });

  const stats = [
    {
      label: 'アクティブ案件',
      value: projects?.total || 0,
      icon: FolderKanban,
      color: 'text-accent-500',
      bgColor: 'bg-accent-500/10',
      tooltip: '現在進行中のGRC案件数です',
    },
    {
      label: '進行中タスク',
      value: tasks?.total || 0,
      icon: ClipboardList,
      color: 'text-blue-500',
      bgColor: 'bg-blue-500/10',
      tooltip: 'インタビュー等の実施待ちタスク数です',
    },
    {
      label: '完了インタビュー',
      value: interviews?.total || 0,
      icon: CheckCircle2,
      color: 'text-emerald-500',
      bgColor: 'bg-emerald-500/10',
      tooltip: '完了済みのAIインタビュー件数です',
    },
    {
      label: '生成レポート',
      value: reports?.total || 0,
      icon: FileText,
      color: 'text-purple-500',
      bgColor: 'bg-purple-500/10',
      tooltip: 'AIが生成したレポートの総数です',
    },
  ];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* ヘッダー */}
      <div>
        <h1 className="text-2xl font-bold text-surface-900 dark:text-surface-50">
          GRC ダッシュボード
        </h1>
        <p className="text-surface-500 dark:text-surface-400 mt-1">
          ガバナンス・リスク・コンプライアンス業務の進捗を一元管理します
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <Card key={stat.label} hover className="p-5">
            <div className="flex items-center gap-4">
              <div className={cn('p-2.5 rounded-lg', stat.bgColor)}>
                <stat.icon className={cn('w-5 h-5', stat.color)} />
              </div>
              <div>
                <Tooltip content={stat.tooltip} position="bottom">
                  <p className="text-sm text-surface-500 dark:text-surface-400 cursor-help border-b border-dashed border-surface-300 dark:border-surface-600">{stat.label}</p>
                </Tooltip>
                <p className="text-2xl font-bold text-surface-900 dark:text-surface-50">{stat.value}</p>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* メインコンテンツ - 非対称レイアウト */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* 左: 最近の案件 + タスク (2/3) */}
        <div className="lg:col-span-2 space-y-6">
          {/* 最近の案件 */}
          <Card>
            <div className="px-6 py-4 border-b border-surface-200 dark:border-surface-700 flex justify-between items-center">
              <h2 className="font-semibold text-surface-900 dark:text-surface-50">最近の案件</h2>
              <Link
                href="/projects"
                className="text-sm text-accent-500 hover:text-accent-600 flex items-center gap-1 transition-colors"
              >
                すべて見る
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
            <div className="divide-y divide-surface-100 dark:divide-surface-800">
              {projects?.items?.length > 0 ? (
                projects.items.map((project: any) => (
                  <Link
                    key={project.id}
                    href={`/projects/${project.id}`}
                    className="flex items-center gap-4 px-6 py-4 hover:bg-surface-50 dark:hover:bg-surface-800/50 transition-colors"
                  >
                    <div className="p-2 bg-surface-100 dark:bg-surface-800 rounded-lg">
                      <FolderKanban className="w-5 h-5 text-surface-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-surface-900 dark:text-surface-100 truncate">
                        {project.name}
                      </p>
                      <p className="text-sm text-surface-500 dark:text-surface-400">
                        {project.clientName || '—'}
                      </p>
                    </div>
                    <span className="text-sm text-surface-400">
                      {project.taskCount} タスク
                    </span>
                  </Link>
                ))
              ) : (
                <EmptyState
                  icon={FolderKanban}
                  title="案件がありません"
                  description="新しい案件を作成して始めましょう"
                  action={{ label: '案件を作成', href: '/projects/new' }}
                />
              )}
            </div>
          </Card>

          {/* 最近のタスク */}
          <Card>
            <div className="px-6 py-4 border-b border-surface-200 dark:border-surface-700 flex justify-between items-center">
              <h2 className="font-semibold text-surface-900 dark:text-surface-50">最近のタスク</h2>
              <Link
                href="/tasks"
                className="text-sm text-accent-500 hover:text-accent-600 flex items-center gap-1 transition-colors"
              >
                すべて見る
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
            <div className="divide-y divide-surface-100 dark:divide-surface-800">
              {tasks?.items?.length > 0 ? (
                tasks.items.map((task: any) => (
                  <Link
                    key={task.id}
                    href={`/tasks/${task.id}`}
                    className="flex items-center gap-4 px-6 py-4 hover:bg-surface-50 dark:hover:bg-surface-800/50 transition-colors"
                  >
                    <div className="p-2 bg-surface-100 dark:bg-surface-800 rounded-lg">
                      <ClipboardList className="w-5 h-5 text-surface-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-surface-900 dark:text-surface-100 truncate">
                        {task.name}
                      </p>
                      <p className="text-sm text-surface-500 dark:text-surface-400">
                        {USE_CASE_LABELS[task.useCaseType] || task.useCaseType}
                      </p>
                    </div>
                    <Badge
                      variant={
                        task.status === 'completed'
                          ? 'success'
                          : task.status === 'in_progress'
                          ? 'warning'
                          : 'default'
                      }
                    >
                      {task.status === 'pending' ? '未着手' : task.status === 'in_progress' ? '進行中' : task.status === 'completed' ? '完了' : task.status}
                    </Badge>
                  </Link>
                ))
              ) : (
                <EmptyState
                  icon={ClipboardList}
                  title="タスクがありません"
                  description="案件からタスクを作成してください"
                />
              )}
            </div>
          </Card>
        </div>

        {/* 右: クイックアクション (1/3) */}
        <div className="space-y-6">
          <Card className="p-6">
            <h2 className="font-semibold text-surface-900 dark:text-surface-50 mb-4">
              クイックアクション
            </h2>
            <div className="space-y-3">
              <Link
                href="/projects/new"
                className="flex items-center gap-3 px-4 py-3 rounded-xl bg-gradient-to-r from-accent-500 to-accent-600 text-white hover:from-accent-600 hover:to-accent-700 transition-all shadow-lg shadow-accent-500/20"
              >
                <Plus className="w-5 h-5" />
                <span className="font-medium">新規案件作成</span>
              </Link>
              <Link
                href="/templates"
                className="flex items-center gap-3 px-4 py-3 rounded-xl border border-surface-200 dark:border-surface-700 text-surface-700 dark:text-surface-300 hover:bg-surface-50 dark:hover:bg-surface-800 transition-colors"
              >
                <FileText className="w-5 h-5 text-surface-400" />
                <span className="font-medium">テンプレート管理</span>
              </Link>
              <Link
                href="/tasks"
                className="flex items-center gap-3 px-4 py-3 rounded-xl border border-surface-200 dark:border-surface-700 text-surface-700 dark:text-surface-300 hover:bg-surface-50 dark:hover:bg-surface-800 transition-colors"
              >
                <MessageSquare className="w-5 h-5 text-surface-400" />
                <span className="font-medium">タスクからインタビュー開始</span>
              </Link>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
