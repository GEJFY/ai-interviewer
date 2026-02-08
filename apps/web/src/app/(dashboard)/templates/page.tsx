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
import { Button, Modal, ModalBody, ModalFooter, Input, Select } from '@/components/ui';

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
      router.push(`/templates/${data.id}`);
    },
  });

  const cloneMutation = useMutation({
    mutationFn: (id: string) => api.templates.clone(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      setOpenMenuId(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.templates.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      setIsDeleteModalOpen(false);
      setSelectedTemplate(null);
    },
  });

  const handleDelete = (template: Template) => {
    setSelectedTemplate(template);
    setIsDeleteModalOpen(true);
    setOpenMenuId(null);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">
            テンプレート管理
          </h1>
          <p className="text-secondary-600 mt-1">
            インタビュー質問テンプレートを管理します
          </p>
        </div>
        <Button
          leftIcon={<Plus className="w-5 h-5" />}
          onClick={() => setIsCreateModalOpen(true)}
        >
          新規テンプレート
        </Button>
      </div>

      {/* Templates Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className="bg-white rounded-xl border border-secondary-200 p-6 animate-pulse"
            >
              <div className="h-6 bg-secondary-200 rounded w-3/4 mb-4" />
              <div className="h-4 bg-secondary-200 rounded w-1/2 mb-2" />
              <div className="h-4 bg-secondary-200 rounded w-full" />
            </div>
          ))}
        </div>
      ) : data?.items?.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {data.items.map((template: Template) => (
            <div
              key={template.id}
              className="bg-white rounded-xl border border-secondary-200 hover:border-primary-300 hover:shadow-md transition group"
            >
              <Link href={`/templates/${template.id}`} className="block p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-2 bg-primary-100 rounded-lg">
                    <FileText className="w-5 h-5 text-primary-600" />
                  </div>
                  <div className="flex items-center gap-2">
                    {template.is_published ? (
                      <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-700">
                        <CheckCircle2 className="w-3 h-3" />
                        公開中
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-secondary-100 text-secondary-600">
                        <Clock className="w-3 h-3" />
                        下書き
                      </span>
                    )}
                  </div>
                </div>
                <h3 className="font-semibold text-secondary-900 mb-1">
                  {template.name}
                </h3>
                <p className="text-sm text-secondary-500 mb-3">
                  {USE_CASE_LABELS[template.use_case_type] || template.use_case_type}
                </p>
                {template.description && (
                  <p className="text-sm text-secondary-600 line-clamp-2 mb-3">
                    {template.description}
                  </p>
                )}
                <div className="flex items-center justify-between text-sm text-secondary-500">
                  <span>{template.questions?.length || 0}問</span>
                  <span>v{template.version}</span>
                </div>
              </Link>
              <div className="border-t border-secondary-100 px-4 py-3 flex justify-between items-center">
                <span className="text-xs text-secondary-500">
                  {format(new Date(template.updated_at), 'yyyy/MM/dd更新', {
                    locale: ja,
                  })}
                </span>
                <div className="relative">
                  <button
                    onClick={(e) => {
                      e.preventDefault();
                      setOpenMenuId(openMenuId === template.id ? null : template.id);
                    }}
                    className="p-1 text-secondary-400 hover:text-secondary-600 hover:bg-secondary-100 rounded"
                  >
                    <MoreVertical className="w-4 h-4" />
                  </button>
                  {openMenuId === template.id && (
                    <div className="absolute right-0 bottom-full mb-1 w-40 bg-white rounded-lg shadow-lg border border-secondary-200 py-1 z-10">
                      <button
                        onClick={(e) => {
                          e.preventDefault();
                          cloneMutation.mutate(template.id);
                        }}
                        className="w-full px-4 py-2 text-left text-sm text-secondary-700 hover:bg-secondary-50 flex items-center gap-2"
                      >
                        <Copy className="w-4 h-4" />
                        複製
                      </button>
                      <button
                        onClick={(e) => {
                          e.preventDefault();
                          handleDelete(template);
                        }}
                        className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                      >
                        <Trash2 className="w-4 h-4" />
                        削除
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-secondary-200 p-12 text-center">
          <FileText className="w-12 h-12 text-secondary-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-secondary-900 mb-2">
            テンプレートがありません
          </h3>
          <p className="text-secondary-500 mb-6">
            最初のテンプレートを作成しましょう
          </p>
          <Button onClick={() => setIsCreateModalOpen(true)}>
            テンプレートを作成
          </Button>
        </div>
      )}

      {/* Create Template Modal */}
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
              onChange={(e) =>
                setNewTemplate({ ...newTemplate, name: e.target.value })
              }
              placeholder="例：コンプライアンス意識調査 2024年版"
              required
            />
            <Select
              label="ユースケースタイプ"
              options={USE_CASE_OPTIONS}
              value={newTemplate.useCaseType}
              onChange={(e) =>
                setNewTemplate({ ...newTemplate, useCaseType: e.target.value })
              }
            />
            <Input
              label="説明"
              value={newTemplate.description}
              onChange={(e) =>
                setNewTemplate({ ...newTemplate, description: e.target.value })
              }
              placeholder="テンプレートの説明（任意）"
            />
          </div>
        </ModalBody>
        <ModalFooter>
          <Button variant="outline" onClick={() => setIsCreateModalOpen(false)}>
            キャンセル
          </Button>
          <Button
            onClick={() => createMutation.mutate()}
            isLoading={createMutation.isPending}
            disabled={!newTemplate.name}
          >
            作成して編集
          </Button>
        </ModalFooter>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        title="テンプレートの削除"
        size="sm"
      >
        <ModalBody>
          <p className="text-secondary-600">
            「{selectedTemplate?.name}」を削除しますか？
            この操作は取り消せません。
          </p>
        </ModalBody>
        <ModalFooter>
          <Button variant="outline" onClick={() => setIsDeleteModalOpen(false)}>
            キャンセル
          </Button>
          <Button
            variant="outline"
            className="text-red-600 border-red-300 hover:bg-red-50"
            onClick={() => selectedTemplate && deleteMutation.mutate(selectedTemplate.id)}
            isLoading={deleteMutation.isPending}
          >
            削除
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
