# ドキュメント一覧

AIインタビューシステムの全ドキュメントを対象読者別に整理しています。目的に合ったセクションからお読みください。

---

## ユーザー向け（業務利用者）

システムを使ってインタビュー業務を行う方向けのドキュメントです。

| ドキュメント | 内容 |
|------------|------|
| [ユーザーマニュアル](manuals/USER_MANUAL.md) | ログイン、案件・タスク管理、インタビュー実施、レポート生成、ナレッジ検索などの全操作手順 |

---

## 開発者向け（エンジニア）

システムの開発・拡張に関わるエンジニア向けのドキュメントです。

### はじめに

| ドキュメント | 内容 |
|------------|------|
| [セットアップガイド](guides/SETUP.md) | 開発環境の構築手順（Docker, Python, Node.js） |
| [開発ガイド](guides/DEVELOPMENT.md) | コーディング規約、ブランチ戦略、テスト方法 |
| [デモ手順書](guides/DEMO.md) | デモ環境の構築とデモデータの活用 |

### 設計・仕様

| ドキュメント | 内容 |
|------------|------|
| [アーキテクチャ](ARCHITECTURE.md) | システム全体の設計思想、コンポーネント構成、データフロー、ER図 |
| [ログ管理仕様書](specifications/LOGGING.md) | 構造化ログ、相関ID、センシティブデータマスキング |
| [エラー処理仕様書](specifications/ERROR_HANDLING.md) | エラー階層、リトライ戦略、サーキットブレーカー |
| [セキュリティ仕様書](specifications/SECURITY.md) | JWT認証、RBAC、OWASP対策、SSO統合 |
| [インフラ仕様書](specifications/INFRASTRUCTURE.md) | Docker、CI/CD、Terraform、マルチクラウド |
| [AIプロバイダー仕様書](specifications/AI_PROVIDERS.md) | LLM/音声/翻訳のマルチプロバイダー設計 |

---

## 運用者向け（SRE・インフラ担当）

本番環境の構築・運用・保守に関わる担当者向けのドキュメントです。

| ドキュメント | 内容 |
|------------|------|
| [デプロイガイド](guides/DEPLOYMENT.md) | 本番環境へのデプロイ手順（Azure/AWS/GCP） |
| [本番チェックリスト](guides/PRODUCTION_CHECKLIST.md) | 本番リリース前の確認項目一覧 |
| [リソース見積](guides/RESOURCE_ESTIMATION.md) | サーバースペック・コスト見積もり |
| [トラブルシューティング](guides/TROUBLESHOOTING.md) | よくある問題と解決方法 |
| [運用マニュアル](manuals/OPERATION_MANUAL.md) | 日常運用、監視、インシデント対応、スケーリング |
| [保守マニュアル](manuals/MAINTENANCE_MANUAL.md) | DB保守、Redis保守、ログ管理、障害復旧(DR) |

---

## ドキュメント構成

```
docs/
├── README.md                    ← このファイル（ナビゲーション）
├── ARCHITECTURE.md              設計・アーキテクチャ
├── guides/                      ガイド類
│   ├── SETUP.md                   開発環境構築
│   ├── DEVELOPMENT.md             開発ワークフロー
│   ├── DEMO.md                    デモ手順
│   ├── DEPLOYMENT.md              本番デプロイ
│   ├── PRODUCTION_CHECKLIST.md    本番チェックリスト
│   ├── RESOURCE_ESTIMATION.md     リソース見積
│   └── TROUBLESHOOTING.md         トラブルシューティング
├── manuals/                     マニュアル類
│   ├── USER_MANUAL.md             ユーザーマニュアル
│   ├── OPERATION_MANUAL.md        運用マニュアル
│   └── MAINTENANCE_MANUAL.md      保守マニュアル
└── specifications/              仕様書類
    ├── LOGGING.md                 ログ管理仕様
    ├── ERROR_HANDLING.md          エラー処理仕様
    ├── SECURITY.md                セキュリティ仕様
    ├── INFRASTRUCTURE.md          インフラ仕様
    └── AI_PROVIDERS.md            AIプロバイダー仕様
```

---

**最終更新日**: 2026年2月17日
