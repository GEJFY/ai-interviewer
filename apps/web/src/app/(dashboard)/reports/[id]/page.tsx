'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import {
  ArrowLeft,
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
import { Button, Modal, ModalBody, ModalFooter } from '@/components/ui';

interface Report {
  id: string;
  title: string;
  report_type: string;
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
  interview_id: string | null;
  task_id: string | null;
  created_by: string | null;
  approved_by: string | null;
  approved_at: string | null;
  created_at: string;
  updated_at: string;
}

const REPORT_TYPE_LABELS: Record<string, string> = {
  summary: 'インタビュー要約',
  process_document: '業務記述書',
  rcm: 'RCM（リスクコントロールマトリクス）',
  audit_workpaper: '監査調書',
  compliance_report: 'コンプライアンスレポート',
  analysis: '分析レポート',
};

const STATUS_LABELS: Record<string, string> = {
  draft: '下書き',
  review: 'レビュー中',
  approved: '承認済み',
  published: '公開',
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
    },
  });

  const submitForReviewMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post(`/reports/${reportId}/submit-review`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['report', reportId] });
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
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const getStatusBadge = (status: string) => {
    const styles = {
      draft: 'bg-secondary-100 text-secondary-700',
      review: 'bg-amber-100 text-amber-700',
      approved: 'bg-green-100 text-green-700',
      published: 'bg-blue-100 text-blue-700',
    };
    const icons = {
      draft: <Clock className="w-3 h-3" />,
      review: <AlertCircle className="w-3 h-3" />,
      approved: <CheckCircle2 className="w-3 h-3" />,
      published: <CheckCircle2 className="w-3 h-3" />,
    };
    return (
      <span
        className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full ${
          styles[status as keyof typeof styles] || styles.draft
        }`}
      >
        {icons[status as keyof typeof icons]}
        {STATUS_LABELS[status] || status}
      </span>
    );
  };

  const updateSectionContent = (index: number, content: string) => {
    if (!editedContent?.sections) return;
    const newSections = [...editedContent.sections];
    newSections[index] = { ...newSections[index], content };
    setEditedContent({ ...editedContent, sections: newSections });
  };

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-secondary-200 rounded w-1/4" />
        <div className="h-4 bg-secondary-200 rounded w-1/2" />
        <div className="h-96 bg-secondary-200 rounded" />
      </div>
    );
  }

  if (!report) {
    return (
      <div className="text-center py-12">
        <FileText className="w-12 h-12 text-secondary-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-secondary-900 mb-2">
          レポートが見つかりません
        </h3>
        <Link href="/reports" className="text-primary-600 hover:text-primary-700">
          レポート一覧に戻る
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link
        href="/reports"
        className="inline-flex items-center gap-2 text-secondary-600 hover:text-secondary-900 transition"
      >
        <ArrowLeft className="w-4 h-4" />
        レポート一覧に戻る
      </Link>

      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-bold text-secondary-900">{report.title}</h1>
            {getStatusBadge(report.status)}
          </div>
          <div className="flex items-center gap-4 text-sm text-secondary-500">
            <span>{REPORT_TYPE_LABELS[report.report_type] || report.report_type}</span>
            <span>
              作成日: {format(new Date(report.created_at), 'yyyy/MM/dd HH:mm', { locale: ja })}
            </span>
            {report.approved_at && (
              <span>
                承認日: {format(new Date(report.approved_at), 'yyyy/MM/dd HH:mm', { locale: ja })}
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
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-secondary-200 py-1 z-10">
                <button
                  onClick={() => handleExport('pdf')}
                  className="w-full px-4 py-2 text-left text-sm text-secondary-700 hover:bg-secondary-50 flex items-center gap-2"
                >
                  <FileText className="w-4 h-4" />
                  PDF形式
                </button>
                <button
                  onClick={() => handleExport('docx')}
                  className="w-full px-4 py-2 text-left text-sm text-secondary-700 hover:bg-secondary-50 flex items-center gap-2"
                >
                  <File className="w-4 h-4" />
                  Word形式
                </button>
                <button
                  onClick={() => handleExport('xlsx')}
                  className="w-full px-4 py-2 text-left text-sm text-secondary-700 hover:bg-secondary-50 flex items-center gap-2"
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
              leftIcon={<CheckCircle2 className="w-4 h-4" />}
              onClick={() => setIsApproveModalOpen(true)}
            >
              承認
            </Button>
          )}
        </div>
      </div>

      {/* Report Content */}
      <div className="bg-white rounded-xl border border-secondary-200">
        {/* Summary */}
        {report.content.summary && (
          <div className="px-6 py-4 border-b border-secondary-200">
            <h2 className="font-semibold text-secondary-900 mb-3">概要</h2>
            {isEditing ? (
              <textarea
                value={editedContent?.summary || ''}
                onChange={(e) =>
                  setEditedContent({ ...editedContent, summary: e.target.value })
                }
                rows={4}
                className="w-full px-4 py-2 border border-secondary-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
              />
            ) : (
              <p className="text-secondary-600 whitespace-pre-wrap">{report.content.summary}</p>
            )}
          </div>
        )}

        {/* Sections */}
        {report.content.sections && report.content.sections.length > 0 && (
          <div className="divide-y divide-secondary-100">
            {report.content.sections.map((section: { title: string; content: string }, index: number) => (
              <div key={index} className="px-6 py-4">
                <h3 className="font-semibold text-secondary-900 mb-3">{section.title}</h3>
                {isEditing ? (
                  <textarea
                    value={editedContent?.sections?.[index]?.content || ''}
                    onChange={(e) => updateSectionContent(index, e.target.value)}
                    rows={6}
                    className="w-full px-4 py-2 border border-secondary-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                  />
                ) : (
                  <div className="text-secondary-600 whitespace-pre-wrap">{section.content}</div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Findings */}
        {report.content.findings && report.content.findings.length > 0 && (
          <div className="px-6 py-4 border-t border-secondary-200">
            <h2 className="font-semibold text-secondary-900 mb-3">主要な発見事項</h2>
            <ul className="space-y-2">
              {report.content.findings.map((finding: string, index: number) => (
                <li key={index} className="flex items-start gap-2 text-secondary-600">
                  <span className="w-5 h-5 flex-shrink-0 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center text-xs font-medium mt-0.5">
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
          <div className="px-6 py-4 border-t border-secondary-200">
            <h2 className="font-semibold text-secondary-900 mb-3">改善提案</h2>
            <ul className="space-y-2">
              {report.content.recommendations.map((rec: string, index: number) => (
                <li key={index} className="flex items-start gap-2 text-secondary-600">
                  <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-green-500 mt-0.5" />
                  {rec}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Approve Modal */}
      <Modal
        isOpen={isApproveModalOpen}
        onClose={() => setIsApproveModalOpen(false)}
        title="レポートを承認"
        size="sm"
      >
        <ModalBody>
          <p className="text-secondary-600">
            このレポートを承認しますか？承認後は公開・配布が可能になります。
          </p>
        </ModalBody>
        <ModalFooter>
          <Button variant="outline" onClick={() => setIsApproveModalOpen(false)}>
            キャンセル
          </Button>
          <Button
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
