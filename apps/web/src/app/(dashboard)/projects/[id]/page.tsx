'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import {
  ArrowLeft,
  Plus,
  ClipboardList,
  Edit2,
  Calendar,
  Users,
} from 'lucide-react';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import api from '@/lib/api-client';
import { Button, Input, Select, Modal, ModalBody, ModalFooter } from '@/components/ui';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

const USE_CASE_OPTIONS = [
  { value: 'compliance_survey', label: 'コンプライアンス意識調査' },
  { value: 'whistleblower_investigation', label: '内部通報調査' },
  { value: 'process_review', label: '業務プロセスヒアリング' },
  { value: 'control_evaluation', label: '統制評価（J-SOX）' },
  { value: 'risk_assessment', label: 'リスクアセスメント' },
  { value: 'board_effectiveness', label: '取締役会実効性評価' },
  { value: 'tacit_knowledge', label: 'ナレッジ抽出' },
];

interface Task {
  id: string;
  name: string;
  description: string | null;
  use_case_type: string;
  status: string;
  interview_count: number;
  completed_interview_count: number;
  deadline: string | null;
}

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const projectId = params.id as string;

  const [isCreateTaskModalOpen, setIsCreateTaskModalOpen] = useState(false);
  const [newTask, setNewTask] = useState({
    name: '',
    description: '',
    use_case_type: '',
    target_count: 1,
  });

  const { data: project, isLoading: isLoadingProject } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => api.projects.get(projectId),
  });

  const { data: tasksData, isLoading: isLoadingTasks } = useQuery({
    queryKey: ['tasks', { projectId }],
    queryFn: () => api.tasks.list({ projectId }),
  });

  const createTaskMutation = useMutation({
    mutationFn: (data: any) => api.tasks.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks', { projectId }] });
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });
      setIsCreateTaskModalOpen(false);
      setNewTask({ name: '', description: '', use_case_type: '', target_count: 1 });
    },
  });

  const handleCreateTask = () => {
    if (!newTask.name.trim() || !newTask.use_case_type) return;
    createTaskMutation.mutate({
      name: newTask.name,
      description: newTask.description || undefined,
      projectId,
      useCaseType: newTask.use_case_type,
      targetCount: newTask.target_count,
    });
  };

  const statusBadgeVariant = (status: string) => {
    if (status === 'in_progress') return 'warning' as const;
    if (status === 'completed') return 'success' as const;
    if (status === 'cancelled') return 'danger' as const;
    return 'default' as const;
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

  const getUseCaseLabel = (type: string) => {
    return USE_CASE_OPTIONS.find((opt) => opt.value === type)?.label || type;
  };

  if (isLoadingProject) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-surface-200 dark:bg-surface-700 rounded w-1/4" />
        <div className="h-4 bg-surface-200 dark:bg-surface-700 rounded w-1/2" />
        <div className="h-64 bg-surface-200 dark:bg-surface-700 rounded" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Back link */}
      <Link
        href="/projects"
        className="inline-flex items-center gap-2 text-surface-500 hover:text-surface-900 dark:hover:text-surface-100 transition"
      >
        <ArrowLeft className="w-4 h-4" />
        案件一覧に戻る
      </Link>

      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-bold text-surface-900 dark:text-surface-50">
              {project?.name}
            </h1>
            <Badge variant={project?.status === 'active' ? 'success' : 'default'}>
              {project?.status === 'active' ? '進行中' : project?.status === 'completed' ? '完了' : project?.status}
            </Badge>
          </div>
          {project?.client_name && (
            <p className="text-surface-500 dark:text-surface-400 flex items-center gap-2">
              <Users className="w-4 h-4" />
              {project.client_name}
            </p>
          )}
          {project?.description && (
            <p className="text-surface-500 dark:text-surface-400 mt-2">{project.description}</p>
          )}
        </div>
        <div className="flex gap-3">
          <Button variant="outline" leftIcon={<Edit2 className="w-4 h-4" />}>
            編集
          </Button>
          <Button
            variant="accent"
            leftIcon={<Plus className="w-5 h-5" />}
            onClick={() => setIsCreateTaskModalOpen(true)}
          >
            タスク追加
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-6">
        <Card className="p-6">
          <p className="text-sm text-surface-500 dark:text-surface-400 mb-1">タスク数</p>
          <p className="text-2xl font-bold text-surface-900 dark:text-surface-50">
            {project?.task_count || 0}
          </p>
        </Card>
        <Card className="p-6">
          <p className="text-sm text-surface-500 dark:text-surface-400 mb-1">完了タスク</p>
          <p className="text-2xl font-bold text-emerald-500">
            {project?.completed_task_count || 0}
          </p>
        </Card>
        <Card className="p-6">
          <p className="text-sm text-surface-500 dark:text-surface-400 mb-1">進捗率</p>
          <p className="text-2xl font-bold text-accent-500">
            {project?.task_count
              ? Math.round(
                  ((project?.completed_task_count || 0) / project.task_count) * 100
                )
              : 0}
            %
          </p>
        </Card>
      </div>

      {/* Tasks */}
      <Card>
        <div className="px-6 py-4 border-b border-surface-200 dark:border-surface-700">
          <h2 className="font-semibold text-surface-900 dark:text-surface-50">タスク一覧</h2>
        </div>

        {isLoadingTasks ? (
          <div className="p-6">
            <div className="animate-pulse space-y-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-16 bg-surface-200 dark:bg-surface-700 rounded" />
              ))}
            </div>
          </div>
        ) : tasksData?.items?.length > 0 ? (
          <div className="divide-y divide-surface-100 dark:divide-surface-800">
            {tasksData.items.map((task: Task) => (
              <Link
                key={task.id}
                href={`/tasks/${task.id}`}
                className="flex items-center gap-4 px-6 py-4 hover:bg-surface-50 dark:hover:bg-surface-800/50 transition"
              >
                <div className="p-2 bg-surface-100 dark:bg-surface-800 rounded-lg">
                  <ClipboardList className="w-5 h-5 text-surface-500 dark:text-surface-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-surface-900 dark:text-surface-50">{task.name}</p>
                  <p className="text-sm text-surface-500 dark:text-surface-400">
                    {getUseCaseLabel(task.use_case_type)}
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="text-sm text-surface-500 dark:text-surface-400">
                      {task.completed_interview_count}/{task.interview_count} 完了
                    </p>
                    {task.deadline && (
                      <p className="text-xs text-surface-400 flex items-center gap-1 justify-end">
                        <Calendar className="w-3 h-3" />
                        {format(new Date(task.deadline), 'M/d', { locale: ja })}
                      </p>
                    )}
                  </div>
                  <Badge variant={statusBadgeVariant(task.status)}>
                    {statusLabel(task.status)}
                  </Badge>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="p-12 text-center">
            <ClipboardList className="w-12 h-12 text-surface-300 dark:text-surface-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-surface-900 dark:text-surface-50 mb-2">
              タスクがありません
            </h3>
            <p className="text-surface-500 dark:text-surface-400 mb-6">
              新しいタスクを追加してインタビューを開始しましょう
            </p>
            <Button variant="accent" onClick={() => setIsCreateTaskModalOpen(true)}>
              最初のタスクを作成
            </Button>
          </div>
        )}
      </Card>

      {/* Create Task Modal */}
      <Modal
        isOpen={isCreateTaskModalOpen}
        onClose={() => setIsCreateTaskModalOpen(false)}
        title="新規タスク作成"
        size="md"
      >
        <ModalBody className="space-y-4">
          <Input
            label="タスク名"
            placeholder="例：コンプライアンス意識調査 2025Q1"
            value={newTask.name}
            onChange={(e) => setNewTask({ ...newTask, name: e.target.value })}
          />
          <Select
            label="ユースケース"
            placeholder="ユースケースを選択"
            options={USE_CASE_OPTIONS}
            value={newTask.use_case_type}
            onChange={(e) =>
              setNewTask({ ...newTask, use_case_type: e.target.value })
            }
          />
          <Input
            label="目標インタビュー数"
            type="number"
            min={1}
            value={newTask.target_count}
            onChange={(e) =>
              setNewTask({ ...newTask, target_count: parseInt(e.target.value) || 1 })
            }
          />
          <div>
            <label className="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-2">
              説明
            </label>
            <textarea
              placeholder="タスクの概要を入力..."
              value={newTask.description}
              onChange={(e) =>
                setNewTask({ ...newTask, description: e.target.value })
              }
              rows={3}
              className="w-full px-4 py-2.5 bg-white dark:bg-surface-800 border border-surface-300 dark:border-surface-600 rounded-lg text-surface-900 dark:text-surface-100 placeholder:text-surface-400 focus:outline-none focus:ring-2 focus:ring-accent-500/50 focus:border-accent-500 resize-none transition-all"
            />
          </div>
        </ModalBody>
        <ModalFooter>
          <Button
            variant="outline"
            onClick={() => setIsCreateTaskModalOpen(false)}
          >
            キャンセル
          </Button>
          <Button
            variant="accent"
            onClick={handleCreateTask}
            isLoading={createTaskMutation.isPending}
            disabled={!newTask.name.trim() || !newTask.use_case_type}
          >
            作成
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
