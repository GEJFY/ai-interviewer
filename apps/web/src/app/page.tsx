import Link from 'next/link';
import { ArrowRight, MessageSquare, FileText, BarChart3 } from 'lucide-react';

export default function HomePage() {
  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-secondary-200 bg-white/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <span className="text-xl font-bold text-primary-600">
                AI Interview Tool
              </span>
            </div>
            <div className="flex items-center gap-4">
              <Link
                href="/login"
                className="text-secondary-600 hover:text-secondary-900"
              >
                ログイン
              </Link>
              <Link
                href="/register"
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition"
              >
                新規登録
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-16">
          <h1 className="text-4xl md:text-5xl font-bold text-secondary-900 mb-6">
            GRCアドバイザリー業務を
            <br />
            <span className="text-primary-600">AIでスマートに</span>
          </h1>
          <p className="text-xl text-secondary-600 max-w-2xl mx-auto mb-8">
            AIによる対話型インタビュー、リアルタイム文字起こし、
            自動レポート生成で業務効率を大幅に向上
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/register"
              className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition flex items-center gap-2"
            >
              無料で始める
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              href="/demo"
              className="px-6 py-3 border border-secondary-300 text-secondary-700 rounded-lg hover:bg-secondary-50 transition"
            >
              デモを見る
            </Link>
          </div>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-8">
          <div className="bg-white rounded-xl p-6 shadow-sm border border-secondary-100">
            <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
              <MessageSquare className="w-6 h-6 text-primary-600" />
            </div>
            <h3 className="text-lg font-semibold text-secondary-900 mb-2">
              AI対話インタビュー
            </h3>
            <p className="text-secondary-600">
              AIが適切な質問を自動生成し、回答に応じた深掘り質問で効率的なヒアリングを実現
            </p>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-secondary-100">
            <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
              <FileText className="w-6 h-6 text-primary-600" />
            </div>
            <h3 className="text-lg font-semibold text-secondary-900 mb-2">
              自動レポート生成
            </h3>
            <p className="text-secondary-600">
              業務記述書、RCM、監査調書などの専門帳票を自動生成し、レビュー時間を削減
            </p>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-secondary-100">
            <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
              <BarChart3 className="w-6 h-6 text-primary-600" />
            </div>
            <h3 className="text-lg font-semibold text-secondary-900 mb-2">
              分析・可視化
            </h3>
            <p className="text-secondary-600">
              意識調査の統計分析、トレンド可視化で組織の課題を明確化
            </p>
          </div>
        </div>

        {/* Use Cases */}
        <div className="mt-16">
          <h2 className="text-2xl font-bold text-secondary-900 text-center mb-8">
            活用シーン
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              'コンプライアンス意識調査',
              '内部監査ヒアリング',
              'リスクアセスメント',
              '取締役会実効性評価',
              'J-SOX統制評価',
              'サイバーリスク評価',
              'ナレッジ抽出・継承',
              '第三者リスク評価',
            ].map((useCase) => (
              <div
                key={useCase}
                className="px-4 py-3 bg-secondary-50 rounded-lg text-secondary-700 text-center"
              >
                {useCase}
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-secondary-200 py-8 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-secondary-500">
            &copy; 2025 AI Interview Tool. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
