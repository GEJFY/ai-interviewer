'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  FileText,
  Plus,
  Copy,
  Trash2,
  CheckCircle2,
  Clock,
  MoreVertical,
} from 'lucide-react';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import api from '@/lib/api-client';
import { Button, Modal, ModalBody, ModalFooter, Input, Select, toast } from '@/components/ui';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { SkeletonCard } from '@/components/ui/skeleton';
import { EmptyState } from '@/components/ui/empty-state';
import { ConfirmDialog } from '@/components/ui/confirm-dialog';

interface Template {
  id: string;
  name: string;
  description: string | null;
  use_case_type: string;
  is_published: boolean;
  version: number;
  questions: Array<{ question: string; order: number }>;
  created_at: string;
  updated_at: string;
}

const USE_CASE_LABELS: Record<string, string> = {
  compliance_survey: 'コンプライアンス意識調査',
  whistleblower_investigation: '内部通報調査',
  process_review: '業務プロセスヒアリング',
  control_evaluation: '統制評価（J-SOX）',
  risk_assessment: 'リスクアセスメント',
  board_effectiveness: '取締役会実効性評価',
  tacit_knowledge: 'ナレッジ抽出',
  hr_interview: '人事面談',
  exit_interview: '退職面談',
  incident_investigation: 'インシデント調査',
  vendor_assessment: 'ベンダー評価',
  project_review: 'プロジェクトレビュー',
};

const USE_CASE_OPTIONS = Object.entries(USE_CASE_LABELS).map(([value, label]) => ({
  value,
  label,
}));

