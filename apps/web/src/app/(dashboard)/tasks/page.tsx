'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { ClipboardList, Calendar, MessageSquare } from 'lucide-react';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import api from '@/lib/api-client';

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

  const getStatusBadge = (status: string) => {
    const styles = {
      pending: 'bg-secondary-100 text-secondary-700',
      in_progress: 'bg-amber-100 text-amber-700',
      completed: 'bg-green-100 text-green-700',
      cancelled: 'bg-red-100 text-red-700',
    };
    const labels = {
      pending: '未着手',
      in_progress: '進行中',
      completed: '完了',
      cancelled: 'キャンセル',
    };
    return (
      <span
        className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
          styles[status as keyof typeof styles] || styles.pending
        }`}
      >
        {labels[status as keyof typeof labels] || status}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-secondary-900">タスク管理</h1>
        <p className="text-secondary-600 mt-1">
          すべてのインタビュータスクを確認できます
        </p>
      </div>

      {/* Tasks List */}
      <div className="bg-white rounded-xl border border-secondary-200">
        {isLoading ? (
          <div className="p-6">
            <div className="animate-pulse space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-16 bg-secondary-100 rounded" />
              ))}
            </div>
          </div>
        ) : data?.items?.length > 0 ? (
          <div className="divide-y divide-secondary-100">
            {data.items.map((task: Task) => (
              <Link
                key={task.id}
                href={`/tasks/${task.id}`}
                className="flex items-center gap-4 px-6 py-4 hover:bg-secondary-50 transition"
              >
                <div className="p-2 bg-secondary-100 rounded-lg">
                  <ClipboardList className="w-5 h-5 text-secondary-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-secondary-900">{task.name}</p>
                  <p className="text-sm text-secondary-500">
                    {USE_CASE_LABELS[task.use_case_type] || task.use_case_type}
                  </p>
                </div>
                <div className="flex items-center gap-6">
                  <div className="flex items-center gap-2 text-sm text-secondary-600">
                    <MessageSquare className="w-4 h-4" />
                    {task.completed_interview_count}/{task.interview_count}
                  </div>
                  {task.deadline && (
                    <div className="flex items-center gap-2 text-sm text-secondary-500">
                      <Calendar className="w-4 h-4" />
                      {format(new Date(task.deadline), 'M/d', { locale: ja })}
                    </div>
                  )}
                  {getStatusBadge(task.status)}
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="p-12 text-center">
            <ClipboardList className="w-12 h-12 text-secondary-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-secondary-900 mb-2">
              タスクがありません
            </h3>
            <p className="text-secondary-500">
              案件からタスクを作成してください
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
