'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import {
  ArrowLeft,
  Save,
  Upload,
  Plus,
  Trash2,
  GripVertical,
  ChevronDown,
  ChevronUp,
  AlertCircle,
} from 'lucide-react';
import api from '@/lib/api-client';
import { Button, Input, Modal, ModalBody, ModalFooter } from '@/components/ui';

interface Question {
  id: string;
  question: string;
  order: number;
  followUps: string[];
  required: boolean;
}

interface Template {
  id: string;
  name: string;
  description: string | null;
  use_case_type: string;
  is_published: boolean;
  version: number;
  questions: Question[];
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
};

export default function TemplateDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const templateId = params.id as string;

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [questions, setQuestions] = useState<Question[]>([]);
  const [expandedQuestionId, setExpandedQuestionId] = useState<string | null>(null);
  const [isPublishModalOpen, setIsPublishModalOpen] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);

  const { data: template, isLoading } = useQuery({
    queryKey: ['template', templateId],
    queryFn: () => api.templates.get(templateId),
  });

  useEffect(() => {
    if (template) {
      setName(template.name);
      setDescription(template.description || '');
      const loadedQuestions = (template.questions || []).map(
        (q: Partial<Question>, index: number) => ({
          id: q.id || `q-${Date.now()}-${index}`,
          question: q.question || '',
          order: q.order ?? index,
          followUps: q.followUps || [],
          required: q.required ?? true,
        })
      );
      setQuestions(loadedQuestions);
    }
  }, [template]);

  const updateMutation = useMutation({
    mutationFn: () =>
      api.templates.update(templateId, {
        name,
        description,
        questions: questions.map((q, index) => ({
          question: q.question,
          order: index,
          followUps: q.followUps,
          required: q.required,
        })),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['template', templateId] });
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      setHasChanges(false);
    },
  });

  const publishMutation = useMutation({
    mutationFn: () => api.templates.publish(templateId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['template', templateId] });
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      setIsPublishModalOpen(false);
    },
  });

  const handleChange = () => {
    setHasChanges(true);
  };

  const addQuestion = () => {
    const newQuestion: Question = {
      id: `q-${Date.now()}`,
      question: '',
      order: questions.length,
      followUps: [],
      required: true,
    };
    setQuestions([...questions, newQuestion]);
    setExpandedQuestionId(newQuestion.id);
    handleChange();
  };

  const updateQuestion = (id: string, updates: Partial<Question>) => {
    setQuestions(
      questions.map((q) => (q.id === id ? { ...q, ...updates } : q))
    );
    handleChange();
  };

  const deleteQuestion = (id: string) => {
    setQuestions(questions.filter((q) => q.id !== id));
    handleChange();
  };

  const addFollowUp = (questionId: string) => {
    setQuestions(
      questions.map((q) =>
        q.id === questionId
          ? { ...q, followUps: [...q.followUps, ''] }
          : q
      )
    );
    handleChange();
  };

  const updateFollowUp = (questionId: string, index: number, value: string) => {
    setQuestions(
      questions.map((q) =>
        q.id === questionId
          ? {
              ...q,
              followUps: q.followUps.map((f, i) => (i === index ? value : f)),
            }
          : q
      )
    );
    handleChange();
  };

  const deleteFollowUp = (questionId: string, index: number) => {
    setQuestions(
      questions.map((q) =>
        q.id === questionId
          ? { ...q, followUps: q.followUps.filter((_, i) => i !== index) }
          : q
      )
    );
    handleChange();
  };

  const moveQuestion = (fromIndex: number, toIndex: number) => {
    if (toIndex < 0 || toIndex >= questions.length) return;
    const newQuestions = [...questions];
    const [moved] = newQuestions.splice(fromIndex, 1);
    newQuestions.splice(toIndex, 0, moved);
    setQuestions(newQuestions);
    handleChange();
  };

  const handleDragStart = (index: number) => {
    setDraggedIndex(index);
  };

  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault();
    if (draggedIndex !== null && draggedIndex !== index) {
      moveQuestion(draggedIndex, index);
      setDraggedIndex(index);
    }
  };

  const handleDragEnd = () => {
    setDraggedIndex(null);
  };

  if (isLoading) {
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
        href="/templates"
        className="inline-flex items-center gap-2 text-secondary-600 hover:text-secondary-900 transition"
      >
        <ArrowLeft className="w-4 h-4" />
        テンプレート一覧に戻る
      </Link>

      {/* Header */}
      <div className="flex justify-between items-start">
        <div className="flex-1 max-w-2xl">
          <div className="flex items-center gap-3 mb-2">
            <input
              type="text"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                handleChange();
              }}
              className="text-2xl font-bold text-secondary-900 bg-transparent border-none outline-none focus:ring-0 w-full"
              placeholder="テンプレート名"
            />
            {template?.is_published ? (
              <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-700">
                公開中
              </span>
            ) : (
              <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-secondary-100 text-secondary-600">
                下書き
              </span>
            )}
          </div>
          <p className="text-sm text-secondary-500 mb-2">
            {USE_CASE_LABELS[template?.use_case_type] || template?.use_case_type} ・
            v{template?.version}
          </p>
          <input
            type="text"
            value={description}
            onChange={(e) => {
              setDescription(e.target.value);
              handleChange();
            }}
            className="text-secondary-600 bg-transparent border-none outline-none focus:ring-0 w-full"
            placeholder="テンプレートの説明を入力..."
          />
        </div>
        <div className="flex gap-3">
          {!template?.is_published && (
            <Button
              variant="outline"
              leftIcon={<Upload className="w-4 h-4" />}
              onClick={() => setIsPublishModalOpen(true)}
              disabled={questions.length === 0}
            >
              公開
            </Button>
          )}
          <Button
            leftIcon={<Save className="w-4 h-4" />}
            onClick={() => updateMutation.mutate()}
            isLoading={updateMutation.isPending}
            disabled={!hasChanges}
          >
            保存
          </Button>
        </div>
      </div>

      {/* Unsaved changes warning */}
      {hasChanges && (
        <div className="flex items-center gap-2 px-4 py-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-700">
          <AlertCircle className="w-4 h-4" />
          <span className="text-sm">未保存の変更があります</span>
        </div>
      )}

      {/* Questions Builder */}
      <div className="bg-white rounded-xl border border-secondary-200">
        <div className="px-6 py-4 border-b border-secondary-200 flex justify-between items-center">
          <h2 className="font-semibold text-secondary-900">
            質問リスト ({questions.length}問)
          </h2>
          <Button size="sm" leftIcon={<Plus className="w-4 h-4" />} onClick={addQuestion}>
            質問を追加
          </Button>
        </div>

        {questions.length > 0 ? (
          <div className="divide-y divide-secondary-100">
            {questions.map((question, index) => (
              <div
                key={question.id}
                draggable
                onDragStart={() => handleDragStart(index)}
                onDragOver={(e) => handleDragOver(e, index)}
                onDragEnd={handleDragEnd}
                className={`px-6 py-4 ${
                  draggedIndex === index ? 'bg-primary-50' : 'bg-white'
                }`}
              >
                <div className="flex items-start gap-4">
                  <div className="flex items-center gap-2 pt-2">
                    <button
                      className="cursor-grab text-secondary-400 hover:text-secondary-600"
                      title="ドラッグで並び替え"
                    >
                      <GripVertical className="w-5 h-5" />
                    </button>
                    <span className="w-8 h-8 flex items-center justify-center bg-primary-100 text-primary-700 rounded-full text-sm font-medium">
                      {index + 1}
                    </span>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-start gap-4">
                      <textarea
                        value={question.question}
                        onChange={(e) =>
                          updateQuestion(question.id, { question: e.target.value })
                        }
                        placeholder="質問を入力..."
                        rows={2}
                        className="flex-1 px-4 py-2 border border-secondary-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                      />
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => moveQuestion(index, index - 1)}
                          disabled={index === 0}
                          className="p-1 text-secondary-400 hover:text-secondary-600 disabled:opacity-30"
                          title="上へ移動"
                        >
                          <ChevronUp className="w-5 h-5" />
                        </button>
                        <button
                          onClick={() => moveQuestion(index, index + 1)}
                          disabled={index === questions.length - 1}
                          className="p-1 text-secondary-400 hover:text-secondary-600 disabled:opacity-30"
                          title="下へ移動"
                        >
                          <ChevronDown className="w-5 h-5" />
                        </button>
                        <button
                          onClick={() => deleteQuestion(question.id)}
                          className="p-1 text-red-400 hover:text-red-600"
                          title="削除"
                        >
                          <Trash2 className="w-5 h-5" />
                        </button>
                      </div>
                    </div>

                    {/* Options */}
                    <div className="mt-3 flex items-center gap-4">
                      <label className="flex items-center gap-2 text-sm text-secondary-600">
                        <input
                          type="checkbox"
                          checked={question.required}
                          onChange={(e) =>
                            updateQuestion(question.id, { required: e.target.checked })
                          }
                          className="rounded border-secondary-300 text-primary-600 focus:ring-primary-500"
                        />
                        必須質問
                      </label>
                      <button
                        onClick={() =>
                          setExpandedQuestionId(
                            expandedQuestionId === question.id ? null : question.id
                          )
                        }
                        className="text-sm text-primary-600 hover:text-primary-700"
                      >
                        フォローアップ質問 ({question.followUps.length})
                      </button>
                    </div>

                    {/* Follow-up questions */}
                    {expandedQuestionId === question.id && (
                      <div className="mt-4 pl-4 border-l-2 border-secondary-200 space-y-3">
                        <p className="text-sm text-secondary-500">
                          回答内容に応じて追加で聞く質問
                        </p>
                        {question.followUps.map((followUp, fIndex) => (
                          <div key={fIndex} className="flex items-center gap-2">
                            <span className="text-secondary-400 text-sm">└</span>
                            <input
                              type="text"
                              value={followUp}
                              onChange={(e) =>
                                updateFollowUp(question.id, fIndex, e.target.value)
                              }
                              placeholder="フォローアップ質問を入力..."
                              className="flex-1 px-3 py-1.5 text-sm border border-secondary-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                            />
                            <button
                              onClick={() => deleteFollowUp(question.id, fIndex)}
                              className="p-1 text-red-400 hover:text-red-600"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        ))}
                        <button
                          onClick={() => addFollowUp(question.id)}
                          className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
                        >
                          <Plus className="w-4 h-4" />
                          フォローアップを追加
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-12 text-center">
            <div className="w-12 h-12 bg-secondary-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Plus className="w-6 h-6 text-secondary-400" />
            </div>
            <h3 className="text-lg font-medium text-secondary-900 mb-2">
              質問がありません
            </h3>
            <p className="text-secondary-500 mb-6">
              「質問を追加」ボタンで質問を追加してください
            </p>
            <Button onClick={addQuestion}>最初の質問を追加</Button>
          </div>
        )}
      </div>

      {/* Publish Modal */}
      <Modal
        isOpen={isPublishModalOpen}
        onClose={() => setIsPublishModalOpen(false)}
        title="テンプレートを公開"
        size="sm"
      >
        <ModalBody>
          <p className="text-secondary-600">
            このテンプレートを公開すると、タスク作成時に選択できるようになります。
            公開後も編集は可能ですが、バージョン番号が更新されます。
          </p>
        </ModalBody>
        <ModalFooter>
          <Button variant="outline" onClick={() => setIsPublishModalOpen(false)}>
            キャンセル
          </Button>
          <Button
            onClick={() => publishMutation.mutate()}
            isLoading={publishMutation.isPending}
          >
            公開する
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
