'use client';

import { useState, Suspense } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  FileText,
  Download,
  RefreshCw,
  Filter,
  FileSpreadsheet,
  File,
  CheckCircle2,
  Clock,
  AlertCircle,
} from 'lucide-react';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import api from '@/lib/api-client';
import { Button, Modal, ModalBody, ModalFooter, Select } from '@/components/ui';

interface Report {
  id: string;
  title: string;
  report_type: string;
  status: string;
  format: string;
  interview_id: string | null;
  task_id: string | null;
  created_at: string;
  updated_at: string;
  approved_at: string | null;
}

const REPORT_TYPE_LABELS: Record<string, string> = {
  summary: 'インタビュー要約',
  process_document: '業務記述書',
  rcm: 'RCM（リスクコントロールマトリクス）',
  audit_workpaper: '監査調書',
  compliance_report: 'コンプライアンスレポート',
  analysis: '分析レポート',
};

const REPORT_TYPE_OPTIONS = [
  { value: '', label: 'すべてのタイプ' },
  ...Object.entries(REPORT_TYPE_LABELS).map(([value, label]) => ({
    value,
    label,
  })),
];

const STATUS_LABELS: Record<string, string> = {
  draft: '下書き',
  review: 'レビュー中',
  approved: '承認済み',
  published: '公開',
};

function ReportsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();

  const interviewId = searchParams.get('interviewId');
  const taskId = searchParams.get('taskId');

  const [isGenerateModalOpen, setIsGenerateModalOpen] = useState(false);
  const [selectedReportType, setSelectedReportType] = useState('summary');
  const [filterType, setFilterType] = useState('');

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['reports', { interviewId, taskId, reportType: filterType }],
    queryFn: () =>
      api.reports.list({
        interviewId: interviewId || undefined,
        taskId: taskId || undefined,
        reportType: filterType || undefined,
      }),
  });

  const generateMutation = useMutation({
    mutationFn: () =>
      api.reports.generate({
        reportType: selectedReportType,
        interviewId: interviewId || undefined,
        taskId: taskId || undefined,
      }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      setIsGenerateModalOpen(false);
      router.push(`/reports/${data.id}`);
    },
  });

  const handleExport = async (report: Report, format: string) => {
    try {
      const blob = await api.reports.export(report.id, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${report.title}.${format === 'pdf' ? 'pdf' : format === 'docx' ? 'docx' : 'xlsx'}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
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

  const getReportIcon = (type: string) => {
    switch (type) {
      case 'rcm':
      case 'audit_workpaper':
        return <FileSpreadsheet className="w-5 h-5 text-green-600" />;
      case 'process_document':
        return <File className="w-5 h-5 text-blue-600" />;
      default:
        return <FileText className="w-5 h-5 text-primary-600" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">レポート</h1>
          <p className="text-secondary-600 mt-1">
            {interviewId
              ? '指定インタビューのレポート'
              : taskId
              ? '指定タスクのレポート'
              : 'すべてのレポートを確認・生成できます'}
          </p>
        </div>
        <div className="flex gap-3">
          <Button
            variant="outline"
            leftIcon={<RefreshCw className="w-4 h-4" />}
            onClick={() => refetch()}
          >
            更新
          </Button>
          <Button
            leftIcon={<FileText className="w-5 h-5" />}
            onClick={() => setIsGenerateModalOpen(true)}
          >
            レポート生成
          </Button>
        </div>
      </div>

      {/* Filter */}
      <div className="flex items-center gap-4 bg-white rounded-xl border border-secondary-200 p-4">
        <Filter className="w-5 h-5 text-secondary-400" />
        <div className="w-64">
          <Select
            options={REPORT_TYPE_OPTIONS}
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            placeholder="レポートタイプで絞り込み"
          />
        </div>
        {(interviewId || taskId) && (
          <Link href="/reports" className="text-sm text-primary-600 hover:text-primary-700">
            フィルターをクリア
          </Link>
        )}
      </div>

      {/* Reports List */}
      <div className="bg-white rounded-xl border border-secondary-200">
        {isLoading ? (
          <div className="p-6">
            <div className="animate-pulse space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-20 bg-secondary-100 rounded" />
              ))}
            </div>
          </div>
        ) : data?.items?.length > 0 ? (
          <div className="divide-y divide-secondary-100">
            {data.items.map((report: Report) => (
              <div
                key={report.id}
                className="flex items-center gap-4 px-6 py-4 hover:bg-secondary-50 transition"
              >
                <div className="p-2 bg-secondary-100 rounded-lg">
                  {getReportIcon(report.report_type)}
                </div>
                <Link href={`/reports/${report.id}`} className="flex-1 min-w-0">
                  <p className="font-medium text-secondary-900">{report.title}</p>
                  <div className="flex items-center gap-4 text-sm text-secondary-500">
                    <span>
                      {REPORT_TYPE_LABELS[report.report_type] || report.report_type}
                    </span>
                    <span>
                      {format(new Date(report.created_at), 'yyyy/MM/dd HH:mm', {
                        locale: ja,
                      })}
                    </span>
                  </div>
                </Link>
                <div className="flex items-center gap-4">
                  {getStatusBadge(report.status)}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleExport(report, 'pdf')}
                      className="p-2 text-secondary-400 hover:text-secondary-600 hover:bg-secondary-100 rounded-lg transition"
                      title="PDF出力"
                    >
                      <Download className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleExport(report, 'docx')}
                      className="p-2 text-secondary-400 hover:text-secondary-600 hover:bg-secondary-100 rounded-lg transition"
                      title="Word出力"
                    >
                      <File className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleExport(report, 'xlsx')}
                      className="p-2 text-secondary-400 hover:text-secondary-600 hover:bg-secondary-100 rounded-lg transition"
                      title="Excel出力"
                    >
                      <FileSpreadsheet className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-12 text-center">
            <FileText className="w-12 h-12 text-secondary-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-secondary-900 mb-2">
              レポートがありません
            </h3>
            <p className="text-secondary-500 mb-6">
              インタビュー完了後にレポートを生成できます
            </p>
            <Button onClick={() => setIsGenerateModalOpen(true)}>
              レポートを生成
            </Button>
          </div>
        )}
      </div>

      {/* Generate Report Modal */}
      <Modal
        isOpen={isGenerateModalOpen}
        onClose={() => setIsGenerateModalOpen(false)}
        title="レポート生成"
      >
        <ModalBody>
          <div className="space-y-4">
            <p className="text-secondary-600">
              AIが自動的にレポートを生成します。生成後に内容を確認・編集できます。
            </p>
            <Select
              label="レポートタイプ"
              options={Object.entries(REPORT_TYPE_LABELS).map(([value, label]) => ({
                value,
                label,
              }))}
              value={selectedReportType}
              onChange={(e) => setSelectedReportType(e.target.value)}
            />
            <div className="bg-secondary-50 rounded-lg p-4">
              <h4 className="font-medium text-secondary-900 mb-2">
                {REPORT_TYPE_LABELS[selectedReportType]}
              </h4>
              <p className="text-sm text-secondary-600">
                {selectedReportType === 'summary' &&
                  'インタビュー内容を要約し、主要なポイントをまとめます。'}
                {selectedReportType === 'process_document' &&
                  '業務プロセスを可視化した業務記述書を作成します。'}
                {selectedReportType === 'rcm' &&
                  'リスクと統制の対応関係を整理したRCMを作成します。'}
                {selectedReportType === 'audit_workpaper' &&
                  '監査手続の結果をまとめた監査調書を作成します。'}
                {selectedReportType === 'compliance_report' &&
                  'コンプライアンス状況の分析レポートを作成します。'}
                {selectedReportType === 'analysis' &&
                  'インタビュー結果の詳細分析レポートを作成します。'}
              </p>
            </div>
          </div>
        </ModalBody>
        <ModalFooter>
          <Button variant="outline" onClick={() => setIsGenerateModalOpen(false)}>
            キャンセル
          </Button>
          <Button
            onClick={() => generateMutation.mutate()}
            isLoading={generateMutation.isPending}
          >
            生成開始
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
}

export default function ReportsPage() {
  return (
    <Suspense
      fallback={
        <div className="space-y-6">
          <div className="animate-pulse">
            <div className="h-8 bg-secondary-200 rounded w-1/4 mb-2" />
            <div className="h-4 bg-secondary-200 rounded w-1/2" />
          </div>
          <div className="h-64 bg-secondary-200 rounded" />
        </div>
      }
    >
      <ReportsContent />
    </Suspense>
  );
}
