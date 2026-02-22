'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import {
  Plus,
  ClipboardList,
  Edit2,
  Calendar,
  Users,
} from 'lucide-react';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import api from '@/lib/api-client';
import { USE_CASE_OPTIONS } from '@/lib/constants';
import { Button, Input, Select, Modal, ModalBody, ModalFooter, toast } from '@/components/ui';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton, SkeletonListItem } from '@/components/ui/skeleton';
import { EmptyState } from '@/components/ui/empty-state';
import { Breadcrumb } from '@/components/ui/breadcrumb';

interface Task {
  id: string;
  name: string;
  description: string | null;
  useCaseType: string;
  status: string;
  interviewCount: number;
  completedInterviewCount: number;
  deadline: string | null;
}

const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const projectId = params.id as string;

  const [isCreateTaskModalOpen, setIsCreateTaskModalOpen] = useState(false);
  const [newTask, setNewTask] = useState({
    name: '',
    description: '',
    useCaseType: '',
    targetCount: 1,
  });

  const isValidId = UUID_REGEX.test(projectId);

  const { data: project, isLoading: isLoadingProject } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => api.projects.get(projectId),
    enabled: isValidId,
  });

  const { data: tasksData, isLoading: isLoadingTasks } = useQuery({
    queryKey: ['tasks', { projectId }],
    queryFn: () => api.tasks.list({ projectId }),
    enabled: isValidId,
  });

  const createTaskMutation = useMutation({
    mutationFn: (data: any) => api.tasks.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks', { projectId }] });
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });
      setIsCreateTaskModalOpen(false);
      setNewTask({ name: '', description: '', useCaseType: '', targetCount: 1 });
      toast.success('タスクを作成しました');
    },
    onError: () => {
      toast.error('タスクの作成に失敗しました');
    },
  });

  const handleCreateTask = () => {
    if (!newTask.name.trim() || !newTask.useCaseType) return;
    createTaskMutation.mutate({
      name: newTask.name,
      description: newTask.description || undefined,
      projectId,
      useCaseType: newTask.useCaseType,
      targetCount: newTask.targetCount,

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

  if (!isValidId) {
    router.replace('/projects');
    return null;
  }

  if (isLoadingProject) {
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
          { label: project?.name || '...' },
        ]}
      />

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
          {project?.clientName && (
            <p className="text-surface-500 dark:text-surface-400 flex items-center gap-2">
              <Users className="w-4 h-4" />
              {project.clientName}
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
            {project?.taskCount || 0}
          </p>
        </Card>
        <Card className="p-6">
          <p className="text-sm text-surface-500 dark:text-surface-400 mb-1">完了タスク</p>
          <p className="text-2xl font-bold text-emerald-500">
            {project?.completedTaskCount || 0}
          </p>
        </Card>
        <Card className="p-6">
          <p className="text-sm text-surface-500 dark:text-surface-400 mb-1">進捗率</p>
          <p className="text-2xl font-bold text-accent-500">
            {project?.taskCount
              ? Math.round(
                  ((project?.completedTaskCount || 0) / project.taskCount) * 100
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
          <div className="p-4">
            <SkeletonListItem count={3} />
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
                    {getUseCaseLabel(task.useCaseType)}
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="text-sm text-surface-500 dark:text-surface-400">
                      {task.completedInterviewCount}/{task.interviewCount} 完了
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
          <EmptyState
            icon={ClipboardList}
            title="タスクがありません"
            description="新しいタスクを追加してインタビューを開始しましょう"
            action={{ label: '最初のタスクを作成', onClick: () => setIsCreateTaskModalOpen(true) }}
          />
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
            value={newTask.useCaseType}
            onChange={(e) =>
              setNewTask({ ...newTask, useCaseType: e.target.value })
            }
          />
          <Input
            label="目標インタビュー数"
            type="number"
            min={1}
            value={newTask.targetCount}
            onChange={(e) =>
              setNewTask({ ...newTask, targetCount: parseInt(e.target.value) || 1 })
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
            disabled={!newTask.name.trim() || !newTask.useCaseType}
          >
            作成
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
