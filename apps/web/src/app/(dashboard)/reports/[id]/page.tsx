'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import {
  Download,
  Save,
  CheckCircle2,
  Send,
  FileText,
  File,
  FileSpreadsheet,
  Clock,
  AlertCircle,
  Edit3,
} from 'lucide-react';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import api, { apiClient } from '@/lib/api-client';
import logger from '@/lib/logger';
import { REPORT_TYPE_LABELS } from '@/lib/constants';
import { Button, Modal, ModalBody, ModalFooter, Tooltip, toast } from '@/components/ui';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Breadcrumb } from '@/components/ui/breadcrumb';

interface Report {
  id: string;
  title: string;
  reportType: string;
  status: string;
  format: string;
  content: {
    sections?: Array<{
      title: string;
      content: string;
    }>;
    summary?: string;
    findings?: string[];
    recommendations?: string[];
    [key: string]: unknown;
  };
  interviewId: string | null;
  taskId: string | null;
  createdBy: string | null;
  approvedBy: string | null;
  approvedAt: string | null;
  createdAt: string;
  updatedAt: string;
}

const STATUS_LABELS: Record<string, string> = {
  draft: '下書き',
  review: 'レビュー中',
  approved: '承認済み',
  published: '公開',
};

const STATUS_TOOLTIPS: Record<string, string> = {
  draft: '編集中のレポートです。レビュー依頼で次のステップへ進みます',
  review: 'レビュー担当者の確認待ちです',
  approved: '承認済みで公開・配布が可能です',
  published: '社内外に公開されたレポートです',
};

