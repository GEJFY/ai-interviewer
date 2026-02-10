'use client';

import Link from 'next/link';
import { ArrowRight, MessageSquare, FileText, BarChart3, Shield, Mic, Zap } from 'lucide-react';
import { motion } from 'framer-motion';
import { ThemeToggle } from '@/components/theme-toggle';

const fadeInUp = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } },
};

const staggerContainer = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.12 } },
};

export default function HomePage() {
  return (
    <div className="min-h-screen bg-[rgb(var(--bg))]">
      {/* Header */}
      <header className="fixed top-0 inset-x-0 z-50 glass-strong">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <span className="text-lg font-bold tracking-tight text-surface-900 dark:text-surface-50">
              AI Interview
              <span className="text-accent-500">.</span>
            </span>
            <div className="flex items-center gap-3">
              <ThemeToggle />
              <Link
                href="/login"
                className="text-sm text-surface-600 dark:text-surface-400 hover:text-surface-900 dark:hover:text-surface-50 transition-colors"
              >
                ログイン
              </Link>
              <Link
                href="/register"
                className="px-4 py-2 text-sm font-medium bg-accent-500 text-white rounded-lg hover:bg-accent-600 transition-colors shadow-sm"
              >
                無料で始める
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero - 非対称レイアウト */}
      <main className="pt-16">
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-32">
          <div className="grid lg:grid-cols-12 gap-12 items-center">
            {/* 左: テキスト (7/12) */}
            <motion.div
              className="lg:col-span-7"
              initial="hidden"
              animate="visible"
              variants={staggerContainer}
            >
              <motion.p
                variants={fadeInUp}
                className="text-sm font-medium text-accent-500 tracking-widest uppercase mb-4"
              >
                GRC Advisory Platform
              </motion.p>
              <motion.h1
                variants={fadeInUp}
                className="text-4xl md:text-5xl lg:text-6xl font-bold leading-[1.1] text-surface-900 dark:text-surface-50 mb-6"
              >
                ヒアリングを、
                <br />
                <span className="text-accent-500">もっとスマートに</span>
              </motion.h1>
              <motion.p
                variants={fadeInUp}
                className="text-lg text-surface-500 dark:text-surface-400 max-w-lg mb-8 leading-relaxed"
              >
                AIによる対話型インタビューとリアルタイム分析で、
                GRCアドバイザリー業務の生産性を根本から変える。
              </motion.p>
              <motion.div variants={fadeInUp} className="flex flex-wrap gap-4">
                <Link
                  href="/register"
                  className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-accent-500 to-accent-600 text-white font-medium rounded-lg hover:from-accent-600 hover:to-accent-700 transition-all shadow-lg shadow-accent-500/25"
                >
                  無料で始める
                  <ArrowRight className="w-4 h-4" />
                </Link>
                <Link
                  href="/demo"
                  className="inline-flex items-center gap-2 px-6 py-3 border border-surface-300 dark:border-surface-600 text-surface-700 dark:text-surface-300 font-medium rounded-lg hover:bg-surface-50 dark:hover:bg-surface-800 transition-colors"
                >
                  デモを見る
                </Link>
              </motion.div>
            </motion.div>

            {/* 右: インタビューUIモック (5/12) */}
            <motion.div
              className="lg:col-span-5"
              initial={{ opacity: 0, x: 30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, delay: 0.3, ease: 'easeOut' }}
            >
              <div className="glass rounded-2xl p-6 space-y-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-xs text-surface-500 dark:text-surface-400">インタビュー進行中</span>
                </div>
                {/* AI メッセージ */}
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-lg bg-accent-500/10 flex items-center justify-center flex-shrink-0">
                    <Zap className="w-4 h-4 text-accent-500" />
                  </div>
                  <div className="glass rounded-xl rounded-tl-sm px-4 py-3 text-sm text-surface-700 dark:text-surface-300 flex-1">
                    内部統制の整備状況について教えてください。特に、承認プロセスの運用は？
                  </div>
                </div>
                {/* ユーザー メッセージ */}
                <div className="flex gap-3 justify-end">
                  <div className="bg-accent-500/10 dark:bg-accent-500/20 rounded-xl rounded-tr-sm px-4 py-3 text-sm text-surface-700 dark:text-surface-300 max-w-[80%]">
                    承認フローは3段階で、部門長→管理部→経営層の順で...
                  </div>
                </div>
                {/* 分析バー */}
                <div className="border-t border-surface-200 dark:border-surface-700 pt-3">
                  <div className="flex items-center justify-between text-xs text-surface-500 dark:text-surface-400 mb-2">
                    <span>カバレッジ</span>
                    <span className="text-accent-500 font-medium">67%</span>
                  </div>
                  <div className="h-1.5 bg-surface-200 dark:bg-surface-700 rounded-full overflow-hidden">
                    <div className="h-full w-2/3 bg-gradient-to-r from-accent-400 to-accent-500 rounded-full" />
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </section>

        {/* 特徴 - 左右交互配置 */}
        <section className="border-t border-surface-200 dark:border-surface-800">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-28">
            <motion.div
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: '-100px' }}
              variants={staggerContainer}
              className="space-y-20"
            >
              {/* Feature 1 */}
              <motion.div variants={fadeInUp} className="grid lg:grid-cols-2 gap-12 items-center">
                <div>
                  <div className="w-10 h-10 rounded-lg bg-accent-500/10 flex items-center justify-center mb-4">
                    <MessageSquare className="w-5 h-5 text-accent-500" />
                  </div>
                  <h3 className="text-2xl font-bold text-surface-900 dark:text-surface-50 mb-3">
                    AI対話インタビュー
                  </h3>
                  <p className="text-surface-500 dark:text-surface-400 leading-relaxed">
                    GRC領域に特化したAIが、回答に応じて適切な深掘り質問を自動生成。
                    テキスト入力と音声入力の両方に対応し、自然な対話でヒアリングを実施。
                  </p>
                </div>
                <div className="glass rounded-xl p-6">
                  <div className="space-y-3">
                    <div className="h-3 bg-surface-200 dark:bg-surface-700 rounded w-3/4" />
                    <div className="h-3 bg-surface-200 dark:bg-surface-700 rounded w-1/2" />
                    <div className="h-3 bg-accent-500/20 rounded w-5/6" />
                    <div className="h-3 bg-surface-200 dark:bg-surface-700 rounded w-2/3" />
                  </div>
                </div>
              </motion.div>

              {/* Feature 2 - 左右反転 */}
              <motion.div variants={fadeInUp} className="grid lg:grid-cols-2 gap-12 items-center">
                <div className="order-2 lg:order-1 glass rounded-xl p-6">
                  <div className="grid grid-cols-3 gap-3">
                    {['業務記述書', 'RCM', '監査調書'].map((doc) => (
                      <div key={doc} className="bg-surface-100 dark:bg-surface-800 rounded-lg p-3 text-center">
                        <FileText className="w-5 h-5 mx-auto mb-1 text-accent-500" />
                        <span className="text-xs text-surface-600 dark:text-surface-400">{doc}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="order-1 lg:order-2">
                  <div className="w-10 h-10 rounded-lg bg-accent-500/10 flex items-center justify-center mb-4">
                    <FileText className="w-5 h-5 text-accent-500" />
                  </div>
                  <h3 className="text-2xl font-bold text-surface-900 dark:text-surface-50 mb-3">
                    自動レポート生成
                  </h3>
                  <p className="text-surface-500 dark:text-surface-400 leading-relaxed">
                    インタビュー結果から業務記述書、RCM、監査調書を自動生成。
                    レビュー時間を大幅に削減し、ドキュメント品質を均一化。
                  </p>
                </div>
              </motion.div>

              {/* Feature 3 */}
              <motion.div variants={fadeInUp} className="grid lg:grid-cols-2 gap-12 items-center">
                <div>
                  <div className="w-10 h-10 rounded-lg bg-accent-500/10 flex items-center justify-center mb-4">
                    <BarChart3 className="w-5 h-5 text-accent-500" />
                  </div>
                  <h3 className="text-2xl font-bold text-surface-900 dark:text-surface-50 mb-3">
                    リアルタイム分析
                  </h3>
                  <p className="text-surface-500 dark:text-surface-400 leading-relaxed">
                    意識調査の統計分析、回答トレンドの可視化でリスクの兆候を早期に発見。
                    マルチクラウドAI基盤による高精度な分析を実現。
                  </p>
                </div>
                <div className="glass rounded-xl p-6">
                  <div className="flex items-end gap-2 h-24">
                    {[40, 65, 45, 80, 55, 90, 70].map((h, i) => (
                      <div
                        key={i}
                        className="flex-1 bg-gradient-to-t from-accent-500 to-accent-400 rounded-t opacity-80"
                        style={{ height: `${h}%` }}
                      />
                    ))}
                  </div>
                </div>
              </motion.div>
            </motion.div>
          </div>
        </section>

        {/* 活用シーン - インタラクティブグリッド */}
        <section className="border-t border-surface-200 dark:border-surface-800 bg-surface-50 dark:bg-surface-950">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-28">
            <motion.div
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: '-100px' }}
              variants={staggerContainer}
            >
              <motion.h2
                variants={fadeInUp}
                className="text-3xl font-bold text-surface-900 dark:text-surface-50 mb-4"
              >
                活用シーン
              </motion.h2>
              <motion.p
                variants={fadeInUp}
                className="text-surface-500 dark:text-surface-400 mb-12 max-w-lg"
              >
                GRC領域の幅広い業務でご活用いただけます。
              </motion.p>
              <motion.div variants={fadeInUp} className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                  { icon: Shield, label: 'コンプライアンス意識調査' },
                  { icon: MessageSquare, label: '内部監査ヒアリング' },
                  { icon: BarChart3, label: 'リスクアセスメント' },
                  { icon: FileText, label: '取締役会実効性評価' },
                  { icon: Shield, label: 'J-SOX統制評価' },
                  { icon: Zap, label: 'サイバーリスク評価' },
                  { icon: Mic, label: 'ナレッジ抽出・継承' },
                  { icon: Shield, label: '第三者リスク評価' },
                ].map(({ icon: Icon, label }) => (
                  <div
                    key={label}
                    className="group flex items-center gap-3 px-4 py-3.5 rounded-xl border border-surface-200 dark:border-surface-800 bg-white dark:bg-surface-900 hover:border-accent-500/40 hover:shadow-sm transition-all cursor-default"
                  >
                    <Icon className="w-4 h-4 text-surface-400 group-hover:text-accent-500 transition-colors flex-shrink-0" />
                    <span className="text-sm text-surface-700 dark:text-surface-300">{label}</span>
                  </div>
                ))}
              </motion.div>
            </motion.div>
          </div>
        </section>

        {/* CTA */}
        <section className="border-t border-surface-200 dark:border-surface-800">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-28 text-center">
            <motion.div
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              variants={staggerContainer}
            >
              <motion.h2
                variants={fadeInUp}
                className="text-3xl md:text-4xl font-bold text-surface-900 dark:text-surface-50 mb-4"
              >
                今すぐ始めましょう
              </motion.h2>
              <motion.p
                variants={fadeInUp}
                className="text-surface-500 dark:text-surface-400 mb-8 max-w-md mx-auto"
              >
                登録は無料。AIの力でGRC業務を効率化しませんか。
              </motion.p>
              <motion.div variants={fadeInUp}>
                <Link
                  href="/register"
                  className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-accent-500 to-accent-600 text-white font-medium rounded-xl hover:from-accent-600 hover:to-accent-700 transition-all shadow-lg shadow-accent-500/25 text-lg"
                >
                  無料アカウント作成
                  <ArrowRight className="w-5 h-5" />
                </Link>
              </motion.div>
            </motion.div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-surface-200 dark:border-surface-800 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-surface-400">
            &copy; 2025 AI Interview Tool. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
