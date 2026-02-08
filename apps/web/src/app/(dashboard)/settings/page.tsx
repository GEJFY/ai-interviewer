'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  User,
  Bell,
  Shield,
  Palette,
  Globe,
  Key,
  Save,
} from 'lucide-react';
import api from '@/lib/api-client';
import { Button, Input, Select } from '@/components/ui';

interface UserProfile {
  id: string;
  email: string;
  name: string;
  role: string;
  organization_id: string | null;
  mfa_enabled: boolean;
}

const LANGUAGE_OPTIONS = [
  { value: 'ja', label: '日本語' },
  { value: 'en', label: 'English' },
  { value: 'zh', label: '中文' },
  { value: 'ko', label: '한국어' },
];

const THEME_OPTIONS = [
  { value: 'light', label: 'ライト' },
  { value: 'dark', label: 'ダーク' },
  { value: 'system', label: 'システム設定に従う' },
];

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('profile');

  // Profile settings
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');

  // Notification settings
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [interviewReminders, setInterviewReminders] = useState(true);
  const [reportUpdates, setReportUpdates] = useState(true);

  // Appearance settings
  const [language, setLanguage] = useState('ja');
  const [theme, setTheme] = useState('light');

  const { data: user, isLoading } = useQuery({
    queryKey: ['user'],
    queryFn: api.auth.me,
  });

  // Update form when user data is loaded
  useEffect(() => {
    if (user) {
      setName(user.name);
      setEmail(user.email);
    }
  }, [user]);

  const updateProfileMutation = useMutation({
    mutationFn: async () => {
      // This would be a real API call
      return { name, email };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user'] });
    },
  });

  const tabs = [
    { id: 'profile', label: 'プロフィール', icon: User },
    { id: 'notifications', label: '通知', icon: Bell },
    { id: 'appearance', label: '表示', icon: Palette },
    { id: 'security', label: 'セキュリティ', icon: Shield },
  ];

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-secondary-200 rounded w-1/4" />
        <div className="h-64 bg-secondary-200 rounded" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-secondary-900">設定</h1>
        <p className="text-secondary-600 mt-1">
          アカウントとアプリケーションの設定を管理します
        </p>
      </div>

      <div className="flex gap-6">
        {/* Sidebar */}
        <div className="w-48 flex-shrink-0">
          <nav className="space-y-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition ${
                  activeTab === tab.id
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-secondary-600 hover:bg-secondary-50'
                }`}
              >
                <tab.icon className="w-5 h-5" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1 bg-white rounded-xl border border-secondary-200">
          {/* Profile Tab */}
          {activeTab === 'profile' && (
            <div className="p-6 space-y-6">
              <div>
                <h2 className="text-lg font-semibold text-secondary-900 mb-4">
                  プロフィール設定
                </h2>
                <div className="space-y-4 max-w-md">
                  <Input
                    label="名前"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                  <Input
                    label="メールアドレス"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                  <div>
                    <label className="block text-sm font-medium text-secondary-700 mb-2">
                      役割
                    </label>
                    <p className="text-secondary-600">
                      {user?.role === 'admin'
                        ? '管理者'
                        : user?.role === 'manager'
                        ? 'マネージャー'
                        : user?.role === 'interviewer'
                        ? 'インタビュアー'
                        : '閲覧者'}
                    </p>
                  </div>
                </div>
              </div>
              <div className="pt-4 border-t border-secondary-200">
                <Button
                  leftIcon={<Save className="w-4 h-4" />}
                  onClick={() => updateProfileMutation.mutate()}
                  isLoading={updateProfileMutation.isPending}
                >
                  保存
                </Button>
              </div>
            </div>
          )}

          {/* Notifications Tab */}
          {activeTab === 'notifications' && (
            <div className="p-6 space-y-6">
              <div>
                <h2 className="text-lg font-semibold text-secondary-900 mb-4">
                  通知設定
                </h2>
                <div className="space-y-4">
                  <label className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-secondary-900">メール通知</p>
                      <p className="text-sm text-secondary-500">
                        重要な更新をメールで受け取る
                      </p>
                    </div>
                    <input
                      type="checkbox"
                      checked={emailNotifications}
                      onChange={(e) => setEmailNotifications(e.target.checked)}
                      className="w-5 h-5 rounded border-secondary-300 text-primary-600 focus:ring-primary-500"
                    />
                  </label>
                  <label className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-secondary-900">
                        インタビューリマインダー
                      </p>
                      <p className="text-sm text-secondary-500">
                        予定されたインタビューの通知
                      </p>
                    </div>
                    <input
                      type="checkbox"
                      checked={interviewReminders}
                      onChange={(e) => setInterviewReminders(e.target.checked)}
                      className="w-5 h-5 rounded border-secondary-300 text-primary-600 focus:ring-primary-500"
                    />
                  </label>
                  <label className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-secondary-900">レポート更新</p>
                      <p className="text-sm text-secondary-500">
                        レポートの承認・公開通知
                      </p>
                    </div>
                    <input
                      type="checkbox"
                      checked={reportUpdates}
                      onChange={(e) => setReportUpdates(e.target.checked)}
                      className="w-5 h-5 rounded border-secondary-300 text-primary-600 focus:ring-primary-500"
                    />
                  </label>
                </div>
              </div>
              <div className="pt-4 border-t border-secondary-200">
                <Button leftIcon={<Save className="w-4 h-4" />}>保存</Button>
              </div>
            </div>
          )}

          {/* Appearance Tab */}
          {activeTab === 'appearance' && (
            <div className="p-6 space-y-6">
              <div>
                <h2 className="text-lg font-semibold text-secondary-900 mb-4">
                  表示設定
                </h2>
                <div className="space-y-4 max-w-md">
                  <Select
                    label="言語"
                    options={LANGUAGE_OPTIONS}
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                  />
                  <Select
                    label="テーマ"
                    options={THEME_OPTIONS}
                    value={theme}
                    onChange={(e) => setTheme(e.target.value)}
                  />
                </div>
              </div>
              <div className="pt-4 border-t border-secondary-200">
                <Button leftIcon={<Save className="w-4 h-4" />}>保存</Button>
              </div>
            </div>
          )}

          {/* Security Tab */}
          {activeTab === 'security' && (
            <div className="p-6 space-y-6">
              <div>
                <h2 className="text-lg font-semibold text-secondary-900 mb-4">
                  セキュリティ設定
                </h2>
                <div className="space-y-6">
                  {/* Password Change */}
                  <div className="p-4 bg-secondary-50 rounded-lg">
                    <div className="flex items-center gap-3 mb-3">
                      <Key className="w-5 h-5 text-secondary-600" />
                      <h3 className="font-medium text-secondary-900">
                        パスワード変更
                      </h3>
                    </div>
                    <p className="text-sm text-secondary-600 mb-4">
                      定期的にパスワードを変更することをお勧めします
                    </p>
                    <Button variant="outline" size="sm">
                      パスワードを変更
                    </Button>
                  </div>

                  {/* MFA */}
                  <div className="p-4 bg-secondary-50 rounded-lg">
                    <div className="flex items-center gap-3 mb-3">
                      <Shield className="w-5 h-5 text-secondary-600" />
                      <h3 className="font-medium text-secondary-900">
                        二要素認証 (MFA)
                      </h3>
                    </div>
                    <p className="text-sm text-secondary-600 mb-4">
                      {user?.mfa_enabled
                        ? '二要素認証は有効です'
                        : 'アカウントのセキュリティを強化するために二要素認証を設定してください'}
                    </p>
                    <Button variant="outline" size="sm">
                      {user?.mfa_enabled ? '設定を管理' : 'MFAを設定'}
                    </Button>
                  </div>

                  {/* Sessions */}
                  <div className="p-4 bg-secondary-50 rounded-lg">
                    <div className="flex items-center gap-3 mb-3">
                      <Globe className="w-5 h-5 text-secondary-600" />
                      <h3 className="font-medium text-secondary-900">
                        アクティブセッション
                      </h3>
                    </div>
                    <p className="text-sm text-secondary-600 mb-4">
                      現在ログイン中のデバイスを管理します
                    </p>
                    <Button variant="outline" size="sm">
                      セッションを管理
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
