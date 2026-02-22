'use client';

import { useState, useEffect } from 'react';
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
  Settings2,
  Save,
} from 'lucide-react';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import api from '@/lib/api-client';
import { Button, Input, Modal, ModalBody, ModalFooter, Select, Tooltip, toast } from '@/components/ui';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton, SkeletonListItem } from '@/components/ui/skeleton';
import { EmptyState } from '@/components/ui/empty-state';
import { Breadcrumb } from '@/components/ui/breadcrumb';

interface Interview {
  id: string;
  status: string;
  language: string;
  startedAt: string | null;
  completedAt: string | null;
  durationSeconds: number | null;
  summary: string | null;
}

export default function TaskDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const taskId = params.id as string;

  const [isCreateInterviewModalOpen, setIsCreateInterviewModalOpen] = useState(false);
  const [isAiSettingsOpen, setIsAiSettingsOpen] = useState(false);
  const [aiSettings, setAiSettings] = useState({
    temperature: 0.7,
    maxQuestions: 10,
    timeLimitMinutes: 30,
    tone: 'formal',
    followUpDepth: 2,
  });

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
          { label: '案件', href: `/projects/${task?.projectId}` },
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
            {task?.targetCount || 0}
          </p>
        </Card>
        <Card className="p-6">
          <p className="text-sm text-surface-500 dark:text-surface-400 mb-1">実施数</p>
          <p className="text-2xl font-bold text-surface-900 dark:text-surface-50">
            {task?.interviewCount || 0}
          </p>
        </Card>
        <Card className="p-6">
          <p className="text-sm text-surface-500 dark:text-surface-400 mb-1">完了数</p>
          <p className="text-2xl font-bold text-emerald-500">
            {task?.completedInterviewCount || 0}
          </p>
        </Card>
        <Card className="p-6">
          <p className="text-sm text-surface-500 dark:text-surface-400 mb-1">達成率</p>
          <p className="text-2xl font-bold text-accent-500">
            {task?.targetCount
              ? Math.round(
                  ((task?.completedInterviewCount || 0) / task.targetCount) * 100
                )
              : 0}
            %
          </p>
        </Card>
      </div>

      {/* AI Settings */}
      <Card>
        <button
          onClick={() => setIsAiSettingsOpen(!isAiSettingsOpen)}
          className="w-full px-6 py-4 flex items-center justify-between hover:bg-surface-50 dark:hover:bg-surface-800/50 transition-colors"
        >
          <div className="flex items-center gap-3">
            <Settings2 className="w-5 h-5 text-accent-500" />
            <h2 className="font-semibold text-surface-900 dark:text-surface-50">AIインタビュー設定</h2>
          </div>
          <span className="text-sm text-surface-400">{isAiSettingsOpen ? '閉じる' : '開く'}</span>
        </button>
        {isAiSettingsOpen && (
          <div className="px-6 pb-6 border-t border-surface-200 dark:border-surface-700">
            <div className="grid grid-cols-2 gap-6 pt-4">
              <div>
                <Tooltip content="AIの応答の多様性を制御します。低いほど定型的、高いほど創造的になります" position="top">
                  <label className="inline-block text-sm font-medium text-surface-700 dark:text-surface-300 mb-2 cursor-help border-b border-dashed border-surface-300 dark:border-surface-600">
                    温度 (Temperature)
                  </label>
                </Tooltip>
                <div className="flex items-center gap-3">
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={aiSettings.temperature}
                    onChange={(e) => setAiSettings({ ...aiSettings, temperature: parseFloat(e.target.value) })}
                    className="flex-1 accent-accent-500"
                  />
                  <span className="text-sm font-medium text-surface-700 dark:text-surface-300 w-8 text-right">{aiSettings.temperature}</span>
                </div>
              </div>
              <div>
                <Tooltip content="1回のインタビューでAIが行う質問の最大数です" position="top">
                  <label className="inline-block text-sm font-medium text-surface-700 dark:text-surface-300 mb-2 cursor-help border-b border-dashed border-surface-300 dark:border-surface-600">
                    最大質問数
                  </label>
                </Tooltip>
                <input
                  type="number"
                  min="3"
                  max="30"
                  value={aiSettings.maxQuestions}
                  onChange={(e) => setAiSettings({ ...aiSettings, maxQuestions: parseInt(e.target.value) || 10 })}
                  className="w-full px-4 py-2 bg-white dark:bg-surface-800 border border-surface-200 dark:border-surface-700 rounded-lg text-surface-900 dark:text-surface-100 focus:outline-none focus:ring-2 focus:ring-accent-500/50"
                />
              </div>
              <div>
                <Tooltip content="インタビューの制限時間（分）です。超過すると自動終了します" position="top">
                  <label className="inline-block text-sm font-medium text-surface-700 dark:text-surface-300 mb-2 cursor-help border-b border-dashed border-surface-300 dark:border-surface-600">
                    制限時間（分）
                  </label>
                </Tooltip>
                <input
                  type="number"
                  min="5"
                  max="120"
                  value={aiSettings.timeLimitMinutes}
                  onChange={(e) => setAiSettings({ ...aiSettings, timeLimitMinutes: parseInt(e.target.value) || 30 })}
                  className="w-full px-4 py-2 bg-white dark:bg-surface-800 border border-surface-200 dark:border-surface-700 rounded-lg text-surface-900 dark:text-surface-100 focus:outline-none focus:ring-2 focus:ring-accent-500/50"
                />
              </div>
              <div>
                <Tooltip content="AIインタビュアーの対話スタイルです" position="top">
                  <label className="inline-block text-sm font-medium text-surface-700 dark:text-surface-300 mb-2 cursor-help border-b border-dashed border-surface-300 dark:border-surface-600">
                    トーン
                  </label>
                </Tooltip>
                <select
                  value={aiSettings.tone}
                  onChange={(e) => setAiSettings({ ...aiSettings, tone: e.target.value })}
                  className="w-full px-4 py-2 bg-white dark:bg-surface-800 border border-surface-200 dark:border-surface-700 rounded-lg text-surface-900 dark:text-surface-100 focus:outline-none focus:ring-2 focus:ring-accent-500/50"
                >
                  <option value="formal">フォーマル（丁寧語・敬語）</option>
                  <option value="casual">カジュアル（ですます調）</option>
                  <option value="professional">プロフェッショナル（専門的）</option>
                </select>
              </div>
              <div className="col-span-2">
                <Tooltip content="回答に対してAIが深掘り質問を行う回数の上限です" position="top">
                  <label className="inline-block text-sm font-medium text-surface-700 dark:text-surface-300 mb-2 cursor-help border-b border-dashed border-surface-300 dark:border-surface-600">
                    深掘り深度
                  </label>
                </Tooltip>
                <div className="flex items-center gap-3">
                  <input
                    type="range"
                    min="0"
                    max="5"
                    step="1"
                    value={aiSettings.followUpDepth}
                    onChange={(e) => setAiSettings({ ...aiSettings, followUpDepth: parseInt(e.target.value) })}
                    className="flex-1 accent-accent-500"
                  />
                  <span className="text-sm font-medium text-surface-700 dark:text-surface-300 w-16 text-right">
                    {aiSettings.followUpDepth === 0 ? 'なし' : `${aiSettings.followUpDepth}回`}
                  </span>
                </div>
              </div>
            </div>
            <div className="pt-4 mt-4 border-t border-surface-200 dark:border-surface-700">
              <Button
                variant="accent"
                size="sm"
                leftIcon={<Save className="w-4 h-4" />}
                onClick={() => toast.success('AI設定を保存しました')}
              >
                設定を保存
              </Button>
            </div>
          </div>
        )}
      </Card>

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
                    {interview.startedAt && (
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {format(new Date(interview.startedAt), 'M/d HH:mm', {
                          locale: ja,
                        })}
                      </span>
                    )}
                    {interview.durationSeconds && (
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatDuration(interview.durationSeconds)}
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