export default function TemplatesPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [newTemplate, setNewTemplate] = useState({
    name: '',
    useCaseType: 'compliance_survey',
    description: '',
  });

  const { data, isLoading } = useQuery({
    queryKey: ['templates'],
    queryFn: () => api.templates.list(),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      api.templates.create({
        name: newTemplate.name,
        useCaseType: newTemplate.useCaseType,
        description: newTemplate.description,
        questions: [],
      }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      setIsCreateModalOpen(false);
      setNewTemplate({ name: '', useCaseType: 'compliance_survey', description: '' });
      toast.success('テンプレートを作成しました');
      router.push(`/templates/${data.id}`);
    },
    onError: () => {
      toast.error('テンプレートの作成に失敗しました');
    },
  });

  const cloneMutation = useMutation({
    mutationFn: (id: string) => api.templates.clone(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      setOpenMenuId(null);
      toast.success('テンプレートを複製しました');
    },
    onError: () => {
      toast.error('テンプレートの複製に失敗しました');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.templates.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      setIsDeleteModalOpen(false);
      setSelectedTemplate(null);
      toast.success('テンプレートを削除しました');
    },
    onError: () => {
      toast.error('テンプレートの削除に失敗しました');
    },
  });

  const handleDelete = (template: Template) => {
    setSelectedTemplate(template);
    setIsDeleteModalOpen(true);
    setOpenMenuId(null);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-surface-900 dark:text-surface-50">
            テンプレート管理
          </h1>
          <p className="text-surface-500 dark:text-surface-400 mt-1">
            インタビュー質問テンプレートを管理します
          </p>
        </div>
        <Button
          variant="accent"
          leftIcon={<Plus className="w-5 h-5" />}
          onClick={() => setIsCreateModalOpen(true)}
        >
          新規テンプレート
        </Button>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : data?.items?.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {data.items.map((template: Template) => (
            <Card key={template.id} hover className="group">
              <Link href={`/templates/${template.id}`} className="block p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-2 bg-accent-500/10 rounded-lg">
                    <FileText className="w-5 h-5 text-accent-500" />
                  </div>
                  <Badge variant={template.is_published ? 'success' : 'default'}>
                    {template.is_published ? (
                      <span className="flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" />
                        公開中
                      </span>
                    ) : (
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        下書き
                      </span>
                    )}
                  </Badge>
                </div>
                <h3 className="font-semibold text-surface-900 dark:text-surface-50 mb-1 group-hover:text-accent-500 transition-colors">
                  {template.name}
                </h3>
                <p className="text-sm text-surface-500 dark:text-surface-400 mb-3">
                  {USE_CASE_LABELS[template.use_case_type] || template.use_case_type}
                </p>
                {template.description && (
                  <p className="text-sm text-surface-500 dark:text-surface-400 line-clamp-2 mb-3">
                    {template.description}
                  </p>
                )}
                <div className="flex items-center justify-between text-sm text-surface-400">
                  <span>{template.questions?.length || 0}問</span>
                  <span>v{template.version}</span>
                </div>
              </Link>
              <div className="border-t border-surface-200 dark:border-surface-700 px-4 py-3 flex justify-between items-center">
                <span className="text-xs text-surface-400">
                  {format(new Date(template.updated_at), 'yyyy/MM/dd更新', { locale: ja })}
                </span>
                <div className="relative">
                  <button
                    onClick={(e) => {
                      e.preventDefault();
                      setOpenMenuId(openMenuId === template.id ? null : template.id);
                    }}
                    className="p-1 text-surface-400 hover:text-surface-600 dark:hover:text-surface-300 hover:bg-surface-100 dark:hover:bg-surface-800 rounded transition-colors"
                  >
                    <MoreVertical className="w-4 h-4" />
                  </button>
                  {openMenuId === template.id && (
                    <div className="absolute right-0 bottom-full mb-1 w-40 bg-white dark:bg-surface-850 rounded-lg shadow-lg border border-surface-200 dark:border-surface-700 py-1 z-10 animate-scale-in">
                      <button
                        onClick={(e) => {
                          e.preventDefault();
                          cloneMutation.mutate(template.id);
                        }}
                        className="w-full px-4 py-2 text-left text-sm text-surface-700 dark:text-surface-300 hover:bg-surface-50 dark:hover:bg-surface-800 flex items-center gap-2"
                      >
                        <Copy className="w-4 h-4" />
                        複製
                      </button>
                      <button
                        onClick={(e) => {
                          e.preventDefault();
                          handleDelete(template);
                        }}
                        className="w-full px-4 py-2 text-left text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-2"
                      >
                        <Trash2 className="w-4 h-4" />
                        削除
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <EmptyState
            icon={FileText}
            title="テンプレートがありません"
            description="最初のテンプレートを作成しましょう"
            action={{ label: 'テンプレートを作成', onClick: () => setIsCreateModalOpen(true) }}
          />
        </Card>
      )}

      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="新規テンプレート作成"
      >
        <ModalBody>
          <div className="space-y-4">
            <Input
              label="テンプレート名"
              value={newTemplate.name}
              onChange={(e) => setNewTemplate({ ...newTemplate, name: e.target.value })}
              placeholder="例：コンプライアンス意識調査 2024年版"
              required
            />
            <Select
              label="ユースケースタイプ"
              options={USE_CASE_OPTIONS}
              value={newTemplate.useCaseType}
              onChange={(e) => setNewTemplate({ ...newTemplate, useCaseType: e.target.value })}
            />
            <Input
              label="説明"
              value={newTemplate.description}
              onChange={(e) => setNewTemplate({ ...newTemplate, description: e.target.value })}
              placeholder="テンプレートの説明（任意）"
            />
          </div>
        </ModalBody>
        <ModalFooter>
          <Button variant="outline" onClick={() => setIsCreateModalOpen(false)}>
            キャンセル
          </Button>
          <Button
            variant="accent"
            onClick={() => createMutation.mutate()}
            isLoading={createMutation.isPending}
            disabled={!newTemplate.name}
          >
            作成して編集
          </Button>
        </ModalFooter>
      </Modal>

      <ConfirmDialog
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        onConfirm={() => selectedTemplate && deleteMutation.mutate(selectedTemplate.id)}
        title="テンプレートの削除"
        message={`「${selectedTemplate?.name}」を削除しますか？この操作は取り消せません。`}
        confirmLabel="削除"
        variant="danger"
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}
