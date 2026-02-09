'use client';

import React, { useState } from 'react';
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
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

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
  ...Object.entries(REPORT_TYPE_LABELS).map(([value, label]) => ({ value, label })),
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

  const statusVariant = (status: string) => {
    if (status === 'approved' || status === 'published') return 'success';
    if (status === 'review') return 'warning';
    return 'default';
  };

  const getReportIcon = (type: string) => {
    switch (type) {
      case 'rcm':
      case 'audit_workpaper':
        return <FileSpreadsheet className="w-5 h-5 text-emerald-500" />;
      case 'process_document':
        return <File className="w-5 h-5 text-blue-500" />;
      default:
        return <FileText className="w-5 h-5 text-accent-500" />;
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-surface-900 dark:text-surface-50">レポート</h1>
          <p className="text-surface-500 dark:text-surface-400 mt-1">
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
            variant="accent"
            leftIcon={<FileText className="w-5 h-5" />}
            onClick={() => setIsGenerateModalOpen(true)}
          >
            レポート生成
          </Button>
        </div>
      </div>

      {/* Filter */}
      <Card className="flex items-center gap-4 p-4">
        <Filter className="w-5 h-5 text-surface-400" />
        <div className="w-64">
          <Select
            options={REPORT_TYPE_OPTIONS}
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            placeholder="レポートタイプで絞り込み"
          />
        </div>
        {(interviewId || taskId) && (
          <Link href="/reports" className="text-sm text-accent-500 hover:text-accent-600 transition-colors">
            フィルターをクリア
          </Link>
        )}
      </Card>

      {/* Reports List */}
      <Card>
        {isLoading ? (
          <div className="p-6">
            <div className="animate-pulse space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-20 bg-surface-100 dark:bg-surface-800 rounded" />
              ))}
            </div>
          </div>
        ) : data?.items?.length > 0 ? (
          <div className="divide-y divide-surface-100 dark:divide-surface-800">
            {data.items.map((report: Report) => (
              <div
                key={report.id}
                className="flex items-center gap-4 px-6 py-4 hover:bg-surface-50 dark:hover:bg-surface-800/50 transition-colors"
              >
                <div className="p-2 bg-surface-100 dark:bg-surface-800 rounded-lg">
                  {getReportIcon(report.report_type)}
                </div>
                <Link href={`/reports/${report.id}`} className="flex-1 min-w-0">
                  <p className="font-medium text-surface-900 dark:text-surface-100">{report.title}</p>
                  <div className="flex items-center gap-4 text-sm text-surface-500 dark:text-surface-400">
                    <span>{REPORT_TYPE_LABELS[report.report_type] || report.report_type}</span>
                    <span>{format(new Date(report.created_at), 'yyyy/MM/dd HH:mm', { locale: ja })}</span>
                  </div>
                </Link>
                <div className="flex items-center gap-4">
                  <Badge variant={statusVariant(report.status)}>
                    {STATUS_LABELS[report.status] || report.status}
                  </Badge>
                  <div className="flex items-center gap-1">
                    {['pdf', 'docx', 'xlsx'].map((fmt) => (
                      <button
                        key={fmt}
                        onClick={() => handleExport(report, fmt)}
                        className="p-2 text-surface-400 hover:text-surface-600 dark:hover:text-surface-300 hover:bg-surface-100 dark:hover:bg-surface-800 rounded-lg transition-colors"
                        title={`${fmt.toUpperCase()}出力`}
                      >
                        {fmt === 'pdf' ? <Download className="w-4 h-4" /> :
                         fmt === 'docx' ? <File className="w-4 h-4" /> :
                         <FileSpreadsheet className="w-4 h-4" />}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-12 text-center">
            <FileText className="w-12 h-12 text-surface-300 dark:text-surface-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-surface-900 dark:text-surface-50 mb-2">
              レポートがありません
            </h3>
            <p className="text-surface-500 dark:text-surface-400 mb-6">
              インタビュー完了後にレポートを生成できます
            </p>
            <Button variant="accent" onClick={() => setIsGenerateModalOpen(true)}>
              レポートを生成
            </Button>
          </div>
        )}
      </Card>

      {/* Generate Report Modal */}
      <Modal
        isOpen={isGenerateModalOpen}
        onClose={() => setIsGenerateModalOpen(false)}
        title="レポート生成"
      >
        <ModalBody>
          <div className="space-y-4">
            <p className="text-surface-500 dark:text-surface-400">
              AIが自動的にレポートを生成します。生成後に内容を確認・編集できます。
            </p>
            <Select
              label="レポートタイプ"
              options={Object.entries(REPORT_TYPE_LABELS).map(([value, label]) => ({ value, label }))}
              value={selectedReportType}
              onChange={(e) => setSelectedReportType(e.target.value)}
            />
            <div className="bg-surface-50 dark:bg-surface-800 rounded-lg p-4">
              <h4 className="font-medium text-surface-900 dark:text-surface-50 mb-2">
                {REPORT_TYPE_LABELS[selectedReportType]}
              </h4>
              <p className="text-sm text-surface-500 dark:text-surface-400">
                {selectedReportType === 'summary' && 'インタビュー内容を要約し、主要なポイントをまとめます。'}
                {selectedReportType === 'process_document' && '業務プロセスを可視化した業務記述書を作成します。'}
                {selectedReportType === 'rcm' && 'リスクと統制の対応関係を整理したRCMを作成します。'}
                {selectedReportType === 'audit_workpaper' && '監査手続の結果をまとめた監査調書を作成します。'}
                {selectedReportType === 'compliance_report' && 'コンプライアンス状況の分析レポートを作成します。'}
                {selectedReportType === 'analysis' && 'インタビュー結果の詳細分析レポートを作成します。'}
              </p>
            </div>
          </div>
        </ModalBody>
        <ModalFooter>
          <Button variant="outline" onClick={() => setIsGenerateModalOpen(false)}>
            キャンセル
          </Button>
          <Button
            variant="accent"
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
    <React.Suspense
      fallback={
        <div className="space-y-6 animate-fade-in">
          <div className="animate-pulse">
            <div className="h-8 bg-surface-200 dark:bg-surface-700 rounded w-1/4 mb-2" />
            <div className="h-4 bg-surface-200 dark:bg-surface-700 rounded w-1/2" />
          </div>
          <div className="h-64 bg-surface-200 dark:bg-surface-700 rounded" />
        </div>
      }
    >
      <ReportsContent />
    </React.Suspense>
  );
}
