'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import {
  ArrowLeft,
  Plus,
  ClipboardList,
  MessageSquare,
  Edit2,
  Trash2,
  Calendar,
  Users,
  MoreVertical,
} from 'lucide-react';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import api from '@/lib/api-client';
import { Button, Input, Select, Modal, ModalBody, ModalFooter } from '@/components/ui';

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

  const getUseCaseLabel = (type: string) => {
    return USE_CASE_OPTIONS.find((opt) => opt.value === type)?.label || type;
  };

  if (isLoadingProject) {
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
        href="/projects"
        className="inline-flex items-center gap-2 text-secondary-600 hover:text-secondary-900 transition"
      >
        <ArrowLeft className="w-4 h-4" />
        案件一覧に戻る
      </Link>

      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-bold text-secondary-900">
              {project?.name}
            </h1>
            <span
              className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                project?.status === 'active'
                  ? 'bg-green-100 text-green-700'
                  : 'bg-secondary-100 text-secondary-700'
              }`}
            >
              {project?.status === 'active' ? '進行中' : project?.status}
            </span>
          </div>
          {project?.client_name && (
            <p className="text-secondary-600 flex items-center gap-2">
              <Users className="w-4 h-4" />
              {project.client_name}
            </p>
          )}
          {project?.description && (
            <p className="text-secondary-600 mt-2">{project.description}</p>
          )}
        </div>
        <div className="flex gap-3">
          <Button variant="outline" leftIcon={<Edit2 className="w-4 h-4" />}>
            編集
          </Button>
          <Button
            leftIcon={<Plus className="w-5 h-5" />}
            onClick={() => setIsCreateTaskModalOpen(true)}
          >
            タスク追加
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-6">
        <div className="bg-white rounded-xl border border-secondary-200 p-6">
          <p className="text-sm text-secondary-500 mb-1">タスク数</p>
          <p className="text-2xl font-bold text-secondary-900">
            {project?.task_count || 0}
          </p>
        </div>
        <div className="bg-white rounded-xl border border-secondary-200 p-6">
          <p className="text-sm text-secondary-500 mb-1">完了タスク</p>
          <p className="text-2xl font-bold text-green-600">
            {project?.completed_task_count || 0}
          </p>
        </div>
        <div className="bg-white rounded-xl border border-secondary-200 p-6">
          <p className="text-sm text-secondary-500 mb-1">進捗率</p>
          <p className="text-2xl font-bold text-primary-600">
            {project?.task_count
              ? Math.round(
                  ((project?.completed_task_count || 0) / project.task_count) * 100
                )
              : 0}
            %
          </p>
        </div>
      </div>

      {/* Tasks */}
      <div className="bg-white rounded-xl border border-secondary-200">
        <div className="px-6 py-4 border-b border-secondary-200">
          <h2 className="font-semibold text-secondary-900">タスク一覧</h2>
        </div>

        {isLoadingTasks ? (
          <div className="p-6">
            <div className="animate-pulse space-y-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-16 bg-secondary-100 rounded" />
              ))}
            </div>
          </div>
        ) : tasksData?.items?.length > 0 ? (
          <div className="divide-y divide-secondary-100">
            {tasksData.items.map((task: Task) => (
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
                    {getUseCaseLabel(task.use_case_type)}
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="text-sm text-secondary-600">
                      {task.completed_interview_count}/{task.interview_count} 完了
                    </p>
                    {task.deadline && (
                      <p className="text-xs text-secondary-400 flex items-center gap-1 justify-end">
                        <Calendar className="w-3 h-3" />
                        {format(new Date(task.deadline), 'M/d', { locale: ja })}
                      </p>
                    )}
                  </div>
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
            <p className="text-secondary-500 mb-6">
              新しいタスクを追加してインタビューを開始しましょう
            </p>
            <Button onClick={() => setIsCreateTaskModalOpen(true)}>
              最初のタスクを作成
            </Button>
          </div>
        )}
      </div>

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
            <label className="block text-sm font-medium text-secondary-700 mb-2">
              説明
            </label>
            <textarea
              placeholder="タスクの概要を入力..."
              value={newTask.description}
              onChange={(e) =>
                setNewTask({ ...newTask, description: e.target.value })
              }
              rows={3}
              className="w-full px-4 py-2.5 border border-secondary-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
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
