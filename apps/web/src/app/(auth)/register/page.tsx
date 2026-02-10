'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Eye, EyeOff, Loader2 } from 'lucide-react';
import { useAuth } from '@/lib/auth';

const registerSchema = z
  .object({
    name: z.string().min(1, '名前を入力してください'),
    email: z.string().email('有効なメールアドレスを入力してください'),
    password: z
      .string()
      .min(8, 'パスワードは8文字以上で入力してください')
      .regex(
        /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
        'パスワードは大文字、小文字、数字を含める必要があります'
      ),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'パスワードが一致しません',
    path: ['confirmPassword'],
  });

type RegisterForm = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const router = useRouter();
  const { register: registerUser, isLoading } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterForm) => {
    setError(null);
    try {
      await registerUser(data.email, data.name, data.password);
      router.push('/dashboard');
    } catch (err: any) {
      setError(
        err.response?.data?.detail || '登録に失敗しました。もう一度お試しください。'
      );
    }
  };

  const inputClasses =
    'w-full px-4 py-3 bg-white dark:bg-surface-800 border border-surface-300 dark:border-surface-600 rounded-lg text-surface-900 dark:text-surface-100 placeholder:text-surface-400 dark:placeholder:text-surface-500 focus:outline-none focus:ring-2 focus:ring-accent-500/50 focus:border-accent-500 transition-all';

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
              チームの力を、
              <br />
              最大限に引き出す。
            </h2>
            <p className="text-surface-400 leading-relaxed max-w-md">
              組織のガバナンス・リスク・コンプライアンスを支える
              インテリジェントなインタビューツール。
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
          <div className="lg:hidden mb-8 text-center">
            <Link href="/" className="text-xl font-bold text-surface-900 dark:text-surface-50">
              AI Interview<span className="text-accent-500">.</span>
            </Link>
          </div>

          <div className="glass rounded-2xl p-8">
            <div className="mb-8">
              <h1 className="text-2xl font-bold text-surface-900 dark:text-surface-50">
                新規登録
              </h1>
              <p className="text-surface-500 dark:text-surface-400 mt-2 text-sm">
                アカウントを作成して始めましょう
              </p>
            </div>

            {error && (
              <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400 text-sm">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-2">
                  名前
                </label>
                <input
                  id="name"
                  type="text"
                  autoComplete="name"
                  {...register('name')}
                  className={inputClasses}
                  placeholder="山田 太郎"
                />
                {errors.name && (
                  <p className="mt-1 text-sm text-red-500">{errors.name.message}</p>
                )}
              </div>

              <div>
                <label htmlFor="email" className="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-2">
                  メールアドレス
                </label>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  {...register('email')}
                  className={inputClasses}
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
                    autoComplete="new-password"
                    {...register('password')}
                    className={`${inputClasses} pr-12`}
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
                <p className="mt-1 text-xs text-surface-400">
                  8文字以上、大文字・小文字・数字を含める
                </p>
              </div>

              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-2">
                  パスワード（確認）
                </label>
                <input
                  id="confirmPassword"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  {...register('confirmPassword')}
                  className={inputClasses}
                  placeholder="••••••••"
                />
                {errors.confirmPassword && (
                  <p className="mt-1 text-sm text-red-500">{errors.confirmPassword.message}</p>
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
                    登録中...
                  </>
                ) : (
                  'アカウント作成'
                )}
              </button>
            </form>

            <div className="mt-6 text-center text-sm text-surface-500 dark:text-surface-400">
              すでにアカウントをお持ちの方は{' '}
              <Link href="/login" className="text-accent-500 hover:text-accent-600 font-medium">
                ログイン
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
