'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { ClipboardList, Clock, AlertCircle, CheckCircle2 } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8100';

interface SharedQuestion {
  order?: number;
  question: string;
  category?: string;
  required?: boolean;
  follow_ups?: string[];
}

interface SharedData {
  interview_id: string;
  task_name: string;
  template_name: string | null;
  description: string | null;
  questions: SharedQuestion[];
  estimated_duration_minutes: number | null;
  language: string;
}

export default function SharedQuestionsPage() {
  const params = useParams();
  const token = params.token as string;

  const [data, setData] = useState<SharedData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchQuestions() {
      try {
        const res = await fetch(`${API_URL}/api/v1/share/${token}`);
        if (!res.ok) {
          const body = await res.json().catch(() => null);
          throw new Error(body?.detail || 'リンクが無効または期限切れです');
        }
        const json = await res.json();
        setData(json);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'エラーが発生しました');
      } finally {
        setLoading(false);
      }
    }
    if (token) fetchQuestions();
  }, [token]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <div className="max-w-md w-full bg-white rounded-xl shadow-sm border p-8 text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h1 className="text-xl font-bold text-gray-900 mb-2">アクセスできません</h1>
          <p className="text-gray-500">{error}</p>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-xl shadow-sm border p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
              <ClipboardList className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                {data.task_name}
              </h1>
              {data.template_name && (
                <p className="text-sm text-gray-500">{data.template_name}</p>
              )}
            </div>
          </div>

          {data.description && (
            <p className="text-gray-600 text-sm mb-4">{data.description}</p>
          )}

          <div className="flex items-center gap-4 text-sm text-gray-500">
            {data.estimated_duration_minutes && (
              <span className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                {data.estimated_duration_minutes}
              </span>
            )}
            <span className="flex items-center gap-1">
              <CheckCircle2 className="w-4 h-4" />
              {data.questions.length}
            </span>
          </div>
        </div>

        {/* Info banner */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <p className="text-sm text-blue-700">
            以下の質問は事前共有用です。インタビュー当日に備えて内容をご確認ください。
            実際のインタビューでは、回答内容に応じてAIが追加の質問をする場合があります。
          </p>
        </div>

        {/* Questions */}
        <div className="space-y-4">
          {data.questions.map((q, index) => (
            <div
              key={index}
              className="bg-white rounded-xl shadow-sm border p-5"
            >
              <div className="flex items-start gap-3">
                <span className="flex-shrink-0 w-7 h-7 rounded-full bg-blue-100 text-blue-700 text-sm font-bold flex items-center justify-center">
                  {q.order ?? index + 1}
                </span>
                <div className="flex-1">
                  <p className="text-gray-900 font-medium">{q.question}</p>

                  {q.category && (
                    <span className="inline-block mt-2 px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">
                      {q.category}
                    </span>
                  )}

                  {q.follow_ups && q.follow_ups.length > 0 && (
                    <div className="mt-3 pl-4 border-l-2 border-gray-200 space-y-1">
                      <p className="text-xs text-gray-400 uppercase tracking-wide">
                        Follow-up
                      </p>
                      {q.follow_ups.map((fu, fi) => (
                        <p key={fi} className="text-sm text-gray-600">
                          {fu}
                        </p>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="text-center mt-8 text-xs text-gray-400">
          Powered by AI Interview Tool
        </div>
      </div>
    </div>
  );
}
