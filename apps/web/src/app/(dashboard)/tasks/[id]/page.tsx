'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus,
  MessageSquare,
  Play,
  FileText,
  Calendar,
  Clock,
  CheckCircle2,
} from 'lucide-react';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import api from '@/lib/api-client';
import { Button, Modal, ModalBody, ModalFooter, toast } from '@/components/ui';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton, SkeletonListItem } from '@/components/ui/skeleton';
import { EmptyState } from '@/components/ui/empty-state';
import { Breadcrumb } from '@/components/ui/breadcrumb';

interface Interview {
  id: string;
  status: string;
  language: string;
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;
  summary: string | null;
}

export default function TaskDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const taskId = params.id as string;

  const [isCreateInterviewModalOpen, setIsCreateInterviewModalOpen] = useState(false);

  const { data: task, isLoading: isLoadingTask } = useQuery({
    queryKey: ['task', taskId],
    queryFn: () => api.tasks.get(taskId),
  });

  const { data: interviewsData, isLoading: isLoadingInterviews } = useQuery({
    queryKey: ['interviews', { taskId }],
    queryFn: () => api.interviews.list({ taskId }),
  });

  const createInterviewMutation = useMutation({
    mutationFn: () => api.interviews.create({ taskId, language: 'ja' }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['interviews', { taskId }] });
      queryClient.invalidateQueries({ queryKey: ['task', taskId] });
      setIsCreateInterviewModalOpen(false);
      toast.success('インタビューを開始します');
      router.push(`/interviews/${data.id}`);
    },
    onError: () => {
      toast.error('インタビューの開始に失敗しました');
    },
  });

  const statusBadgeVariant = (status: string) => {
    if (status === 'in_progress') return 'warning' as const;
    if (status === 'completed') return 'success' as const;
    if (status === 'cancelled') return 'danger' as const;
    if (status === 'paused') return 'warning' as const;
    return 'default' as const;
  };

  const statusLabel = (status: string) => {
    const labels: Record<string, string> = {
      scheduled: '予定',
      in_progress: '実施中',
      paused: '一時停止',
      completed: '完了',
      cancelled: 'キャンセル',
    };
    return labels[status] || status;
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}分${secs}秒`;
  };

  if (isLoadingTask) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-1/4" />
        <Skeleton className="h-4 w-1/2" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <Breadcrumb
        items={[
          { label: '案件管理', href: '/projects' },
          { label: '案件', href: `/projects/${task?.project_id}` },
          { label: task?.name || '...' },
        ]}
      />

      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-bold text-surface-900 dark:text-surface-50">
              {task?.name}
            </h1>
            <Badge variant={statusBadgeVariant(task?.status)}>
              {statusLabel(task?.status)}
            </Badge>
          </div>
          {task?.description && (
            <p className="text-surface-500 dark:text-surface-400">{task.description}</p>
          )}
        </div>
        <div className="flex gap-3">
          <Button
            variant="outline"
            leftIcon={<FileText className="w-4 h-4" />}
            onClick={() => router.push(`/reports?taskId=${taskId}`)}
          >
            レポート
          </Button>
          <Button
            variant="accent"
            leftIcon={<Plus className="w-5 h-5" />}
            onClick={() => setIsCreateInterviewModalOpen(true)}
          >
            インタビュー開始
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-6">
        <Card className="p-6">
          <p className="text-sm text-surface-500 dark:text-surface-400 mb-1">目標数</p>
          <p className="text-2xl font-bold text-surface-900 dark:text-surface-50">
            {task?.target_count || 0}
          </p>
        </Card>
        <Card className="p-6">
          <p className="text-sm text-surface-500 dark:text-surface-400 mb-1">実施数</p>
          <p className="text-2xl font-bold text-surface-900 dark:text-surface-50">
            {task?.interview_count || 0}
          </p>
        </Card>
        <Card className="p-6">
          <p className="text-sm text-surface-500 dark:text-surface-400 mb-1">完了数</p>
          <p className="text-2xl font-bold text-emerald-500">
            {task?.completed_interview_count || 0}
          </p>
        </Card>
        <Card className="p-6">
          <p className="text-sm text-surface-500 dark:text-surface-400 mb-1">達成率</p>
          <p className="text-2xl font-bold text-accent-500">
            {task?.target_count
              ? Math.round(
                  ((task?.completed_interview_count || 0) / task.target_count) * 100
                )
              : 0}
            %
          </p>
        </Card>
      </div>

      {/* Interviews */}
      <Card>
        <div className="px-6 py-4 border-b border-surface-200 dark:border-surface-700">
          <h2 className="font-semibold text-surface-900 dark:text-surface-50">インタビュー一覧</h2>
        </div>

        {isLoadingInterviews ? (
          <div className="p-4">
            <SkeletonListItem count={3} />
          </div>
        ) : interviewsData?.items?.length > 0 ? (
          <div className="divide-y divide-surface-100 dark:divide-surface-800">
            {interviewsData.items.map((interview: Interview) => (
              <div
                key={interview.id}
                className="flex items-center gap-4 px-6 py-4 hover:bg-surface-50 dark:hover:bg-surface-800/50 transition"
              >
                <div
                  className={`p-2 rounded-lg ${
                    interview.status === 'completed'
                      ? 'bg-emerald-500/10'
                      : interview.status === 'in_progress'
                      ? 'bg-amber-500/10'
                      : 'bg-surface-100 dark:bg-surface-800'
                  }`}
                >
                  {interview.status === 'completed' ? (
                    <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                  ) : (
                    <MessageSquare className="w-5 h-5 text-surface-500 dark:text-surface-400" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-surface-900 dark:text-surface-50">
                    インタビュー #{interview.id.slice(0, 8)}
                  </p>
                  <div className="flex items-center gap-4 text-sm text-surface-500 dark:text-surface-400">
                    {interview.started_at && (
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {format(new Date(interview.started_at), 'M/d HH:mm', {
                          locale: ja,
                        })}
                      </span>
                    )}
                    {interview.duration_seconds && (
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatDuration(interview.duration_seconds)}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Badge variant={statusBadgeVariant(interview.status)}>
                    {statusLabel(interview.status)}
                  </Badge>
                  {interview.status === 'scheduled' && (
                    <Button
                      size="sm"
                      variant="accent"
                      leftIcon={<Play className="w-4 h-4" />}
                      onClick={() => router.push(`/interviews/${interview.id}`)}
                    >
                      開始
                    </Button>
                  )}
                  {interview.status === 'in_progress' && (
                    <Button
                      size="sm"
                      variant="accent"
                      onClick={() => router.push(`/interviews/${interview.id}`)}
                    >
                      続ける
                    </Button>
                  )}
                  {interview.status === 'completed' && (
                    <Button
                      size="sm"
                      variant="outline"
                      leftIcon={<FileText className="w-4 h-4" />}
                      onClick={() =>
                        router.push(`/reports?interviewId=${interview.id}`)
                      }
                    >
                      レポート
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState
            icon={MessageSquare}
            title="インタビューがありません"
            description="新しいインタビューを開始しましょう"
            action={{ label: '最初のインタビューを開始', onClick: () => setIsCreateInterviewModalOpen(true) }}
          />
        )}
      </Card>

      {/* Create Interview Modal */}
      <Modal
        isOpen={isCreateInterviewModalOpen}
        onClose={() => setIsCreateInterviewModalOpen(false)}
        title="インタビューを開始"
        size="sm"
      >
        <ModalBody>
          <p className="text-surface-500 dark:text-surface-400">
            新しいインタビューセッションを開始します。
            AIが質問を自動生成し、対話形式でインタビューを進めます。
          </p>
        </ModalBody>
        <ModalFooter>
          <Button
            variant="outline"
            onClick={() => setIsCreateInterviewModalOpen(false)}
          >
            キャンセル
          </Button>
          <Button
            variant="accent"
            onClick={() => createInterviewMutation.mutate()}
            isLoading={createInterviewMutation.isPending}
            leftIcon={<Play className="w-4 h-4" />}
          >
            開始
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
