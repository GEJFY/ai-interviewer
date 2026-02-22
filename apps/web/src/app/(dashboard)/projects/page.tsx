'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Plus,
  Search,
  FolderKanban,
  Calendar,
  Users,
} from 'lucide-react';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import api from '@/lib/api-client';
import { Button, Input, Modal, ModalBody, ModalFooter, toast } from '@/components/ui';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { SkeletonCard } from '@/components/ui/skeleton';
import { EmptyState } from '@/components/ui/empty-state';

interface Project {
  id: string;
  name: string;
  description: string | null;
  clientName: string | null;
  status: string;
  startDate: string | null;
  endDate: string | null;
  taskCount: number;
  completedTaskCount: number;
  createdAt: string;
}

export default function ProjectsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [newProject, setNewProject] = useState({
    name: '',
    description: '',
    clientName: '',
  });

  const { data, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.projects.list({ pageSize: 100 }),
  });

  const createMutation = useMutation({
    mutationFn: (data: { name: string; description?: string; clientName?: string }) =>
      api.projects.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setIsCreateModalOpen(false);
      setNewProject({ name: '', description: '', clientName: '' });
      toast.success('案件を作成しました');
    },
    onError: () => {
      toast.error('案件の作成に失敗しました');
    },
  });

  const filteredProjects = data?.items?.filter((project: Project) =>
    project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    project.clientName?.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  const handleCreateProject = () => {
    if (!newProject.name.trim()) return;
    createMutation.mutate({
      name: newProject.name,
      description: newProject.description || undefined,
      clientName: newProject.clientName || undefined,
    });
  };

  const statusVariant = (status: string) => {
    if (status === 'active') return 'success';
    if (status === 'completed') return 'info';
    return 'default';
  };

  const statusLabel = (status: string) => {
    const labels: Record<string, string> = { active: '進行中', completed: '完了', archived: 'アーカイブ' };
    return labels[status] || status;
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-surface-900 dark:text-surface-50">案件管理</h1>
          <p className="text-surface-500 dark:text-surface-400 mt-1">
            プロジェクトの作成と管理を行います
          </p>
        </div>
        <Button
          variant="accent"
          leftIcon={<Plus className="w-5 h-5" />}
          onClick={() => setIsCreateModalOpen(true)}
        >
          新規案件作成
        </Button>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-surface-400" />
        <input
          type="text"
          placeholder="案件名またはクライアント名で検索..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 bg-white dark:bg-surface-800 border border-surface-300 dark:border-surface-600 rounded-lg text-surface-900 dark:text-surface-100 placeholder:text-surface-400 focus:outline-none focus:ring-2 focus:ring-accent-500/50 focus:border-accent-500 transition-all"
        />
      </div>

      {/* Projects Grid */}
      {isLoading ? (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : filteredProjects.length > 0 ? (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProjects.map((project: Project) => (
            <Link key={project.id} href={`/projects/${project.id}`}>
              <Card hover className="p-6 h-full group">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-2 bg-accent-500/10 rounded-lg">
                    <FolderKanban className="w-6 h-6 text-accent-500" />
                  </div>
                  <Badge variant={statusVariant(project.status)}>
                    {statusLabel(project.status)}
                  </Badge>
                </div>

                <h3 className="text-lg font-semibold text-surface-900 dark:text-surface-50 mb-2 group-hover:text-accent-500 transition-colors">
                  {project.name}
                </h3>

                {project.clientName && (
                  <p className="text-sm text-surface-500 dark:text-surface-400 mb-3 flex items-center gap-1">
                    <Users className="w-4 h-4" />
                    {project.clientName}
                  </p>
                )}

                {project.description && (
                  <p className="text-sm text-surface-500 dark:text-surface-400 mb-4 line-clamp-2">
                    {project.description}
                  </p>
                )}

                <div className="flex items-center justify-between text-sm text-surface-400">
                  <span>
                    {project.completedTaskCount}/{project.taskCount} タスク完了
                  </span>
                  {project.startDate && (
                    <span className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      {format(new Date(project.startDate), 'M/d', { locale: ja })}
                    </span>
                  )}
                </div>

                {project.taskCount > 0 && (
                  <div className="mt-4 h-1.5 bg-surface-200 dark:bg-surface-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-accent-400 to-accent-500 rounded-full transition-all"
                      style={{
                        width: `${(project.completedTaskCount / project.taskCount) * 100}%`,
                      }}
                    />
                  </div>
                )}
              </Card>
            </Link>
          ))}
        </div>
      ) : (
        <Card>
          <EmptyState
            icon={FolderKanban}
            title={searchQuery ? '検索結果がありません' : '案件がありません'}
            description={searchQuery ? '別のキーワードで検索してください' : '新しい案件を作成して始めましょう'}
            variant={searchQuery ? 'search' : 'default'}
            action={!searchQuery ? { label: '最初の案件を作成', onClick: () => setIsCreateModalOpen(true) } : undefined}
          />
        </Card>
      )}

      {/* Create Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="新規案件作成"
        size="md"
      >
        <ModalBody className="space-y-4">
          <Input
            label="案件名"
            placeholder="例：2025年度 内部監査"
            value={newProject.name}
            onChange={(e) =>
              setNewProject({ ...newProject, name: e.target.value })
            }
            error={createMutation.isError ? '案件名を入力してください' : undefined}
          />
          <Input
            label="クライアント名"
            placeholder="例：株式会社〇〇"
            value={newProject.clientName}
            onChange={(e) =>
              setNewProject({ ...newProject, clientName: e.target.value })
            }
          />
          <div>
            <label className="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-2">
              説明
            </label>
            <textarea
              placeholder="案件の概要を入力..."
              value={newProject.description}
              onChange={(e) =>
                setNewProject({ ...newProject, description: e.target.value })
              }
              rows={3}
              className="w-full px-4 py-2.5 bg-white dark:bg-surface-800 border border-surface-300 dark:border-surface-600 rounded-lg text-surface-900 dark:text-surface-100 placeholder:text-surface-400 focus:outline-none focus:ring-2 focus:ring-accent-500/50 focus:border-accent-500 resize-none transition-all"
            />
          </div>
        </ModalBody>
        <ModalFooter>
          <Button variant="outline" onClick={() => setIsCreateModalOpen(false)}>
            キャンセル
          </Button>
          <Button
            variant="accent"
            onClick={handleCreateProject}
            isLoading={createMutation.isPending}
            disabled={!newProject.name.trim()}
          >
            作成
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
