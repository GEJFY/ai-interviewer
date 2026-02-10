'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Eye, EyeOff, Loader2, Zap } from 'lucide-react';
import { useAuth } from '@/lib/auth';

const loginSchema = z.object({
  email: z.string().email('有効なメールアドレスを入力してください'),
  password: z.string().min(1, 'パスワードを入力してください'),
});

type LoginForm = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginForm) => {
    setError(null);
    try {
      await login(data.email, data.password);
      router.push('/dashboard');
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 'ログインに失敗しました。メールアドレスとパスワードを確認してください。'
      );
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* 左: ブランドパネル */}
      <div className="hidden lg:flex lg:w-[45%] bg-surface-950 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-accent-500/10 via-transparent to-transparent" />
        <div className="relative z-10 flex flex-col justify-between p-12 w-full">
          <Link href="/" className="text-lg font-bold text-surface-50">
            AI Interview<span className="text-accent-400">.</span>
          </Link>
          <div>
            <h2 className="text-3xl font-bold text-surface-50 mb-4 leading-tight">
              GRC業務を、
              <br />
              次のレベルへ。
            </h2>
            <p className="text-surface-400 leading-relaxed max-w-md">
              AIによるインタビュー自動化、リアルタイム分析、
              レポート自動生成で業務効率を飛躍的に向上させます。
            </p>
          </div>
          <p className="text-sm text-surface-600">
            &copy; 2025 AI Interview Tool
          </p>
        </div>
      </div>

      {/* 右: フォーム */}
      <div className="flex-1 flex items-center justify-center px-4 py-8 bg-[rgb(var(--bg))]">
        <div className="w-full max-w-md">
          {/* モバイル用ロゴ */}
          <div className="lg:hidden mb-8 text-center">
            <Link href="/" className="text-xl font-bold text-surface-900 dark:text-surface-50">
              AI Interview<span className="text-accent-500">.</span>
            </Link>
          </div>

          <div className="glass rounded-2xl p-8">
            <div className="mb-8">
              <h1 className="text-2xl font-bold text-surface-900 dark:text-surface-50">
                ログイン
              </h1>
              <p className="text-surface-500 dark:text-surface-400 mt-2 text-sm">
                アカウント情報を入力してください
              </p>
            </div>

            {error && (
              <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400 text-sm">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-2">
                  メールアドレス
                </label>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  {...register('email')}
                  className="w-full px-4 py-3 bg-white dark:bg-surface-800 border border-surface-300 dark:border-surface-600 rounded-lg text-surface-900 dark:text-surface-100 placeholder:text-surface-400 dark:placeholder:text-surface-500 focus:outline-none focus:ring-2 focus:ring-accent-500/50 focus:border-accent-500 transition-all"
                  placeholder="example@company.com"
                />
                {errors.email && (
                  <p className="mt-1 text-sm text-red-500">{errors.email.message}</p>
                )}
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-2">
                  パスワード
                </label>
                <div className="relative">
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    {...register('password')}
                    className="w-full px-4 py-3 bg-white dark:bg-surface-800 border border-surface-300 dark:border-surface-600 rounded-lg text-surface-900 dark:text-surface-100 placeholder:text-surface-400 dark:placeholder:text-surface-500 focus:outline-none focus:ring-2 focus:ring-accent-500/50 focus:border-accent-500 transition-all pr-12"
                    placeholder="••••••••"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-surface-400 hover:text-surface-600 dark:hover:text-surface-300 transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
                {errors.password && (
                  <p className="mt-1 text-sm text-red-500">{errors.password.message}</p>
                )}
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 bg-gradient-to-r from-accent-500 to-accent-600 text-white rounded-lg font-medium hover:from-accent-600 hover:to-accent-700 transition-all shadow-lg shadow-accent-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    ログイン中...
                  </>
                ) : (
                  'ログイン'
                )}
              </button>
            </form>

            <div className="mt-6 text-center text-sm text-surface-500 dark:text-surface-400">
              アカウントをお持ちでない方は{' '}
              <Link href="/register" className="text-accent-500 hover:text-accent-600 font-medium">
                新規登録
              </Link>
            </div>
          </div>

          <div className="mt-6 text-center">
            <Link href="/" className="text-sm text-surface-500 hover:text-surface-700 dark:hover:text-surface-300 transition-colors">
              ← トップページに戻る
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
