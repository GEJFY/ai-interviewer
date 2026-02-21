'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import {
  User,
  Calendar,
  AlertCircle,
  Save,
  Building2,
  Briefcase,
} from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Profile {
  id: string;
  name: string | null;
  email: string | null;
  department: string | null;
  position: string | null;
}

interface PortalInterview {
  id: string;
  task_name: string | null;
  status: string;
  scheduled_at: string | null;
  language: string;
}

interface PortalData {
  profile: Profile;
  interviews: PortalInterview[];
}

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  scheduled: { label: '予定', color: 'bg-blue-100 text-blue-700' },
  in_progress: { label: '進行中', color: 'bg-yellow-100 text-yellow-700' },
  paused: { label: '一時停止', color: 'bg-gray-100 text-gray-600' },
  completed: { label: '完了', color: 'bg-green-100 text-green-700' },
  cancelled: { label: 'キャンセル', color: 'bg-red-100 text-red-600' },
};

export default function PortalPage() {
  const params = useParams();
  const token = params.token as string;

  const [data, setData] = useState<PortalData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // Edit state
  const [editName, setEditName] = useState('');
  const [editDept, setEditDept] = useState('');
  const [editPos, setEditPos] = useState('');

  useEffect(() => {
    async function fetchPortal() {
      try {
        const res = await fetch(`${API_URL}/api/v1/portal/${token}`);
        if (!res.ok) {
          const body = await res.json().catch(() => null);
          throw new Error(body?.detail || 'リンクが無効または期限切れです');
        }
        const json: PortalData = await res.json();
        setData(json);
        setEditName(json.profile.name || '');
        setEditDept(json.profile.department || '');
        setEditPos(json.profile.position || '');
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'エラーが発生しました');
      } finally {
        setLoading(false);
      }
    }
    if (token) fetchPortal();
  }, [token]);

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    try {
      const res = await fetch(`${API_URL}/api/v1/portal/${token}/profile`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: editName || null,
          department: editDept || null,
          position: editPos || null,
        }),
      });
      if (!res.ok) throw new Error('更新に失敗しました');
      const updated: Profile = await res.json();
      setData((prev) => (prev ? { ...prev, profile: updated } : prev));
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      // ignore
    } finally {
      setSaving(false);
    }
  };

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
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900">
            インタビューポータル
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            ご自身の情報確認・編集とインタビュー予定の確認ができます
          </p>
        </div>

        {/* Profile Card */}
        <div className="bg-white rounded-xl shadow-sm border p-6 mb-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
              <User className="w-5 h-5 text-blue-600" />
            </div>
            <h2 className="text-lg font-semibold text-gray-900">
              プロフィール
            </h2>
          </div>

          <div className="space-y-4">
            {data.profile.email && (
              <div>
                <label className="block text-xs text-gray-400 mb-1">メール</label>
                <p className="text-sm text-gray-700">{data.profile.email}</p>
              </div>
            )}

            <div>
              <label className="block text-xs text-gray-400 mb-1">氏名</label>
              <input
                type="text"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                placeholder="氏名を入力"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="flex items-center gap-1 text-xs text-gray-400 mb-1">
                  <Building2 className="w-3 h-3" /> 部署
                </label>
                <input
                  type="text"
                  value={editDept}
                  onChange={(e) => setEditDept(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  placeholder="部署"
                />
              </div>
              <div>
                <label className="flex items-center gap-1 text-xs text-gray-400 mb-1">
                  <Briefcase className="w-3 h-3" /> 役職
                </label>
                <input
                  type="text"
                  value={editPos}
                  onChange={(e) => setEditPos(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  placeholder="役職"
                />
              </div>
            </div>

            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              <Save className="w-4 h-4" />
              {saving ? '保存中...' : saved ? '保存しました' : '保存'}
            </button>
          </div>
        </div>

        {/* Interviews */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
              <Calendar className="w-5 h-5 text-green-600" />
            </div>
            <h2 className="text-lg font-semibold text-gray-900">
              インタビュー予定
            </h2>
          </div>

          {data.interviews.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-6">
              現在予定されているインタビューはありません
            </p>
          ) : (
            <div className="space-y-3">
              {data.interviews.map((iv) => {
                const st = STATUS_LABELS[iv.status] || {
                  label: iv.status,
                  color: 'bg-gray-100 text-gray-600',
                };
                return (
                  <div
                    key={iv.id}
                    className="flex items-center justify-between p-4 rounded-lg border"
                  >
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {iv.task_name || 'インタビュー'}
                      </p>
                      {iv.scheduled_at && (
                        <p className="text-xs text-gray-400 mt-0.5">
                          {new Date(iv.scheduled_at).toLocaleDateString('ja-JP', {
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric',
                          })}
                        </p>
                      )}
                    </div>
                    <span
                      className={`px-2.5 py-1 text-xs font-medium rounded-full ${st.color}`}
                    >
                      {st.label}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="text-center mt-8 text-xs text-gray-400">
          Powered by AI Interview Tool
        </div>
      </div>
    </div>
  );
}
