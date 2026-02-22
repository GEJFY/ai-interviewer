'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Save,
  Upload,
  Plus,
  Trash2,
  GripVertical,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Settings2,
} from 'lucide-react';
import api from '@/lib/api-client';
import { USE_CASE_LABELS } from '@/lib/constants';
import { Button, Input, Modal, ModalBody, ModalFooter, Tooltip, toast } from '@/components/ui';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Breadcrumb } from '@/components/ui/breadcrumb';

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
  useCaseType: string;
  isPublished: boolean;
  version: number;
  questions: Question[];
  createdAt: string;
  updatedAt: string;
}

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
  const [isAiSettingsOpen, setIsAiSettingsOpen] = useState(false);
  const [aiSettings, setAiSettings] = useState({
    temperature: 0.7,
    maxQuestions: 10,
    timeLimitMinutes: 30,
    tone: 'formal',
    followUpDepth: 2,
  });

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
      toast.success('テンプレートを保存しました');
    },
    onError: () => {
      toast.error('テンプレートの保存に失敗しました');
    },
  });

  const publishMutation = useMutation({
    mutationFn: () => api.templates.publish(templateId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['template', templateId] });
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      setIsPublishModalOpen(false);
      toast.success('テンプレートを公開しました');
    },
    onError: () => {
      toast.error('テンプレートの公開に失敗しました');
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
          { label: 'テンプレート', href: '/templates' },
          { label: template?.name || '...' },
        ]}
      />

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
              className="text-2xl font-bold text-surface-900 dark:text-surface-50 bg-transparent border-none outline-none focus:ring-0 w-full"
              placeholder="テンプレート名"
            />
            <Badge variant={template?.isPublished ? 'success' : 'default'}>
              {template?.isPublished ? '公開中' : '下書き'}
            </Badge>
          </div>
          <p className="text-sm text-surface-500 dark:text-surface-400 mb-2">
            {USE_CASE_LABELS[template?.useCaseType] || template?.useCaseType} ・
            v{template?.version}
          </p>
          <input
            type="text"
            value={description}
            onChange={(e) => {
              setDescription(e.target.value);
              handleChange();
            }}
            className="text-surface-500 dark:text-surface-400 bg-transparent border-none outline-none focus:ring-0 w-full"
            placeholder="テンプレートの説明を入力..."
          />
        </div>
        <div className="flex gap-3">
          {!template?.isPublished && (
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
            variant="accent"
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
        <div className="flex items-center gap-2 px-4 py-3 bg-amber-500/10 border border-amber-500/30 rounded-lg text-amber-600 dark:text-amber-400">
          <AlertCircle className="w-4 h-4" />
          <span className="text-sm">未保存の変更があります</span>
        </div>
      )}

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
            <p className="text-sm text-surface-500 dark:text-surface-400 pt-4 mb-4">
              このテンプレートを使用したインタビューのデフォルト設定です。タスク側で個別に上書きできます。
            </p>
            <div className="grid grid-cols-2 gap-6">
              <div>
                <Tooltip content="AIの応答の多様性を制御します。低いほど定型的、高いほど創造的" position="top">
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
                    onChange={(e) => { setAiSettings({ ...aiSettings, temperature: parseFloat(e.target.value) }); handleChange(); }}
                    className="flex-1 accent-accent-500"
                  />
                  <span className="text-sm font-medium text-surface-700 dark:text-surface-300 w-8 text-right">{aiSettings.temperature}</span>
                </div>
              </div>
              <div>
                <Tooltip content="1回のインタビューでの最大質問数" position="top">
                  <label className="inline-block text-sm font-medium text-surface-700 dark:text-surface-300 mb-2 cursor-help border-b border-dashed border-surface-300 dark:border-surface-600">
                    最大質問数
                  </label>
                </Tooltip>
                <input
                  type="number"
                  min="3"
                  max="30"
                  value={aiSettings.maxQuestions}
                  onChange={(e) => { setAiSettings({ ...aiSettings, maxQuestions: parseInt(e.target.value) || 10 }); handleChange(); }}
                  className="w-full px-4 py-2 bg-white dark:bg-surface-800 border border-surface-200 dark:border-surface-700 rounded-lg text-surface-900 dark:text-surface-100 focus:outline-none focus:ring-2 focus:ring-accent-500/50"
                />
              </div>
              <div>
                <Tooltip content="AIインタビュアーの対話スタイル" position="top">
                  <label className="inline-block text-sm font-medium text-surface-700 dark:text-surface-300 mb-2 cursor-help border-b border-dashed border-surface-300 dark:border-surface-600">
                    トーン
                  </label>
                </Tooltip>
                <select
                  value={aiSettings.tone}
                  onChange={(e) => { setAiSettings({ ...aiSettings, tone: e.target.value }); handleChange(); }}
                  className="w-full px-4 py-2 bg-white dark:bg-surface-800 border border-surface-200 dark:border-surface-700 rounded-lg text-surface-900 dark:text-surface-100 focus:outline-none focus:ring-2 focus:ring-accent-500/50"
                >
                  <option value="formal">フォーマル（丁寧語・敬語）</option>
                  <option value="casual">カジュアル（ですます調）</option>
                  <option value="professional">プロフェッショナル（専門的）</option>
                </select>
              </div>
              <div>
                <Tooltip content="深掘り質問を行う回数の上限" position="top">
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
                    onChange={(e) => { setAiSettings({ ...aiSettings, followUpDepth: parseInt(e.target.value) }); handleChange(); }}
                    className="flex-1 accent-accent-500"
                  />
                  <span className="text-sm font-medium text-surface-700 dark:text-surface-300 w-16 text-right">
                    {aiSettings.followUpDepth === 0 ? 'なし' : `${aiSettings.followUpDepth}回`}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* Questions Builder */}
      <Card>
        <div className="px-6 py-4 border-b border-surface-200 dark:border-surface-700 flex justify-between items-center">
          <h2 className="font-semibold text-surface-900 dark:text-surface-50">
            質問リスト ({questions.length}問)
          </h2>
          <Button size="sm" variant="accent" leftIcon={<Plus className="w-4 h-4" />} onClick={addQuestion}>
            質問を追加
          </Button>
        </div>

        {questions.length > 0 ? (
          <div className="divide-y divide-surface-100 dark:divide-surface-800">
            {questions.map((question, index) => (
              <div
                key={question.id}
                draggable
                onDragStart={() => handleDragStart(index)}
                onDragOver={(e) => handleDragOver(e, index)}
                onDragEnd={handleDragEnd}
                className={`px-6 py-4 ${
                  draggedIndex === index ? 'bg-accent-500/5 dark:bg-accent-500/10' : ''
                }`}
              >
                <div className="flex items-start gap-4">
                  <div className="flex items-center gap-2 pt-2">
                    <button
                      className="cursor-grab text-surface-400 hover:text-surface-600 dark:hover:text-surface-300"
                      title="ドラッグで並び替え"
                    >
                      <GripVertical className="w-5 h-5" />
                    </button>
                    <span className="w-8 h-8 flex items-center justify-center bg-accent-500/10 text-accent-600 dark:text-accent-400 rounded-full text-sm font-medium">
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
                        className="flex-1 px-4 py-2 bg-white dark:bg-surface-800 border border-surface-200 dark:border-surface-700 rounded-lg text-surface-900 dark:text-surface-100 placeholder:text-surface-400 focus:outline-none focus:ring-2 focus:ring-accent-500/50 focus:border-accent-500 resize-none transition-all"
                      />
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => moveQuestion(index, index - 1)}
                          disabled={index === 0}
                          className="p-1 text-surface-400 hover:text-surface-600 dark:hover:text-surface-300 disabled:opacity-30"
                          title="上へ移動"
                        >
                          <ChevronUp className="w-5 h-5" />
                        </button>
                        <button
                          onClick={() => moveQuestion(index, index + 1)}
                          disabled={index === questions.length - 1}
                          className="p-1 text-surface-400 hover:text-surface-600 dark:hover:text-surface-300 disabled:opacity-30"
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
                      <label className="flex items-center gap-2 text-sm text-surface-500 dark:text-surface-400">
                        <input
                          type="checkbox"
                          checked={question.required}
                          onChange={(e) =>
                            updateQuestion(question.id, { required: e.target.checked })
                          }
                          className="rounded border-surface-300 dark:border-surface-600 text-accent-500 focus:ring-accent-500"
                        />
                        必須質問
                      </label>
                      <button
                        onClick={() =>
                          setExpandedQuestionId(
                            expandedQuestionId === question.id ? null : question.id
                          )
                        }
                        className="text-sm text-accent-500 hover:text-accent-600 dark:hover:text-accent-400"
                      >
                        フォローアップ質問 ({question.followUps.length})
                      </button>
                    </div>

                    {/* Follow-up questions */}
                    {expandedQuestionId === question.id && (
                      <div className="mt-4 pl-4 border-l-2 border-surface-200 dark:border-surface-700 space-y-3">
                        <p className="text-sm text-surface-500 dark:text-surface-400">
                          回答内容に応じて追加で聞く質問
                        </p>
                        {question.followUps.map((followUp, fIndex) => (
                          <div key={fIndex} className="flex items-center gap-2">
                            <span className="text-surface-400 text-sm">└</span>
                            <input
                              type="text"
                              value={followUp}
                              onChange={(e) =>
                                updateFollowUp(question.id, fIndex, e.target.value)
                              }
                              placeholder="フォローアップ質問を入力..."
                              className="flex-1 px-3 py-1.5 text-sm bg-white dark:bg-surface-800 border border-surface-200 dark:border-surface-700 rounded-lg text-surface-900 dark:text-surface-100 placeholder:text-surface-400 focus:outline-none focus:ring-2 focus:ring-accent-500/50 focus:border-accent-500 transition-all"
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
                          className="text-sm text-accent-500 hover:text-accent-600 dark:hover:text-accent-400 flex items-center gap-1"
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
            <div className="w-12 h-12 bg-surface-100 dark:bg-surface-800 rounded-full flex items-center justify-center mx-auto mb-4">
              <Plus className="w-6 h-6 text-surface-400" />
            </div>
            <h3 className="text-lg font-medium text-surface-900 dark:text-surface-50 mb-2">
              質問がありません
            </h3>
            <p className="text-surface-500 dark:text-surface-400 mb-6">
              「質問を追加」ボタンで質問を追加してください
            </p>
            <Button variant="accent" onClick={addQuestion}>最初の質問を追加</Button>
          </div>
        )}
      </Card>

      {/* Publish Modal */}
      <Modal
        isOpen={isPublishModalOpen}
        onClose={() => setIsPublishModalOpen(false)}
        title="テンプレートを公開"
        size="sm"
      >
        <ModalBody>
          <p className="text-surface-500 dark:text-surface-400">
            このテンプレートを公開すると、タスク作成時に選択できるようになります。
            公開後も編集は可能ですが、バージョン番号が更新されます。
          </p>
        </ModalBody>
        <ModalFooter>
          <Button variant="outline" onClick={() => setIsPublishModalOpen(false)}>
            キャンセル
          </Button>
          <Button
            variant="accent"
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
