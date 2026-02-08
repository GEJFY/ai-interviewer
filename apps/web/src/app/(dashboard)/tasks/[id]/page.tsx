'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import {
  ArrowLeft,
  Plus,
  MessageSquare,
  Play,
  FileText,
  Calendar,
  Clock,
  User,
  CheckCircle2,
} from 'lucide-react';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import api from '@/lib/api-client';
import { Button, Modal, ModalBody, ModalFooter } from '@/components/ui';

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
      // Navigate to interview page
      router.push(`/interviews/${data.id}`);
    },
  });

  const getStatusBadge = (status: string) => {
    const styles = {
      scheduled: 'bg-secondary-100 text-secondary-700',
      in_progress: 'bg-amber-100 text-amber-700',
      paused: 'bg-orange-100 text-orange-700',
      completed: 'bg-green-100 text-green-700',
      cancelled: 'bg-red-100 text-red-700',
    };
    const labels = {
      scheduled: '予定',
      in_progress: '実施中',
      paused: '一時停止',
      completed: '完了',
      cancelled: 'キャンセル',
    };
    return (
      <span
        className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
          styles[status as keyof typeof styles] || styles.scheduled
        }`}
      >
        {labels[status as keyof typeof labels] || status}
      </span>
    );
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}分${secs}秒`;
  };

  if (isLoadingTask) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-secondary-200 rounded w-1/4" />
        <div className="h-4 bg-secondary-200 rounded w-1/2" />
        <div className="h-64 bg-secondary-200 rounded" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link
        href={`/projects/${task?.project_id}`}
        className="inline-flex items-center gap-2 text-secondary-600 hover:text-secondary-900 transition"
      >
        <ArrowLeft className="w-4 h-4" />
        案件に戻る
      </Link>

      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-bold text-secondary-900">
              {task?.name}
            </h1>
            {getStatusBadge(task?.status)}
          </div>
          {task?.description && (
            <p className="text-secondary-600">{task.description}</p>
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
            leftIcon={<Plus className="w-5 h-5" />}
            onClick={() => setIsCreateInterviewModalOpen(true)}
          >
            インタビュー開始
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-6">
        <div className="bg-white rounded-xl border border-secondary-200 p-6">
          <p className="text-sm text-secondary-500 mb-1">目標数</p>
          <p className="text-2xl font-bold text-secondary-900">
            {task?.target_count || 0}
          </p>
        </div>
        <div className="bg-white rounded-xl border border-secondary-200 p-6">
          <p className="text-sm text-secondary-500 mb-1">実施数</p>
          <p className="text-2xl font-bold text-secondary-900">
            {task?.interview_count || 0}
          </p>
        </div>
        <div className="bg-white rounded-xl border border-secondary-200 p-6">
          <p className="text-sm text-secondary-500 mb-1">完了数</p>
          <p className="text-2xl font-bold text-green-600">
            {task?.completed_interview_count || 0}
          </p>
        </div>
        <div className="bg-white rounded-xl border border-secondary-200 p-6">
          <p className="text-sm text-secondary-500 mb-1">達成率</p>
          <p className="text-2xl font-bold text-primary-600">
            {task?.target_count
              ? Math.round(
                  ((task?.completed_interview_count || 0) / task.target_count) * 100
                )
              : 0}
            %
          </p>
        </div>
      </div>

      {/* Interviews */}
      <div className="bg-white rounded-xl border border-secondary-200">
        <div className="px-6 py-4 border-b border-secondary-200">
          <h2 className="font-semibold text-secondary-900">インタビュー一覧</h2>
        </div>

        {isLoadingInterviews ? (
          <div className="p-6">
            <div className="animate-pulse space-y-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-16 bg-secondary-100 rounded" />
              ))}
            </div>
          </div>
        ) : interviewsData?.items?.length > 0 ? (
          <div className="divide-y divide-secondary-100">
            {interviewsData.items.map((interview: Interview) => (
              <div
                key={interview.id}
                className="flex items-center gap-4 px-6 py-4 hover:bg-secondary-50 transition"
              >
                <div
                  className={`p-2 rounded-lg ${
                    interview.status === 'completed'
                      ? 'bg-green-100'
                      : interview.status === 'in_progress'
                      ? 'bg-amber-100'
                      : 'bg-secondary-100'
                  }`}
                >
                  {interview.status === 'completed' ? (
                    <CheckCircle2 className="w-5 h-5 text-green-600" />
                  ) : (
                    <MessageSquare className="w-5 h-5 text-secondary-500" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-secondary-900">
                    インタビュー #{interview.id.slice(0, 8)}
                  </p>
                  <div className="flex items-center gap-4 text-sm text-secondary-500">
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
                  {getStatusBadge(interview.status)}
                  {interview.status === 'scheduled' && (
                    <Button
                      size="sm"
                      leftIcon={<Play className="w-4 h-4" />}
                      onClick={() => router.push(`/interviews/${interview.id}`)}
                    >
                      開始
                    </Button>
                  )}
                  {interview.status === 'in_progress' && (
                    <Button
                      size="sm"
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
          <div className="p-12 text-center">
            <MessageSquare className="w-12 h-12 text-secondary-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-secondary-900 mb-2">
              インタビューがありません
            </h3>
            <p className="text-secondary-500 mb-6">
              新しいインタビューを開始しましょう
            </p>
            <Button onClick={() => setIsCreateInterviewModalOpen(true)}>
              最初のインタビューを開始
            </Button>
          </div>
        )}
      </div>

      {/* Create Interview Modal */}
      <Modal
        isOpen={isCreateInterviewModalOpen}
        onClose={() => setIsCreateInterviewModalOpen(false)}
        title="インタビューを開始"
        size="sm"
      >
        <ModalBody>
          <p className="text-secondary-600">
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
