'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { ClipboardList, Calendar, MessageSquare } from 'lucide-react';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import api from '@/lib/api-client';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { SkeletonListItem } from '@/components/ui/skeleton';
import { EmptyState } from '@/components/ui/empty-state';

interface Task {
  id: string;
  name: string;
  project_id: string;
  use_case_type: string;
  status: string;
  interview_count: number;
  completed_interview_count: number;
  deadline: string | null;
}

const USE_CASE_LABELS: Record<string, string> = {
  compliance_survey: 'コンプライアンス意識調査',
  whistleblower_investigation: '内部通報調査',
  process_review: '業務プロセスヒアリング',
  control_evaluation: '統制評価（J-SOX）',
  risk_assessment: 'リスクアセスメント',
  board_effectiveness: '取締役会実効性評価',
  tacit_knowledge: 'ナレッジ抽出',
};

export default function TasksPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => api.tasks.list({ pageSize: 100 }),
  });

  const statusVariant = (status: string) => {
    if (status === 'in_progress') return 'warning';
    if (status === 'completed') return 'success';
    if (status === 'cancelled') return 'danger';
    return 'default';
  };

  const statusLabel = (status: string) => {
    const labels: Record<string, string> = {
      pending: '未着手',
      in_progress: '進行中',
      completed: '完了',
      cancelled: 'キャンセル',
    };
    return labels[status] || status;
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-surface-900 dark:text-surface-50">タスク管理</h1>
        <p className="text-surface-500 dark:text-surface-400 mt-1">
          すべてのインタビュータスクを確認できます
        </p>
      </div>

      <Card>
        {isLoading ? (
          <div className="p-4">
            <SkeletonListItem count={5} />
          </div>
        ) : data?.items?.length > 0 ? (
          <div className="divide-y divide-surface-100 dark:divide-surface-800">
            {data.items.map((task: Task) => (
              <Link
                key={task.id}
                href={`/tasks/${task.id}`}
                className="flex items-center gap-4 px-6 py-4 hover:bg-surface-50 dark:hover:bg-surface-800/50 transition-colors"
              >
                <div className="p-2 bg-surface-100 dark:bg-surface-800 rounded-lg">
                  <ClipboardList className="w-5 h-5 text-surface-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-surface-900 dark:text-surface-100">{task.name}</p>
                  <p className="text-sm text-surface-500 dark:text-surface-400">
                    {USE_CASE_LABELS[task.use_case_type] || task.use_case_type}
                  </p>
                </div>
                <div className="flex items-center gap-6">
                  <div className="flex items-center gap-2 text-sm text-surface-500 dark:text-surface-400">
                    <MessageSquare className="w-4 h-4" />
                    {task.completed_interview_count}/{task.interview_count}
                  </div>
                  {task.deadline && (
                    <div className="flex items-center gap-2 text-sm text-surface-400">
                      <Calendar className="w-4 h-4" />
                      {format(new Date(task.deadline), 'M/d', { locale: ja })}
                    </div>
                  )}
                  <Badge variant={statusVariant(task.status)}>
                    {statusLabel(task.status)}
                  </Badge>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <EmptyState
            icon={ClipboardList}
            title="タスクがありません"
            description="案件からタスクを作成してください"
            action={{ label: '案件一覧へ', href: '/projects' }}
          />
        )}
      </Card>
    </div>
  );
}