export default function ReportDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const reportId = params.id as string;

  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState<Report['content'] | null>(null);
  const [isExportMenuOpen, setIsExportMenuOpen] = useState(false);
  const [isApproveModalOpen, setIsApproveModalOpen] = useState(false);

  const { data: report, isLoading } = useQuery({
    queryKey: ['report', reportId],
    queryFn: async () => {
      const response = await apiClient.get(`/reports/${reportId}`);
      return response.data;
    },
  });

  useEffect(() => {
    if (report) {
      setEditedContent(report.content);
    }
  }, [report]);

  const updateMutation = useMutation({
    mutationFn: async (content: Report['content']) => {
      const response = await apiClient.put(`/reports/${reportId}`, { content });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['report', reportId] });
      setIsEditing(false);
      toast.success('レポートを保存しました');
    },
    onError: () => {
      toast.error('レポートの保存に失敗しました');
    },
  });

  const submitForReviewMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post(`/reports/${reportId}/submit-review`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['report', reportId] });
      toast.success('レビューを依頼しました');
    },
    onError: () => {
      toast.error('レビュー依頼に失敗しました');
    },
  });

  const approveMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post(`/reports/${reportId}/approve`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['report', reportId] });
      setIsApproveModalOpen(false);
      toast.success('レポートを承認しました');
    },
    onError: () => {
      toast.error('レポートの承認に失敗しました');
    },
  });

  const handleExport = async (format: string) => {
    try {
      const blob = await api.reports.export(reportId, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${report?.title}.${format === 'pdf' ? 'pdf' : format === 'docx' ? 'docx' : 'xlsx'}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      setIsExportMenuOpen(false);
      toast.success('エクスポートしました');
    } catch (error) {
      logger.error('Export failed:', error);
      toast.error('エクスポートに失敗しました');
    }
  };

  const statusBadgeVariant = (status: string) => {
    if (status === 'review') return 'warning' as const;
    if (status === 'approved') return 'success' as const;
    if (status === 'published') return 'info' as const;
    return 'default' as const;
  };

  const statusIcon = (status: string) => {
    if (status === 'draft') return <Clock className="w-3 h-3" />;
    if (status === 'review') return <AlertCircle className="w-3 h-3" />;
    return <CheckCircle2 className="w-3 h-3" />;
  };

  const updateSectionContent = (index: number, content: string) => {
    if (!editedContent?.sections) return;
    const newSections = [...editedContent.sections];
    newSections[index] = { ...newSections[index], content };
    setEditedContent({ ...editedContent, sections: newSections });
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-1/4" />
        <Skeleton className="h-4 w-1/2" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (!report) {
    return (
      <div className="text-center py-12">
        <FileText className="w-12 h-12 text-surface-300 dark:text-surface-600 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-surface-900 dark:text-surface-50 mb-2">
          レポートが見つかりません
        </h3>
        <Link href="/reports" className="text-accent-500 hover:text-accent-600 dark:hover:text-accent-400">
          レポート一覧に戻る
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <Breadcrumb
        items={[
          { label: 'レポート', href: '/reports' },
          { label: report.title },
        ]}
      />

      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-bold text-surface-900 dark:text-surface-50">{report.title}</h1>
            <Tooltip content={STATUS_TOOLTIPS[report.status] || ''} position="bottom">
              <Badge variant={statusBadgeVariant(report.status)}>
                <span className="flex items-center gap-1">
                  {statusIcon(report.status)}
                  {STATUS_LABELS[report.status] || report.status}
                </span>
              </Badge>
            </Tooltip>
          </div>
          <div className="flex items-center gap-4 text-sm text-surface-500 dark:text-surface-400">
            <span>{REPORT_TYPE_LABELS[report.reportType] || report.reportType}</span>
            <span>
              作成日: {format(new Date(report.createdAt), 'yyyy/MM/dd HH:mm', { locale: ja })}
            </span>
            {report.approvedAt && (
              <span>
                承認日: {format(new Date(report.approvedAt), 'yyyy/MM/dd HH:mm', { locale: ja })}
              </span>
            )}
          </div>
        </div>
        <div className="flex gap-3">
          {/* Export dropdown */}
          <div className="relative">
            <Button
              variant="outline"
              leftIcon={<Download className="w-4 h-4" />}
              onClick={() => setIsExportMenuOpen(!isExportMenuOpen)}
            >
              エクスポート
            </Button>
            {isExportMenuOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-surface-850 rounded-lg shadow-lg border border-surface-200 dark:border-surface-700 py-1 z-10 animate-scale-in">
                <button
                  onClick={() => handleExport('pdf')}
                  className="w-full px-4 py-2 text-left text-sm text-surface-700 dark:text-surface-300 hover:bg-surface-50 dark:hover:bg-surface-800 flex items-center gap-2"
                >
                  <FileText className="w-4 h-4" />
                  PDF形式
                </button>
                <button
                  onClick={() => handleExport('docx')}
                  className="w-full px-4 py-2 text-left text-sm text-surface-700 dark:text-surface-300 hover:bg-surface-50 dark:hover:bg-surface-800 flex items-center gap-2"
                >
                  <File className="w-4 h-4" />
                  Word形式
                </button>
                <button
                  onClick={() => handleExport('xlsx')}
                  className="w-full px-4 py-2 text-left text-sm text-surface-700 dark:text-surface-300 hover:bg-surface-50 dark:hover:bg-surface-800 flex items-center gap-2"
                >
                  <FileSpreadsheet className="w-4 h-4" />
                  Excel形式
                </button>
              </div>
            )}
          </div>

          {report.status === 'draft' && (
            <>
              {isEditing ? (
                <>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setEditedContent(report.content);
                      setIsEditing(false);
                    }}
                  >
                    キャンセル
                  </Button>
                  <Button
                    variant="accent"
                    leftIcon={<Save className="w-4 h-4" />}
                    onClick={() => editedContent && updateMutation.mutate(editedContent)}
                    isLoading={updateMutation.isPending}
                  >
                    保存
                  </Button>
                </>
              ) : (
                <>
                  <Button
                    variant="outline"
                    leftIcon={<Edit3 className="w-4 h-4" />}
                    onClick={() => setIsEditing(true)}
                  >
                    編集
                  </Button>
                  <Button
                    variant="accent"
                    leftIcon={<Send className="w-4 h-4" />}
                    onClick={() => submitForReviewMutation.mutate()}
                    isLoading={submitForReviewMutation.isPending}
                  >
                    レビュー依頼
                  </Button>
                </>
              )}
            </>
          )}

          {report.status === 'review' && (
            <Button
              variant="accent"
              leftIcon={<CheckCircle2 className="w-4 h-4" />}
              onClick={() => setIsApproveModalOpen(true)}
            >
              承認
            </Button>
          )}
        </div>
      </div>

      {/* Report Content */}
      <Card>
        {/* Summary */}
        {report.content.summary && (
          <div className="px-6 py-4 border-b border-surface-200 dark:border-surface-700">
            <h2 className="font-semibold text-surface-900 dark:text-surface-50 mb-3">概要</h2>
            {isEditing ? (
              <textarea
                value={editedContent?.summary || ''}
                onChange={(e) =>
                  setEditedContent({ ...editedContent, summary: e.target.value })
                }
                rows={4}
                className="w-full px-4 py-2 bg-white dark:bg-surface-800 border border-surface-200 dark:border-surface-700 rounded-lg text-surface-900 dark:text-surface-100 placeholder:text-surface-400 focus:outline-none focus:ring-2 focus:ring-accent-500/50 focus:border-accent-500 resize-none transition-all"
              />
            ) : (
              <p className="text-surface-600 dark:text-surface-300 whitespace-pre-wrap">{report.content.summary}</p>
            )}
          </div>
        )}

        {/* Sections */}
        {report.content.sections && report.content.sections.length > 0 && (
          <div className="divide-y divide-surface-100 dark:divide-surface-800">
            {report.content.sections.map((section: { title: string; content: string }, index: number) => (
              <div key={index} className="px-6 py-4">
                <h3 className="font-semibold text-surface-900 dark:text-surface-50 mb-3">{section.title}</h3>
                {isEditing ? (
                  <textarea
                    value={editedContent?.sections?.[index]?.content || ''}
                    onChange={(e) => updateSectionContent(index, e.target.value)}
                    rows={6}
                    className="w-full px-4 py-2 bg-white dark:bg-surface-800 border border-surface-200 dark:border-surface-700 rounded-lg text-surface-900 dark:text-surface-100 placeholder:text-surface-400 focus:outline-none focus:ring-2 focus:ring-accent-500/50 focus:border-accent-500 resize-none transition-all"
                  />
                ) : (
                  <div className="text-surface-600 dark:text-surface-300 whitespace-pre-wrap">{section.content}</div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Findings */}
        {report.content.findings && report.content.findings.length > 0 && (
          <div className="px-6 py-4 border-t border-surface-200 dark:border-surface-700">
            <h2 className="font-semibold text-surface-900 dark:text-surface-50 mb-3">主要な発見事項</h2>
            <ul className="space-y-2">
              {report.content.findings.map((finding: string, index: number) => (
                <li key={index} className="flex items-start gap-2 text-surface-600 dark:text-surface-300">
                  <span className="w-5 h-5 flex-shrink-0 bg-accent-500/10 text-accent-600 dark:text-accent-400 rounded-full flex items-center justify-center text-xs font-medium mt-0.5">
                    {index + 1}
                  </span>
                  {finding}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Recommendations */}
        {report.content.recommendations && report.content.recommendations.length > 0 && (
          <div className="px-6 py-4 border-t border-surface-200 dark:border-surface-700">
            <h2 className="font-semibold text-surface-900 dark:text-surface-50 mb-3">改善提案</h2>
            <ul className="space-y-2">
              {report.content.recommendations.map((rec: string, index: number) => (
                <li key={index} className="flex items-start gap-2 text-surface-600 dark:text-surface-300">
                  <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-emerald-500 mt-0.5" />
                  {rec}
                </li>
              ))}
            </ul>
          </div>
        )}
      </Card>

      {/* Approve Modal */}
      <Modal
        isOpen={isApproveModalOpen}
        onClose={() => setIsApproveModalOpen(false)}
        title="レポートを承認"
        size="sm"
      >
        <ModalBody>
          <p className="text-surface-500 dark:text-surface-400">
            このレポートを承認しますか？承認後は公開・配布が可能になります。
          </p>
        </ModalBody>
        <ModalFooter>
          <Button variant="outline" onClick={() => setIsApproveModalOpen(false)}>
            キャンセル
          </Button>
          <Button
            variant="accent"
            onClick={() => approveMutation.mutate()}
            isLoading={approveMutation.isPending}
          >
            承認
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
