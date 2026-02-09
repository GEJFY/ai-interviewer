'use client';

import { useState, useEffect } from 'react';
import { useTheme } from 'next-themes';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  User,
  Bell,
  Shield,
  Palette,
  Globe,
  Key,
  Save,
  Cloud,
  CheckCircle2,
  Loader2,
  AlertCircle,
  Cpu,
  Zap,
  DollarSign,
} from 'lucide-react';
import { cn } from '@/lib/cn';
import api from '@/lib/api-client';
import { Button, Input, Select } from '@/components/ui';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

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
  { value: 'dark', label: 'ダーク' },
  { value: 'light', label: 'ライト' },
  { value: 'system', label: 'システム設定に従う' },
];

const AI_PROVIDERS = [
  {
    id: 'azure',
    name: 'Azure OpenAI',
    description: 'Microsoft Azure上のOpenAIサービス',
    icon: '☁️',
    fields: [
      { key: 'azure_openai_api_key', label: 'API Key', type: 'password' },
      { key: 'azure_openai_endpoint', label: 'Endpoint URL', type: 'text' },
      { key: 'azure_openai_deployment_name', label: 'Deployment Name', type: 'text' },
    ],
  },
  {
    id: 'aws',
    name: 'AWS Bedrock',
    description: 'Amazon Bedrock (Claude, Titan等)',
    icon: '🔶',
    fields: [
      { key: 'aws_access_key_id', label: 'Access Key ID', type: 'password' },
      { key: 'aws_secret_access_key', label: 'Secret Access Key', type: 'password' },
      { key: 'aws_region', label: 'Region', type: 'text' },
    ],
  },
  {
    id: 'gcp',
    name: 'GCP Vertex AI',
    description: 'Google Cloud Vertex AI (Gemini等)',
    icon: '🔵',
    fields: [
      { key: 'gcp_project_id', label: 'Project ID', type: 'text' },
      { key: 'gcp_location', label: 'Location', type: 'text' },
    ],
  },
  {
    id: 'local',
    name: 'Local LLM (Ollama)',
    description: '開発・テスト用ローカルLLM',
    icon: '🖥️',
    fields: [
      { key: 'ollama_base_url', label: 'Base URL', type: 'text' },
      { key: 'ollama_model', label: 'Model Name', type: 'text' },
    ],
  },
];

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const { theme: currentTheme, setTheme: setAppTheme } = useTheme();
  const [activeTab, setActiveTab] = useState('profile');

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [interviewReminders, setInterviewReminders] = useState(true);
  const [reportUpdates, setReportUpdates] = useState(true);
  const [language, setLanguage] = useState('ja');
  const [selectedProvider, setSelectedProvider] = useState('azure');
  const [providerConfig, setProviderConfig] = useState<Record<string, string>>({});
  const [testStatus, setTestStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');

  const { data: user, isLoading } = useQuery({
    queryKey: ['user'],
    queryFn: api.auth.me,
  });

  useEffect(() => {
    if (user) {
      setName(user.name);
      setEmail(user.email);
    }
  }, [user]);

  const updateProfileMutation = useMutation({
    mutationFn: async () => ({ name, email }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['user'] }),
  });

  const [testMessage, setTestMessage] = useState('');

  const handleTestConnection = async () => {
    setTestStatus('testing');
    setTestMessage('');
    try {
      const result = await api.models.testConnection(selectedProvider);
      if (result.status === 'success') {
        setTestStatus('success');
        setTestMessage(result.model_used ? `${result.message} (${result.model_used})` : result.message);
      } else {
        setTestStatus('error');
        setTestMessage(result.message);
      }
    } catch {
      setTestStatus('error');
      setTestMessage('接続テストに失敗しました');
    }
    setTimeout(() => setTestStatus('idle'), 5000);
  };

  const tabs = [
    { id: 'profile', label: 'プロフィール', icon: User },
    { id: 'ai-provider', label: 'AIプロバイダー', icon: Cloud },
    { id: 'notifications', label: '通知', icon: Bell },
    { id: 'appearance', label: '外観', icon: Palette },
    { id: 'security', label: 'セキュリティ', icon: Shield },
  ];

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-surface-200 dark:bg-surface-700 rounded w-1/4" />
        <div className="h-64 bg-surface-200 dark:bg-surface-700 rounded" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-surface-900 dark:text-surface-50">設定</h1>
        <p className="text-surface-500 dark:text-surface-400 mt-1">
          アカウントとアプリケーションの設定を管理します
        </p>
      </div>

      <div className="flex gap-6">
        {/* サイドナビ */}
        <div className="w-48 flex-shrink-0">
          <nav className="space-y-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors relative',
                  activeTab === tab.id
                    ? 'bg-surface-100 dark:bg-surface-800 text-surface-900 dark:text-surface-50'
                    : 'text-surface-500 hover:bg-surface-50 dark:hover:bg-surface-900 hover:text-surface-700 dark:hover:text-surface-300'
                )}
              >
                {activeTab === tab.id && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-accent-500 rounded-r" />
                )}
                <tab.icon className={cn('w-5 h-5', activeTab === tab.id && 'text-accent-500')} />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* コンテンツ */}
        <Card className="flex-1">
          {/* プロフィール */}
          {activeTab === 'profile' && (
            <div className="p-6 space-y-6">
              <h2 className="text-lg font-semibold text-surface-900 dark:text-surface-50">
                プロフィール設定
              </h2>
              <div className="space-y-4 max-w-md">
                <Input label="名前" value={name} onChange={(e) => setName(e.target.value)} />
                <Input label="メールアドレス" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
                <div>
                  <label className="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-2">役割</label>
                  <p className="text-surface-500 dark:text-surface-400">
                    {user?.role === 'admin' ? '管理者' : user?.role === 'manager' ? 'マネージャー' : user?.role === 'interviewer' ? 'インタビュアー' : '閲覧者'}
                  </p>
                </div>
              </div>
              <div className="pt-4 border-t border-surface-200 dark:border-surface-700">
                <Button variant="accent" leftIcon={<Save className="w-4 h-4" />} onClick={() => updateProfileMutation.mutate()} isLoading={updateProfileMutation.isPending}>
                  保存
                </Button>
              </div>
            </div>
          )}

          {/* AIプロバイダー */}
          {activeTab === 'ai-provider' && (
            <div className="p-6 space-y-6">
              <div>
                <h2 className="text-lg font-semibold text-surface-900 dark:text-surface-50 mb-1">
                  AIプロバイダー設定
                </h2>
                <p className="text-sm text-surface-500 dark:text-surface-400">
                  インタビューとレポート生成に使用するAIサービスを選択・設定します
                </p>
              </div>

              {/* プロバイダー選択カード */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {AI_PROVIDERS.map((provider) => (
                  <button
                    key={provider.id}
                    onClick={() => setSelectedProvider(provider.id)}
                    className={cn(
                      'p-4 rounded-xl border-2 text-left transition-all',
                      selectedProvider === provider.id
                        ? 'border-accent-500 bg-accent-500/5 dark:bg-accent-500/10'
                        : 'border-surface-200 dark:border-surface-700 hover:border-surface-300 dark:hover:border-surface-600'
                    )}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-2xl">{provider.icon}</span>
                      {selectedProvider === provider.id && (
                        <CheckCircle2 className="w-5 h-5 text-accent-500" />
                      )}
                    </div>
                    <h3 className="font-semibold text-surface-900 dark:text-surface-50 text-sm">
                      {provider.name}
                    </h3>
                    <p className="text-xs text-surface-400 mt-0.5">
                      {provider.description}
                    </p>
                  </button>
                ))}
              </div>

              {/* 選択中プロバイダーの設定フォーム */}
              {AI_PROVIDERS.filter((p) => p.id === selectedProvider).map((provider) => (
                <div key={provider.id} className="space-y-4 max-w-lg">
                  <h3 className="font-medium text-surface-900 dark:text-surface-50">
                    {provider.name} 接続設定
                  </h3>
                  {provider.fields.map((field) => (
                    <Input
                      key={field.key}
                      label={field.label}
                      type={field.type}
                      value={providerConfig[field.key] || ''}
                      onChange={(e) => setProviderConfig({ ...providerConfig, [field.key]: e.target.value })}
                      placeholder={`${field.label}を入力...`}
                    />
                  ))}
                  <div className="flex items-center gap-3 pt-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleTestConnection}
                      isLoading={testStatus === 'testing'}
                    >
                      接続テスト
                    </Button>
                    {testStatus === 'success' && (
                      <span className="flex items-center gap-1 text-sm text-emerald-500">
                        <CheckCircle2 className="w-4 h-4" /> {testMessage || '接続成功'}
                      </span>
                    )}
                    {testStatus === 'error' && (
                      <span className="flex items-center gap-1 text-sm text-red-500">
                        <AlertCircle className="w-4 h-4" /> {testMessage || '接続失敗'}
                      </span>
                    )}
                  </div>
                </div>
              ))}

              {/* モデル選択ガイド */}
              <div className="space-y-3">
                <h3 className="font-medium text-surface-900 dark:text-surface-50 flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-accent-500" />
                  モデル選択ガイド
                </h3>
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-surface-50 dark:bg-surface-800 rounded-lg">
                    <div className="flex items-center gap-2 mb-1">
                      <Zap className="w-4 h-4 text-amber-500" />
                      <span className="text-sm font-medium text-surface-900 dark:text-surface-100">リアルタイム対話</span>
                    </div>
                    <p className="text-xs text-surface-500 dark:text-surface-400">
                      低遅延モデル推奨: Claude Haiku, GPT-5 Nano, Gemini Flash Lite
                    </p>
                  </div>
                  <div className="p-3 bg-surface-50 dark:bg-surface-800 rounded-lg">
                    <div className="flex items-center gap-2 mb-1">
                      <DollarSign className="w-4 h-4 text-emerald-500" />
                      <span className="text-sm font-medium text-surface-900 dark:text-surface-100">分析・レポート</span>
                    </div>
                    <p className="text-xs text-surface-500 dark:text-surface-400">
                      高精度モデル推奨: Claude Opus, GPT-5.2, Gemini Pro
                    </p>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-surface-200 dark:border-surface-700">
                <Button variant="accent" leftIcon={<Save className="w-4 h-4" />}>
                  保存
                </Button>
              </div>
            </div>
          )}

          {/* 通知 */}
          {activeTab === 'notifications' && (
            <div className="p-6 space-y-6">
              <h2 className="text-lg font-semibold text-surface-900 dark:text-surface-50">
                通知設定
              </h2>
              <div className="space-y-4">
                {[
                  { label: 'メール通知', desc: '重要な更新をメールで受け取る', checked: emailNotifications, onChange: setEmailNotifications },
                  { label: 'インタビューリマインダー', desc: '予定されたインタビューの通知', checked: interviewReminders, onChange: setInterviewReminders },
                  { label: 'レポート更新', desc: 'レポートの承認・公開通知', checked: reportUpdates, onChange: setReportUpdates },
                ].map((item) => (
                  <label key={item.label} className="flex items-center justify-between py-2">
                    <div>
                      <p className="font-medium text-surface-900 dark:text-surface-100">{item.label}</p>
                      <p className="text-sm text-surface-500 dark:text-surface-400">{item.desc}</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={item.checked}
                      onChange={(e) => item.onChange(e.target.checked)}
                      className="w-5 h-5 rounded border-surface-300 dark:border-surface-600 text-accent-500 focus:ring-accent-500"
                    />
                  </label>
                ))}
              </div>
              <div className="pt-4 border-t border-surface-200 dark:border-surface-700">
                <Button variant="accent" leftIcon={<Save className="w-4 h-4" />}>保存</Button>
              </div>
            </div>
          )}

          {/* 外観 */}
          {activeTab === 'appearance' && (
            <div className="p-6 space-y-6">
              <h2 className="text-lg font-semibold text-surface-900 dark:text-surface-50">
                外観設定
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
                  value={currentTheme || 'dark'}
                  onChange={(e) => setAppTheme(e.target.value)}
                />
              </div>
              <div className="pt-4 border-t border-surface-200 dark:border-surface-700">
                <Button variant="accent" leftIcon={<Save className="w-4 h-4" />}>保存</Button>
              </div>
            </div>
          )}

          {/* セキュリティ */}
          {activeTab === 'security' && (
            <div className="p-6 space-y-6">
              <h2 className="text-lg font-semibold text-surface-900 dark:text-surface-50">
                セキュリティ設定
              </h2>
              <div className="space-y-4">
                {[
                  { icon: Key, title: 'パスワード変更', desc: '定期的にパスワードを変更することをお勧めします', action: 'パスワードを変更' },
                  { icon: Shield, title: '二要素認証 (MFA)', desc: user?.mfa_enabled ? '二要素認証は有効です' : 'セキュリティ強化のためMFAを設定してください', action: user?.mfa_enabled ? '設定を管理' : 'MFAを設定' },
                  { icon: Globe, title: 'アクティブセッション', desc: '現在ログイン中のデバイスを管理します', action: 'セッションを管理' },
                ].map((item) => (
                  <div key={item.title} className="p-4 bg-surface-50 dark:bg-surface-800 rounded-xl">
                    <div className="flex items-center gap-3 mb-3">
                      <item.icon className="w-5 h-5 text-surface-500 dark:text-surface-400" />
                      <h3 className="font-medium text-surface-900 dark:text-surface-100">{item.title}</h3>
                    </div>
                    <p className="text-sm text-surface-500 dark:text-surface-400 mb-4">{item.desc}</p>
                    <Button variant="outline" size="sm">{item.action}</Button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
