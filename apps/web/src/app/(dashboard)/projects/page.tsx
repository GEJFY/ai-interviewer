'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Plus,
  Search,
  FolderKanban,
  MoreVertical,
  Calendar,
  Users,
} from 'lucide-react';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import api from '@/lib/api-client';
import { Button, Input, Modal, ModalBody, ModalFooter } from '@/components/ui';

interface Project {
  id: string;
  name: string;
  description: string | null;
  client_name: string | null;
  status: string;
  start_date: string | null;
  end_date: string | null;
  task_count: number;
  completed_task_count: number;
  created_at: string;
}

export default function ProjectsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [newProject, setNewProject] = useState({
    name: '',
    description: '',
    client_name: '',
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
      setNewProject({ name: '', description: '', client_name: '' });
    },
  });

  const filteredProjects = data?.items?.filter((project: Project) =>
    project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    project.client_name?.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  const handleCreateProject = () => {
    if (!newProject.name.trim()) return;
    createMutation.mutate({
      name: newProject.name,
      description: newProject.description || undefined,
      clientName: newProject.client_name || undefined,
    });
  };

  const getStatusBadge = (status: string) => {
    const styles = {
      active: 'bg-green-100 text-green-700',
      completed: 'bg-blue-100 text-blue-700',
      archived: 'bg-secondary-100 text-secondary-700',
    };
    const labels = {
      active: '進行中',
      completed: '完了',
      archived: 'アーカイブ',
    };
    return (
      <span
        className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
          styles[status as keyof typeof styles] || styles.active
        }`}
      >
        {labels[status as keyof typeof labels] || status}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">案件管理</h1>
          <p className="text-secondary-600 mt-1">
            プロジェクトの作成と管理を行います
          </p>
        </div>
        <Button
          leftIcon={<Plus className="w-5 h-5" />}
          onClick={() => setIsCreateModalOpen(true)}
        >
          新規案件作成
        </Button>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-secondary-400" />
        <input
          type="text"
          placeholder="案件名またはクライアント名で検索..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 border border-secondary-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        />
      </div>

      {/* Projects Grid */}
      {isLoading ? (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className="bg-white rounded-xl border border-secondary-200 p-6 animate-pulse"
            >
              <div className="h-6 bg-secondary-200 rounded w-3/4 mb-4" />
              <div className="h-4 bg-secondary-200 rounded w-1/2 mb-2" />
              <div className="h-4 bg-secondary-200 rounded w-1/3" />
            </div>
          ))}
        </div>
      ) : filteredProjects.length > 0 ? (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProjects.map((project: Project) => (
            <Link
              key={project.id}
              href={`/projects/${project.id}`}
              className="bg-white rounded-xl border border-secondary-200 p-6 hover:border-primary-300 hover:shadow-md transition group"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="p-2 bg-primary-100 rounded-lg">
                  <FolderKanban className="w-6 h-6 text-primary-600" />
                </div>
                {getStatusBadge(project.status)}
              </div>

              <h3 className="text-lg font-semibold text-secondary-900 mb-2 group-hover:text-primary-600 transition">
                {project.name}
              </h3>

              {project.client_name && (
                <p className="text-sm text-secondary-500 mb-3 flex items-center gap-1">
                  <Users className="w-4 h-4" />
                  {project.client_name}
                </p>
              )}

              {project.description && (
                <p className="text-sm text-secondary-600 mb-4 line-clamp-2">
                  {project.description}
                </p>
              )}

              <div className="flex items-center justify-between text-sm text-secondary-500">
                <span>
                  {project.completed_task_count}/{project.task_count} タスク完了
                </span>
                {project.start_date && (
                  <span className="flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    {format(new Date(project.start_date), 'M/d', { locale: ja })}
                  </span>
                )}
              </div>

              {/* Progress bar */}
              {project.task_count > 0 && (
                <div className="mt-4 h-2 bg-secondary-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary-500 rounded-full transition-all"
                    style={{
                      width: `${
                        (project.completed_task_count / project.task_count) * 100
                      }%`,
                    }}
                  />
                </div>
              )}
            </Link>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-secondary-200 p-12 text-center">
          <FolderKanban className="w-12 h-12 text-secondary-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-secondary-900 mb-2">
            {searchQuery ? '検索結果がありません' : '案件がありません'}
          </h3>
          <p className="text-secondary-500 mb-6">
            {searchQuery
              ? '別のキーワードで検索してください'
              : '新しい案件を作成して始めましょう'}
          </p>
          {!searchQuery && (
            <Button onClick={() => setIsCreateModalOpen(true)}>
              最初の案件を作成
            </Button>
          )}
        </div>
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
            value={newProject.client_name}
            onChange={(e) =>
              setNewProject({ ...newProject, client_name: e.target.value })
            }
          />
          <div>
            <label className="block text-sm font-medium text-secondary-700 mb-2">
              説明
            </label>
            <textarea
              placeholder="案件の概要を入力..."
              value={newProject.description}
              onChange={(e) =>
                setNewProject({ ...newProject, description: e.target.value })
              }
              rows={3}
              className="w-full px-4 py-2.5 border border-secondary-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
            />
          </div>
        </ModalBody>
        <ModalFooter>
          <Button
            variant="outline"
            onClick={() => setIsCreateModalOpen(false)}
          >
            キャンセル
          </Button>
          <Button
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
