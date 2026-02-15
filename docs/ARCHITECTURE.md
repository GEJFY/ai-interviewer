# AI Interview Tool - アーキテクチャドキュメント

> GRC Advisory AI Interview System のシステムアーキテクチャ概要

---

## 目次

1. [システム概要](#1-システム概要)
2. [アーキテクチャ図](#2-アーキテクチャ図)
3. [コンポーネント構成](#3-コンポーネント構成)
4. [データフロー](#4-データフロー)
5. [技術スタック](#5-技術スタック)
6. [インフラストラクチャ](#6-インフラストラクチャ)
7. [セキュリティアーキテクチャ](#7-セキュリティアーキテクチャ)
8. [拡張ポイント](#8-拡張ポイント)

---

## 1. システム概要

AI Interview Tool は、GRC (Governance, Risk, Compliance) 領域に特化した
AI 駆動型インタビューシステムである。内部監査・コンプライアンス調査・リスク
評価などの業務プロセスにおけるヒアリング作業を自動化し、構造化されたレポート
生成まで一貫して支援する。

### 設計思想

- **マルチクラウド対応**: Azure / AWS / GCP の AI サービスを抽象化し、
  ベンダーロックインを回避
- **モノレポ構成**: pnpm workspaces + uv workspace による Python/TypeScript
  ハイブリッドモノレポ
- **レイヤードアーキテクチャ**: 共通パッケージ (grc_core, grc_ai) と
  アプリケーション (backend, web) を明確に分離
- **リアルタイム対話**: WebSocket によるストリーミング AI 対話

### プロジェクト構造 (トップレベル)

```
ai-interviewer/
├── apps/
│   ├── backend/          # FastAPI Python バックエンド (grc_backend)
│   ├── web/              # Next.js 15 フロントエンド (React 19)
│   └── mobile/           # Expo React Native (計画中)
├── packages/
│   └── @grc/
│       ├── core/         # 共通ドメインモデル・DB (grc_core)
│       ├── ai/           # AI/LLM プロバイダ抽象化 (grc_ai)
│       └── infrastructure/ # インフラ共通ユーティリティ
├── infrastructure/
│   ├── terraform/        # マルチクラウド IaC (Azure モジュール)
│   └── db/               # DB 初期化スクリプト
├── docker-compose.yml    # ローカル開発環境
├── pnpm-workspace.yaml   # TypeScript ワークスペース定義
├── pyproject.toml         # Python ワークスペース定義 (uv)
└── docs/                 # ドキュメント
```

---

## 2. アーキテクチャ図

### 全体システム構成

```
┌─────────────────────────────────────────────────────────────────────┐
│                         クライアント層                                │
│                                                                     │
│  ┌─────────────────────┐    ┌─────────────────────┐                │
│  │   Next.js 15 Web    │    │  Expo React Native  │                │
│  │   (React 19)        │    │  (計画中)            │                │
│  │                     │    │                     │                │
│  │  ┌───────────────┐  │    └─────────────────────┘                │
│  │  │ Zustand       │  │                                           │
│  │  │ TanStack Query│  │                                           │
│  │  │ WebSocket     │  │                                           │
│  │  └───────────────┘  │                                           │
│  └────────┬────────────┘                                           │
│           │ HTTPS / WSS                                            │
└───────────┼─────────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────────┐
│                          API ゲートウェイ層                            │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                    FastAPI Application                          │  │
│  │                                                                 │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │  │
│  │  │Security  │  │  CORS    │  │Rate Limit│  │Error     │       │  │
│  │  │Headers   │  │Middleware│  │Middleware│  │Handlers  │       │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │  │
│  │                                                                 │  │
│  │  ┌───────────────────── REST API Routes ─────────────────────┐ │  │
│  │  │ /auth  /projects  /tasks  /interviews  /templates         │ │  │
│  │  │ /reports  /knowledge  /models  /demo  /health             │ │  │
│  │  └──────────────────────────────────────────────────────────-┘ │  │
│  │                                                                 │  │
│  │  ┌───────────────────── WebSocket ───────────────────────────┐ │  │
│  │  │ /interviews/{id}/stream  (リアルタイム対話)                 │ │  │
│  │  └──────────────────────────────────────────────────────────-┘ │  │
│  └──────────┬──────────────────────────────┬────────────────────-┘  │
│             │                              │                         │
└─────────────┼──────────────────────────────┼─────────────────────────┘
              │                              │
              ▼                              ▼
┌─────────────────────────┐    ┌─────────────────────────┐
│    サービス層             │    │    AI プロバイダ層        │
│                         │    │                         │
│  ┌───────────────────┐  │    │  ┌───────────────────┐  │
│  │ InterviewAgent    │  │    │  │ AIProvider        │  │
│  │ (対話制御)         │  │    │  │ Protocol          │  │
│  ├───────────────────┤  │    │  ├───────────────────┤  │
│  │ TranscriptionSvc  │  │    │  │ AzureOpenAI       │  │
│  │ (音声文字起こし)    │  │    │  │ AWS Bedrock       │  │
│  ├───────────────────┤  │    │  │ GCP Vertex AI     │  │
│  │ SynthesisService  │  │    │  │ Ollama (Local)    │  │
│  │ (音声合成)         │  │    │  └───────────────────┘  │
│  ├───────────────────┤  │    │                         │
│  │ ReportGenerator   │  │    │  ┌───────────────────┐  │
│  │ (レポート生成)     │  │    │  │ SpeechProvider    │  │
│  ├───────────────────┤  │    │  │ Protocol          │  │
│  │ AuditService      │  │    │  ├───────────────────┤  │
│  │ (監査ログ)        │  │    │  │ Azure Speech      │  │
│  ├───────────────────┤  │    │  │ AWS Transcribe    │  │
│  │ KnowledgeService  │  │    │  │ GCP Speech        │  │
│  │ (ナレッジベース)    │  │    │  └───────────────────┘  │
│  ├───────────────────┤  │    │                         │
│  │ SSOService        │  │    │  ┌───────────────────┐  │
│  │ (シングルサインオン) │    │  │  │ TranslationSvc   │  │
│  └───────────────────┘  │    │  │ (翻訳サービス)     │  │
│                         │    │  └───────────────────┘  │
└────────────┬────────────┘    └─────────────────────────┘
             │
             ▼
┌───────────────────────────────────────────────────────────────────────┐
│                         データ永続化層                                 │
│                                                                       │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌──────────────┐  │
│  │ PostgreSQL 16       │  │ Redis 7             │  │ Azure Blob   │  │
│  │ + pgvector          │  │                     │  │ Storage      │  │
│  │                     │  │ - セッションキャッシュ│  │              │  │
│  │ - SQLAlchemy Async  │  │ - レート制限カウンタ  │  │ - 音声ファイル│  │
│  │ - Connection Pool   │  │ - 一時データ         │  │ - レポート   │  │
│  │ - Alembic Migration │  │                     │  │              │  │
│  └─────────────────────┘  └─────────────────────┘  └──────────────┘  │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### パッケージ依存関係

```
                    ┌──────────────────┐
                    │   apps/backend   │
                    │  (grc_backend)   │
                    └────┬────────┬────┘
                         │        │
              depends on │        │ depends on
                         ▼        ▼
              ┌──────────────┐  ┌──────────────┐
              │ packages/    │  │ packages/    │
              │ @grc/core    │  │ @grc/ai      │
              │ (grc_core)   │  │ (grc_ai)     │
              └──────────────┘  └──────┬───────┘
                                       │
                                       │ depends on
                                       ▼
                                ┌──────────────┐
                                │ packages/    │
                                │ @grc/core    │
                                │ (grc_core)   │
                                └──────────────┘

     ┌──────────────┐    consumes API    ┌──────────────┐
     │  apps/web     │ ────────────────> │ apps/backend  │
     │  (Next.js)    │   REST + WS       │ (FastAPI)     │
     └──────────────┘                    └──────────────┘
```

---

## 3. コンポーネント構成

### 3.1 バックエンド (apps/backend)

FastAPI ベースの非同期 Python バックエンド。Lifespan Manager パターンで
アプリケーションのライフサイクルを管理する。

```
apps/backend/
├── src/grc_backend/
│   ├── main.py              # FastAPI app ファクトリ + Lifespan
│   ├── config.py            # pydantic-settings 環境設定
│   ├── api/
│   │   ├── deps.py          # FastAPI 依存性注入 (DI)
│   │   ├── routes/
│   │   │   ├── auth.py      # 認証 (JWT login/register/refresh)
│   │   │   ├── projects.py  # プロジェクト CRUD
│   │   │   ├── tasks.py     # タスク CRUD
│   │   │   ├── interviews.py # インタビュー管理
│   │   │   ├── templates.py # テンプレート管理
│   │   │   ├── reports.py   # レポート生成・エクスポート
│   │   │   ├── knowledge.py # ナレッジベース
│   │   │   ├── models.py    # AI モデル一覧・接続テスト
│   │   │   ├── demo.py      # デモデータ管理 (非本番)
│   │   │   └── health.py    # ヘルスチェック
│   │   └── websocket/
│   │       └── interview_ws.py  # WebSocket リアルタイム対話
│   ├── core/
│   │   ├── errors.py        # エラー型定義・ハンドラ
│   │   ├── logging.py       # 構造化ログ (JSON/Console)
│   │   └── security.py      # セキュリティミドルウェア
│   ├── services/
│   │   ├── transcription_service.py  # 音声文字起こし
│   │   ├── synthesis_service.py      # 音声合成 (TTS)
│   │   ├── report_generator.py       # レポート生成
│   │   ├── audit_service.py          # 監査ログ
│   │   ├── knowledge_service.py      # ナレッジベース管理
│   │   └── sso_service.py            # SSO 連携
│   └── demo/
│       ├── data.py          # デモ用 GRC マスターデータ
│       ├── seeder.py        # DB シーダー
│       └── cli.py           # CLI ツール
├── migrations/              # Alembic マイグレーション
├── tests/                   # pytest テストスイート
└── Dockerfile               # マルチステージビルド
```

#### API ルート設計

全エンドポイントは `/api/v1` プレフィックス配下で提供される。

| パス                              | メソッド          | 説明                    |
|----------------------------------|------------------|------------------------|
| `/api/v1/health`                 | GET              | ヘルスチェック            |
| `/api/v1/auth/login`             | POST             | JWT ログイン             |
| `/api/v1/auth/register`          | POST             | ユーザー登録             |
| `/api/v1/auth/refresh`           | POST             | トークンリフレッシュ      |
| `/api/v1/auth/me`                | GET              | 現在ユーザー情報          |
| `/api/v1/projects`               | GET, POST        | プロジェクト一覧・作成    |
| `/api/v1/projects/{id}`          | GET, PUT, DELETE | プロジェクト詳細・更新    |
| `/api/v1/tasks`                  | GET, POST        | タスク一覧・作成          |
| `/api/v1/tasks/{id}`             | GET              | タスク詳細               |
| `/api/v1/interviews`             | GET, POST        | インタビュー一覧・作成    |
| `/api/v1/interviews/{id}`        | GET              | インタビュー詳細          |
| `/api/v1/interviews/{id}/start`  | POST             | インタビュー開始          |
| `/api/v1/interviews/{id}/complete`| POST            | インタビュー完了          |
| `/api/v1/interviews/{id}/stream` | WebSocket        | リアルタイム対話ストリーム |
| `/api/v1/templates`              | GET, POST        | テンプレート一覧・作成    |
| `/api/v1/templates/{id}`         | GET, PUT, DELETE | テンプレート詳細・更新    |
| `/api/v1/templates/{id}/clone`   | POST             | テンプレート複製          |
| `/api/v1/templates/{id}/publish` | POST             | テンプレート公開          |
| `/api/v1/reports`                | GET              | レポート一覧             |
| `/api/v1/reports/generate`       | POST             | レポート生成             |
| `/api/v1/reports/{id}/export`    | GET              | レポートエクスポート      |
| `/api/v1/knowledge`              | GET, POST        | ナレッジベース管理        |
| `/api/v1/models`                 | GET              | AI モデル一覧            |
| `/api/v1/models/recommended`     | GET              | 推奨モデル               |
| `/api/v1/models/providers`       | GET              | プロバイダ一覧           |
| `/api/v1/models/test-connection` | POST             | 接続テスト               |
| `/api/v1/demo/*`                 | POST             | デモデータ管理 (非本番)   |

#### 依存性注入 (DI) パターン

FastAPI の `Depends()` を活用し、以下の依存性を注入する。

```python
# deps.py で定義された型エイリアス
DBSession    = Annotated[AsyncSession, Depends(get_db)]
CurrentUser  = Annotated[User, Depends(get_current_active_user)]
AdminUser    = Annotated[User, Depends(require_admin)]
ManagerUser  = Annotated[User, Depends(require_manager_or_admin)]
AIProviderDep = Annotated[AIProvider, Depends(get_ai_provider)]
```

### 3.2 フロントエンド (apps/web)

Next.js 15 (App Router) + React 19 によるモダン SPA。Turbopack による
高速 HMR を開発時に利用。

```
apps/web/src/
├── app/
│   ├── layout.tsx           # ルートレイアウト
│   ├── providers.tsx        # QueryClient + I18n プロバイダ
│   ├── page.tsx             # ランディングページ
│   ├── error.tsx            # グローバルエラーバウンダリ
│   ├── (auth)/
│   │   ├── login/page.tsx   # ログインページ
│   │   └── register/page.tsx # 新規登録ページ
│   ├── (dashboard)/
│   │   ├── layout.tsx       # ダッシュボードレイアウト (サイドバー)
│   │   ├── error.tsx        # ダッシュボードエラーバウンダリ
│   │   ├── dashboard/page.tsx   # ダッシュボードホーム
│   │   ├── projects/
│   │   │   ├── page.tsx         # プロジェクト一覧
│   │   │   └── [id]/page.tsx    # プロジェクト詳細
│   │   ├── tasks/
│   │   │   ├── page.tsx         # タスク一覧
│   │   │   └── [id]/page.tsx    # タスク詳細
│   │   ├── templates/
│   │   │   ├── page.tsx         # テンプレート一覧
│   │   │   └── [id]/page.tsx    # テンプレート詳細
│   │   ├── reports/
│   │   │   ├── page.tsx         # レポート一覧
│   │   │   └── [id]/page.tsx    # レポート詳細
│   │   ├── knowledge/page.tsx   # ナレッジベース
│   │   └── settings/page.tsx    # 設定
│   └── interviews/
│       └── [id]/
│           ├── page.tsx         # インタビュー実施画面
│           └── error.tsx        # インタビューエラーバウンダリ
├── components/
│   ├── VoiceInput.tsx       # 音声入力コンポーネント
│   ├── LanguageSelector.tsx # 言語選択
│   ├── theme-provider.tsx   # テーマプロバイダ (next-themes)
│   ├── theme-toggle.tsx     # ダークモードトグル
│   └── ui/                  # 共通 UI コンポーネント群
│       ├── button.tsx
│       ├── card.tsx
│       ├── badge.tsx
│       ├── input.tsx
│       ├── select.tsx
│       ├── modal.tsx
│       ├── toast.tsx
│       ├── skeleton.tsx
│       ├── empty-state.tsx
│       ├── breadcrumb.tsx
│       └── confirm-dialog.tsx
├── hooks/
│   ├── useAudioRecorder.ts  # 音声録音 Hook
│   └── useAudioPlayer.ts   # 音声再生 Hook
└── lib/
    ├── api-client.ts        # Axios インスタンス + JWT インターセプタ
    ├── websocket.ts         # WebSocket クライアント (自動再接続)
    ├── auth.ts              # 認証ユーティリティ
    ├── cn.ts                # Tailwind クラス結合 (clsx + tailwind-merge)
    └── i18n.tsx             # 多言語対応 (next-intl)
```

#### 状態管理戦略

```
┌─────────────────────────────────────────────────────────┐
│                   状態管理レイヤー                        │
│                                                         │
│  ┌─────────────────┐     ┌──────────────────────────┐  │
│  │    Zustand       │     │    TanStack Query        │  │
│  │                  │     │                          │  │
│  │ - 認証状態        │     │ - サーバーデータキャッシュ  │  │
│  │ - UI 状態         │     │ - 自動再検証 (staleTime) │  │
│  │ - テーマ設定      │     │ - 楽観的更新             │  │
│  │ - WebSocket 状態  │     │ - ページネーション        │  │
│  └─────────────────┘     └──────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │    React Hook Form + Zod                         │   │
│  │    - フォームバリデーション                         │   │
│  │    - 型安全なフォーム状態                           │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 3.3 共通パッケージ - grc_core (packages/@grc/core)

ドメインモデル、スキーマ、リポジトリ、データベース接続を提供する共有パッケージ。

```
packages/@grc/core/src/grc_core/
├── database.py          # DatabaseManager (async engine + session)
├── enums.py             # ドメイン列挙型
├── models/
│   ├── base.py          # SQLAlchemy Base + TimestampMixin
│   ├── organization.py  # 組織モデル
│   ├── user.py          # ユーザーモデル
│   ├── project.py       # プロジェクトモデル
│   ├── task.py          # タスク (InterviewTask) モデル
│   ├── template.py      # テンプレートモデル
│   ├── interview.py     # インタビューモデル
│   ├── interviewee.py   # 被面談者モデル
│   ├── transcript.py    # トランスクリプトエントリモデル
│   ├── report.py        # レポートモデル
│   ├── knowledge.py     # ナレッジアイテムモデル
│   └── audit_log.py     # 監査ログモデル
├── schemas/             # Pydantic スキーマ (API 入出力)
│   ├── base.py
│   ├── user.py
│   ├── project.py
│   ├── task.py
│   ├── interview.py
│   ├── template.py
│   ├── transcript.py
│   ├── report.py
│   └── knowledge.py
└── repositories/        # Repository パターン (DB アクセス抽象化)
    ├── base.py          # BaseRepository (汎用 CRUD)
    ├── user.py
    ├── project.py
    ├── task.py
    ├── interview.py
    └── template.py
```

#### ドメインモデル ER 図

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Organization │     │    User      │     │   Project    │
├──────────────┤     ├──────────────┤     ├──────────────┤
│ id (UUID)    │◄──┐ │ id (UUID)    │  ┌─>│ id (UUID)    │
│ name         │   │ │ email        │  │  │ name         │
│ created_at   │   │ │ name         │  │  │ description  │
│ updated_at   │   └─│ org_id (FK)  │  │  │ status       │
└──────────────┘     │ role         │  │  │ client_name  │
                     │ created_at   │  │  │ created_at   │
                     └──────────────┘  │  └──────┬───────┘
                                       │         │
                                       │         │ 1:N
                                       │         ▼
┌──────────────┐                       │  ┌──────────────┐
│  Template    │                       │  │InterviewTask │
├──────────────┤                       │  ├──────────────┤
│ id (UUID)    │◄──────────────────────┼─ │ id (UUID)    │
│ name         │                       │  │ name         │
│ use_case_type│                       │  │ project_id   │
│ questions[]  │                       │  │ template_id  │
│ is_published │                       │  │ use_case_type│
│ created_at   │                       │  │ status       │
└──────────────┘                       │  │ target_count │
                                       │  │ settings{}   │
                                       │  └──────┬───────┘
                                       │         │
                                       │         │ 1:N
                                       │         ▼
┌──────────────┐                       │  ┌──────────────┐
│ Interviewee  │◄──────────────────────┼──│  Interview   │
├──────────────┤                       │  ├──────────────┤
│ id (UUID)    │                       │  │ id (UUID)    │
│ name         │                       │  │ task_id (FK) │
│ email        │                       │  │ interviewee_id│
│ department   │                       │  │ status       │
└──────────────┘                       │  │ language     │
                                       │  │ summary      │
                                       │  │ ai_analysis  │
                                       │  │ started_at   │
                                       │  │ completed_at │
                                       │  └──────┬───────┘
                                       │         │
                                       │         │ 1:N
                                       │         ▼
┌──────────────┐                       │  ┌─────────────────┐
│   Report     │                       │  │TranscriptEntry  │
├──────────────┤                       │  ├─────────────────┤
│ id (UUID)    │◄──────────────────────┘  │ id (UUID)       │
│ interview_id │                          │ interview_id    │
│ task_id      │                          │ speaker (Enum)  │
│ report_type  │                          │ content         │
│ content      │                          │ timestamp_ms    │
│ status       │                          │ metadata{}      │
│ created_at   │                          └─────────────────┘
└──────────────┘

┌──────────────┐     ┌──────────────┐
│KnowledgeItem │     │  AuditLog    │
├──────────────┤     ├──────────────┤
│ id (UUID)    │     │ id (UUID)    │
│ title        │     │ user_id      │
│ content      │     │ action       │
│ embedding    │     │ resource_type│
│ (pgvector)   │     │ resource_id  │
│ metadata{}   │     │ details{}    │
│ created_at   │     │ created_at   │
└──────────────┘     └──────────────┘
```

#### GRC ユースケース列挙型 (UseCaseType)

本システムは以下の GRC 業務領域をサポートする。

| カテゴリ        | ユースケース                      | コード                       |
|---------------|--------------------------------|------------------------------|
| コンプライアンス | コンプライアンス意識調査           | `compliance_survey`          |
|               | 内部通報調査                     | `whistleblower_investigation`|
|               | 規程遵守確認                     | `regulation_compliance`      |
|               | 下請法対応                       | `subcontract_act`            |
|               | 個人情報取扱                     | `privacy_assessment`         |
|               | 贈収賄リスク                     | `bribery_risk`               |
| 内部監査       | 業務プロセスヒアリング             | `process_review`             |
|               | 取引確認                         | `transaction_verification`   |
|               | 異常取引調査                     | `anomaly_investigation`      |
|               | 統制評価 (J-SOX)                 | `control_evaluation`         |
|               | IT 統制評価                      | `it_control`                 |
|               | フォローアップ                    | `followup`                   |
| リスク管理     | リスクアセスメント                 | `risk_assessment`            |
|               | BCP/BCM 評価                     | `bcp_evaluation`             |
|               | サイバーリスク                    | `cyber_risk`                 |
|               | 第三者リスク                     | `third_party_risk`           |
|               | ESG リスク                       | `esg_risk`                   |
| ガバナンス     | 取締役会実効性                    | `board_effectiveness`        |
|               | 内部統制システム                  | `internal_control_system`    |
|               | グループガバナンス                | `group_governance`           |
| ナレッジ管理   | 暗黙知形式知化                    | `tacit_knowledge`            |
|               | 引継ぎ                           | `handover`                   |
|               | ベストプラクティス                | `best_practice`              |

### 3.4 共通パッケージ - grc_ai (packages/@grc/ai)

マルチクラウド AI プロバイダの抽象化レイヤー。Provider Pattern + Factory
パターンにより、プロバイダ切り替えを設定のみで実現する。

```
packages/@grc/ai/src/grc_ai/
├── base.py              # AIProvider Protocol (chat, stream_chat, embed)
├── config.py            # AIConfig (プロバイダ別設定)
├── factory.py           # create_ai_provider() ファクトリ
├── models.py            # モデルカタログ
├── providers/
│   ├── azure_openai.py  # Azure OpenAI 実装
│   ├── aws_bedrock.py   # AWS Bedrock 実装
│   ├── gcp_vertex.py    # GCP Vertex AI 実装
│   └── ollama_provider.py # Ollama ローカル LLM 実装
├── dialogue/
│   ├── interview_agent.py # InterviewAgent (対話制御エンジン)
│   └── prompts.py         # PromptManager (プロンプトテンプレート)
├── speech/
│   ├── base.py            # SpeechToText / TextToSpeech Protocol
│   ├── factory.py         # create_speech_provider() ファクトリ
│   ├── azure_speech.py    # Azure Cognitive Speech 実装
│   ├── aws_speech.py      # AWS Transcribe + Polly 実装
│   └── gcp_speech.py      # GCP Speech-to-Text / Text-to-Speech 実装
└── translation/
    ├── base.py            # Translation Protocol
    ├── factory.py         # create_translation_provider() ファクトリ
    ├── azure_translate.py # Azure Translator 実装
    ├── aws_translate.py   # AWS Translate 実装
    └── gcp_translate.py   # GCP Translation 実装
```

#### AI プロバイダ Protocol

```python
@runtime_checkable
class AIProvider(Protocol):
    """全プロバイダが準拠すべき Protocol"""

    async def chat(messages, *, model, temperature, max_tokens) -> ChatResponse: ...
    async def stream_chat(messages, *, model, temperature, max_tokens) -> AsyncIterator[ChatChunk]: ...
    async def embed(text, *, model) -> EmbeddingResponse: ...
    async def embed_batch(texts, *, model) -> list[EmbeddingResponse]: ...
    async def close() -> None: ...
```

#### AI プロバイダ別デフォルトモデル

| プロバイダ          | チャットモデル                          | Embedding モデル        |
|-------------------|-----------------------------------------|------------------------|
| Microsoft Foundry | gpt-5-nano / gpt-5.2                   | text-embedding-3-large |
| AWS Bedrock       | Claude Opus 4.6 / Claude Haiku 4.5     | (Bedrock 内蔵)         |
| GCP Vertex AI     | Gemini 3 Pro / Gemini 3 Flash Preview  | (Vertex AI 内蔵)       |
| Ollama (Local)    | gemma3:1b                              | nomic-embed-text       |

---

## 4. データフロー

### 4.1 インタビューライフサイクル

ユーザーがプロジェクトを作成してから、レポートが生成されるまでの全体フロー。

```
  ユーザー操作                  システム処理                    データストア
  ──────────                ──────────                  ──────────

  [1] プロジェクト作成  ──>  POST /projects  ──────────>  PostgreSQL
                                                         (projects テーブル)

  [2] テンプレート選択  ──>  GET /templates  <──────────  PostgreSQL
      or 新規作成            POST /templates ──────────>  (templates テーブル)

  [3] タスク作成       ──>  POST /tasks     ──────────>  PostgreSQL
      (テンプレート紐付)                                   (interview_tasks テーブル)

  [4] インタビュー作成  ──>  POST /interviews ─────────>  PostgreSQL
                                                         (interviews テーブル)

  [5] インタビュー開始  ──>  WebSocket 接続
      (/interviews/{id}/stream)
         │
         │   ┌─────────────────────────────────────────────────┐
         │   │         WebSocket リアルタイム対話ループ           │
         │   │                                                 │
         │   │  ユーザー発話                                    │
         │   │    │                                            │
         │   │    ▼                                            │
         │   │  [音声入力の場合]                                │
         │   │    │                                            │
         │   │    ▼                                            │
         │   │  Speech-to-Text ──> テキスト変換                 │
         │   │    │                                            │
         │   │    ▼                                            │
         │   │  InterviewAgent.respond_stream()                │
         │   │    │                                            │
         │   │    ├──> AIProvider.stream_chat() ──> LLM API    │
         │   │    │                                            │
         │   │    ▼                                            │
         │   │  AI レスポンス (ストリーミング)                    │
         │   │    │                                            │
         │   │    ├──> TranscriptEntry 保存 ──> PostgreSQL     │
         │   │    │                                            │
         │   │    ▼                                            │
         │   │  [音声出力の場合]                                │
         │   │    │                                            │
         │   │    ▼                                            │
         │   │  Text-to-Speech ──> 音声合成                    │
         │   │    │                                            │
         │   │    ▼                                            │
         │   │  クライアントへ送信                               │
         │   │                                                 │
         │   │  [ループ継続 or 終了]                            │
         │   └─────────────────────────────────────────────────┘
         │
         ▼
  [6] インタビュー終了  ──>  InterviewAgent.end()
                            InterviewAgent.summarize()
                              │
                              ├──> summary + ai_analysis 保存
                              │    ──> PostgreSQL (interviews テーブル)
                              │
                              ▼
  [7] レポート生成     ──>  POST /reports/generate
                              │
                              ├──> ReportGenerator
                              │    (トランスクリプト分析)
                              │
                              ▼
                            レポート保存 ──> PostgreSQL
                                            (reports テーブル)

  [8] ナレッジ蓄積     ──>  KnowledgeService
                              │
                              ├──> AIProvider.embed()
                              │    (ベクトル化)
                              │
                              ▼
                            KnowledgeItem 保存 ──> PostgreSQL
                                                   (pgvector)
```

### 4.2 WebSocket メッセージプロトコル

クライアントからサーバーへ送信するメッセージ形式。

```
クライアント -> サーバー:
{
    "type": "message" | "audio_chunk" | "control",
    "payload": {
        "content": "テキストメッセージ",          // type: message
        "audio": "base64 エンコード音声データ",   // type: audio_chunk
        "action": "pause" | "resume" | "end"    // type: control
    }
}

サーバー -> クライアント:
{
    "type": "ai_response" | "transcription" | "status" | "error",
    "payload": {
        "content": "AI の応答テキスト",
        "isPartial": true/false,     // ストリーミング中間結果
        "isFinal": true/false,       // 最終結果フラグ
        "speaker": "ai" | "interviewee",
        "text": "文字起こし結果",
        "timestamp": 1234567890,
        "status": "connected" | "paused" | "resumed" | "completed",
        "summary": { ... },          // 完了時サマリー
        "message": "エラーメッセージ"
    }
}
```

### 4.3 JWT 認証フロー

```
[ログイン]
  Client                          Server
    │                               │
    │  POST /auth/login             │
    │  (email + password)           │
    │──────────────────────────────>│
    │                               │  パスワード検証 (bcrypt)
    │                               │  JWT 生成 (HS256)
    │  { access_token,              │
    │    refresh_token }            │
    │<──────────────────────────────│
    │                               │
    │  API リクエスト               │
    │  Authorization: Bearer {JWT}  │
    │──────────────────────────────>│
    │                               │  JWT 検証 (python-jose)
    │                               │  ユーザー取得
    │  レスポンス                    │
    │<──────────────────────────────│

[トークンリフレッシュ - axios インターセプタによる自動実行]
    │                               │
    │  401 Unauthorized             │
    │<──────────────────────────────│
    │                               │
    │  POST /auth/refresh           │
    │  { refresh_token }            │
    │──────────────────────────────>│
    │                               │  refresh_token 検証
    │  { new_access_token,          │  新しいトークンペア生成
    │    new_refresh_token }        │
    │<──────────────────────────────│
    │                               │
    │  元のリクエストをリトライ       │
    │──────────────────────────────>│
```

---

## 5. 技術スタック

### 5.1 バックエンド

| カテゴリ         | 技術                        | バージョン    | 用途                          |
|----------------|----------------------------|-------------|-------------------------------|
| Web Framework  | FastAPI                    | >= 0.115.6  | 非同期 REST API + WebSocket    |
| ASGI Server    | Uvicorn                    | >= 0.34.0   | 本番/開発 ASGI サーバー         |
| 型バリデーション  | Pydantic                   | >= 2.10.0   | リクエスト/レスポンス検証        |
| 設定管理        | pydantic-settings          | >= 2.7.0    | 環境変数マッピング              |
| ORM            | SQLAlchemy (async)         | >= 2.0.37   | 非同期 DB アクセス              |
| DB ドライバ     | asyncpg                    | >= 0.30.0   | PostgreSQL 非同期ドライバ       |
| マイグレーション  | Alembic                    | >= 1.14.0   | スキーママイグレーション         |
| キャッシュ       | redis-py                   | >= 5.2.0    | Redis クライアント              |
| JWT 認証        | python-jose                | >= 3.3.0    | JWT エンコード/デコード         |
| パスワード       | passlib + bcrypt           | >= 1.7.4    | パスワードハッシュ              |
| ログ            | 標準 logging (StructuredLogger) | -      | JSON 構造化ログ                |
| テスト          | pytest + pytest-asyncio    | >= 8.3.0    | 非同期テスト                   |
| Linter         | Ruff                       | >= 0.8.0    | Python リンター + フォーマッタ   |
| 型チェック       | mypy                       | >= 1.14.0   | 静的型チェック                  |

### 5.2 フロントエンド

| カテゴリ         | 技術                        | バージョン    | 用途                          |
|----------------|----------------------------|-------------|-------------------------------|
| Framework      | Next.js (App Router)       | 15.x       | SSR/SSG + ルーティング          |
| UI Library     | React                      | 19.x       | コンポーネントベース UI          |
| State (Client) | Zustand                    | 5.x        | クライアント状態管理             |
| State (Server) | TanStack Query             | 5.x        | サーバーデータキャッシュ          |
| HTTP Client    | Axios                      | 1.7.x      | REST API クライアント           |
| WebSocket      | Native WebSocket           | -          | リアルタイム通信                |
| Forms          | React Hook Form + Zod      | 7.x / 3.x  | フォーム管理 + バリデーション    |
| Styling        | Tailwind CSS               | 3.4.x      | ユーティリティファースト CSS      |
| Animation      | Framer Motion              | 11.x       | UI アニメーション               |
| Icons          | Lucide React               | 0.468.x    | アイコンライブラリ              |
| I18n           | next-intl                  | 3.x        | 多言語対応 (日本語デフォルト)    |
| Theme          | next-themes                | 0.4.x      | ダークモード                   |
| Date           | date-fns                   | 4.x        | 日付処理                      |
| E2E Test       | Playwright                 | 1.49.x     | E2E テスト                    |
| Unit Test      | Jest + Testing Library     | 29.x       | コンポーネントテスト            |
| Type Check     | TypeScript                 | 5.7.x      | 型安全性                      |

### 5.3 インフラストラクチャ

| カテゴリ         | 技術                        | バージョン    | 用途                          |
|----------------|----------------------------|-------------|-------------------------------|
| Database       | PostgreSQL + pgvector      | 16         | メインデータストア + ベクトル検索 |
| Cache          | Redis                      | 7          | セッション・キャッシュ           |
| Container      | Docker + Docker Compose    | -          | ローカル開発環境               |
| IaC            | Terraform                  | >= 1.9.0   | インフラ定義・プロビジョニング   |
| Cloud          | Azure (primary)            | -          | 本番デプロイ先                 |
| Registry       | Azure Container Registry   | -          | コンテナイメージ管理            |
| Compute        | Azure App Service (Linux)  | -          | バックエンド実行環境            |
| Frontend Host  | Azure Static Web Apps      | -          | フロントエンド配信              |
| AI Service     | Microsoft Foundry          | -          | LLM + Embedding              |
| Speech         | Azure Cognitive Speech     | -          | STT + TTS                    |
| Storage        | Azure Blob Storage         | -          | ファイルストレージ              |
| Monitoring     | Application Insights       | -          | APM + ログ集約                |
| Secret Mgmt    | Azure Key Vault            | -          | シークレット管理               |
| Local LLM      | Ollama                     | latest     | ローカル開発用 LLM             |

### 5.4 開発ツールチェーン

| ツール           | 用途                                            |
|----------------|------------------------------------------------|
| pnpm           | TypeScript パッケージ管理 (ワークスペース対応)      |
| uv             | Python パッケージ管理 (ワークスペース対応)          |
| Ruff           | Python リンター + フォーマッタ (統合ツール)         |
| Prettier       | TypeScript/JSON フォーマッタ                     |
| ESLint         | TypeScript リンター                             |
| Turbopack      | Next.js 高速バンドラー (開発時)                   |

---

## 6. インフラストラクチャ

### 6.1 ローカル開発環境 (Docker Compose)

Docker Compose により、全サービスをワンコマンドで起動する。

```
docker-compose.yml
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐   │
│  │  postgres        │  │  redis           │  │  ollama      │   │
│  │  (pgvector:pg16) │  │  (redis:7-alpine)│  │  (optional)  │   │
│  │  :5432           │  │  :6379           │  │  :11434      │   │
│  └────────┬────────┘  └────────┬────────┘  └──────────────┘   │
│           │ backend network     │                               │
│  ┌────────┴────────────────────┴───────────────────────────┐   │
│  │                    backend                               │   │
│  │  FastAPI (uvicorn --reload)                              │   │
│  │  :8001 -> :8000                                         │   │
│  │  Volume: ./apps/backend/src, ./packages/@grc/*/src      │   │
│  └────────────────────────┬────────────────────────────────┘   │
│                            │ frontend network                    │
│  ┌────────────────────────┴────────────────────────────────┐   │
│  │                      web                                 │   │
│  │  Next.js (next dev --turbopack)                          │   │
│  │  :3001 -> :3000                                         │   │
│  │  Volume: ./apps/web                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Networks: backend (backend <-> DB/Redis/Ollama)               │
│            frontend (web <-> backend)                           │
│                                                                 │
│  Profiles: local-llm (Ollama を有効化)                          │
└─────────────────────────────────────────────────────────────────┘
```

**起動コマンド:**

```bash
# 基本起動 (PostgreSQL + Redis + Backend + Web)
docker-compose up -d

# ローカル LLM (Ollama) 付きで起動
docker-compose --profile local-llm up -d

# デモデータ自動投入 (SEED_DEMO=true がデフォルト)
docker-compose up -d
```

### 6.2 Azure 本番環境 (Terraform)

Terraform で管理される Azure リソース群。環境 (dev/staging/prod) により
SKU が自動的にスケーリングされる。

```
Azure Resource Group: {project}-{env}-rg
│
├── Virtual Network (10.0.0.0/16)
│   ├── app-subnet (10.0.1.0/24)  -- App Service 用
│   └── db-subnet  (10.0.2.0/24)  -- PostgreSQL 用 (Private Link)
│
├── Azure App Service (Linux)
│   ├── Backend API コンテナ
│   ├── Health Check: /api/v1/health
│   ├── Managed Identity (SystemAssigned)
│   └── VNet 統合 (app-subnet)
│
├── Azure Static Web Apps
│   └── Next.js フロントエンド
│
├── PostgreSQL Flexible Server (v16)
│   ├── Private DNS Zone (privatelink.postgres.database.azure.com)
│   ├── Extensions: vector, uuid-ossp
│   ├── dev: B_Standard_B2s / prod: GP_Standard_D4s_v3
│   └── Backup: dev 7日 / prod 35日 (geo-redundant)
│
├── Azure Cache for Redis
│   ├── TLS 1.2 強制
│   ├── dev: Basic C0 / prod: Standard C2
│   └── maxmemory-policy: volatile-lru
│
├── Azure Cognitive Services
│   ├── OpenAI (S0) - GPT-5.2, GPT-5-nano, Claude models
│   ├── Speech Services (S0) - STT + TTS
│   └── Embedding: text-embedding-3-large
│
├── Storage Account
│   ├── audio-files コンテナ (private)
│   ├── reports コンテナ (private)
│   ├── Versioning 有効
│   └── dev: LRS / prod: GRS
│
├── Container Registry
│   ├── dev: Basic / prod: Premium
│   └── Admin アクセス有効
│
├── Key Vault
│   ├── RBAC 認証
│   └── Soft Delete 7日
│
├── Application Insights + Log Analytics
│   └── 保持期間 30日
│
└── Monitoring / Alerting
    ├── API Health Alert (Severity 1)
    ├── API Response Time Alert (> 5秒, Severity 2)
    ├── Database CPU Alert (> 80%, Severity 2)
    ├── Redis Memory Alert (> 80%, Severity 2)
    ├── Diagnostic Settings (API + DB)
    └── Smart Detection (failure anomalies)
```

### 6.3 環境別構成

| 項目                     | Development      | Staging              | Production           |
|------------------------|------------------|---------------------|---------------------|
| App Service SKU         | B2               | B2                  | P2v3                |
| PostgreSQL SKU          | B_Standard_B2s   | B_Standard_B2s      | GP_Standard_D4s_v3  |
| Redis SKU               | Basic C0         | Basic C0            | Standard C2         |
| Container Registry      | Basic            | Basic               | Premium             |
| Storage Replication     | LRS              | LRS                 | GRS                 |
| DB Backup               | 7日              | 7日                  | 35日 (geo-redundant) |
| Always On               | No               | No                  | Yes                 |
| HSTS                    | Off              | Off                 | On                  |
| CSP                     | Off              | Off                 | On                  |
| Rate Limiting           | Off              | On (120 req/min)    | On (60 req/min)     |
| API Docs                | 有効             | 無効                 | 無効                 |
| Demo Endpoints          | 有効             | 有効                 | 無効                 |

---

## 7. セキュリティアーキテクチャ

### 7.1 レイヤード セキュリティ

```
                    ┌─────────────────────────────────┐
                    │         セキュリティ層             │
                    └─────────────────────────────────┘

  [Layer 1] ネットワーク
  ─────────────────────────────────────────────────────
  - VNet 分離 (App Subnet / DB Subnet)
  - PostgreSQL Private Link (パブリックアクセス無効)
  - Redis TLS 1.2 強制
  - HTTPS Only (App Service)

  [Layer 2] アプリケーションミドルウェア (security.py)
  ─────────────────────────────────────────────────────
  - CORS 制御 (許可オリジン明示指定)
  - セキュリティヘッダー
      X-Content-Type-Options: nosniff
      X-Frame-Options: DENY
      X-XSS-Protection: 1; mode=block
      Referrer-Policy: strict-origin-when-cross-origin
      Strict-Transport-Security (本番のみ)
      Content-Security-Policy (本番のみ)
  - Rate Limiting (Sliding Window アルゴリズム)
  - IP Allowlist / Blocklist
  - リクエストサイズ制限 (10MB)
  - Request ID 追跡 (X-Request-ID)

  [Layer 3] 認証・認可
  ─────────────────────────────────────────────────────
  - JWT 認証 (HS256, python-jose)
  - Access Token (30分有効)
  - Refresh Token (7日有効)
  - ロールベースアクセス制御 (RBAC)
      admin       - 全機能アクセス
      manager     - プロジェクト管理 + レポート
      interviewer - インタビュー実施
      viewer      - 閲覧のみ
  - パスワードハッシュ (bcrypt)

  [Layer 4] API キー管理 + CSRF
  ─────────────────────────────────────────────────────
  - APIKeyManager: HMAC-SHA256 ベースのキー生成・検証
  - CSRFProtection: セッション紐付きトークン
  - タイムスタンプベースのトークン有効期限 (1時間)

  [Layer 5] データ保護
  ─────────────────────────────────────────────────────
  - 構造化ログの機密データマスキング (password, token, api_key 等)
  - Azure Key Vault によるシークレット管理
  - 環境変数による設定注入 (.env)
  - 本番環境でのデフォルト SECRET_KEY 使用禁止 (バリデータ)

  [Layer 6] 監査
  ─────────────────────────────────────────────────────
  - AuditLog モデル (全操作記録)
  - 構造化ログによるリクエスト追跡
  - Application Insights 統合
  - Diagnostic Settings (API / DB ログ)
```

### 7.2 機密データマスキング

ログ出力時に以下のフィールド名を含むデータは自動的に `[REDACTED]` に置換される。

```
password, api_key, secret, token, authorization,
cookie, credential, private_key, access_token,
refresh_token, api_secret, client_secret
```

### 7.3 セキュリティ設定フロー

```python
# main.py での設定
security_config = SecurityConfig(
    cors_origins=settings.cors_origins,
    rate_limit_enabled=settings.rate_limit_enabled,
    rate_limit_requests=settings.rate_limit_requests,
    rate_limit_window=settings.rate_limit_window,
    hsts_enabled=settings.is_production,
    csp_enabled=settings.is_production,
    debug=settings.debug,
)
setup_security(app, security_config)
```

---

## 8. 拡張ポイント

本システムは以下の拡張ポイントを持ち、機能追加を容易にする設計となっている。

### 8.1 新しい AI プロバイダの追加

`AIProvider` Protocol を実装し、`factory.py` に登録するだけで新プロバイダを追加可能。

```python
# 1. providers/ に新しいプロバイダクラスを実装
class NewProvider:
    async def chat(self, messages, **kwargs) -> ChatResponse: ...
    async def stream_chat(self, messages, **kwargs) -> AsyncIterator[ChatChunk]: ...
    async def embed(self, text, **kwargs) -> EmbeddingResponse: ...
    async def embed_batch(self, texts, **kwargs) -> list[EmbeddingResponse]: ...
    async def close(self) -> None: ...

# 2. AIProviderType に新しい列挙値を追加
class AIProviderType(StrEnum):
    NEW_PROVIDER = "new_provider"

# 3. factory.py の match 文に追加
case AIProviderType.NEW_PROVIDER:
    return NewProvider(config.new_provider)
```

### 8.2 新しい音声プロバイダの追加

`SpeechToTextProvider` / `TextToSpeechProvider` Protocol に準拠する
クラスを実装し、`speech/factory.py` に登録する。

```
実装対象 Protocol:
  - transcribe(audio_data, language, format, sample_rate) -> TranscriptionResult
  - transcribe_stream(audio_stream, ...) -> AsyncIterator[TranscriptionResult]
  - synthesize(text, language, voice_id, ...) -> SynthesisResult
  - synthesize_stream(text, ...) -> AsyncIterator[bytes]
  - list_voices(language) -> list[VoiceInfo]
```

### 8.3 新しい GRC ユースケースの追加

1. `grc_core/enums.py` の `UseCaseType` に新しい値を追加
2. `grc_ai/dialogue/prompts.py` にユースケース固有のプロンプトを追加
3. 必要に応じて `ReportType` を追加しレポート生成ロジックを拡張

### 8.4 新しいレポートタイプの追加

1. `grc_core/enums.py` の `ReportType` に新しい値を追加
2. `services/report_generator.py` にレポート生成ロジックを追加
3. フロントエンドの `/reports` ページにレポート表示テンプレートを追加

### 8.5 新しい API ルートの追加

```python
# 1. apps/backend/src/grc_backend/api/routes/ に新しいルートファイルを作成
# 2. main.py に router を登録
app.include_router(new_route.router, prefix="/api/v1/new-resource", tags=["NewResource"])
```

### 8.6 新しいクラウドプロバイダの追加 (インフラ)

```
infrastructure/terraform/modules/ に新しいモジュールを追加:
  modules/aws/main.tf    - AWS リソース定義
  modules/gcp/main.tf    - GCP リソース定義
```

### 8.7 モバイルアプリ (計画中)

```
apps/mobile/ (Expo React Native)
  - 共通 API クライアント (lib/api-client.ts の移植)
  - WebSocket リアルタイム対話
  - ネイティブ音声入出力
  - オフライン対応 (計画)
```

---

## 付録

### A. 環境変数一覧

| 変数名                         | デフォルト値                          | 説明                       |
|-------------------------------|-------------------------------------|---------------------------|
| `ENVIRONMENT`                 | `development`                       | 実行環境                    |
| `DEBUG`                       | `false`                             | デバッグモード               |
| `SECRET_KEY`                  | `dev-secret-key-change-in-production` | JWT 署名鍵 (本番変更必須)  |
| `DATABASE_URL`                | `postgresql+asyncpg://...`          | PostgreSQL 接続文字列       |
| `REDIS_URL`                   | `redis://localhost:6379/0`          | Redis 接続文字列            |
| `AI_PROVIDER`                 | `azure`                             | AI プロバイダ選択            |
| `AZURE_OPENAI_API_KEY`        | -                                   | Microsoft Foundry API キー   |
| `AZURE_OPENAI_ENDPOINT`       | -                                   | Microsoft Foundry エンドポイント |
| `AZURE_OPENAI_DEPLOYMENT_NAME`| `gpt-5-nano`                        | Microsoft Foundry デプロイ名 |
| `AWS_ACCESS_KEY_ID`           | -                                   | AWS アクセスキー             |
| `AWS_SECRET_ACCESS_KEY`       | -                                   | AWS シークレットキー          |
| `AWS_REGION`                  | `ap-northeast-1`                    | AWS リージョン               |
| `AWS_BEDROCK_MODEL_ID`        | `anthropic.claude-sonnet-4-5-...`   | Bedrock モデル ID           |
| `GCP_PROJECT_ID`              | -                                   | GCP プロジェクト ID          |
| `GCP_LOCATION`                | `asia-northeast1`                   | GCP ロケーション             |
| `OLLAMA_BASE_URL`             | `http://localhost:11434`            | Ollama ベース URL           |
| `OLLAMA_MODEL`                | `gemma3:1b`                         | Ollama チャットモデル         |
| `OLLAMA_EMBEDDING_MODEL`      | `nomic-embed-text`                  | Ollama 埋め込みモデル        |
| `SPEECH_PROVIDER`             | `azure`                             | 音声プロバイダ選択           |
| `AZURE_SPEECH_KEY`            | -                                   | Azure Speech キー           |
| `AZURE_SPEECH_REGION`         | `japaneast`                         | Azure Speech リージョン      |
| `CORS_ORIGINS`                | `["http://localhost:3000", ...]`    | CORS 許可オリジン            |
| `RATE_LIMIT_ENABLED`          | `false`                             | レート制限有効化              |
| `RATE_LIMIT_REQUESTS`         | `100`                               | レート制限リクエスト数         |
| `RATE_LIMIT_WINDOW`           | `60`                                | レート制限ウィンドウ (秒)     |
| `LOG_LEVEL`                   | `INFO`                              | ログレベル                   |
| `JSON_LOGS`                   | `false`                             | JSON ログ出力                |
| `SEED_DEMO`                   | `false`                             | デモデータ自動投入            |
| `DB_POOL_SIZE`                | `10`                                | DB 接続プールサイズ           |
| `DB_MAX_OVERFLOW`             | `20`                                | DB 最大オーバーフロー接続     |

### B. 開発クイックスタート

```bash
# 1. リポジトリクローン
git clone <repository-url>
cd ai-interviewer

# 2. TypeScript 依存インストール
pnpm install

# 3. Python 依存インストール (uv 推奨)
uv sync

# 4. Docker サービス起動
docker-compose up -d

# 5. フロントエンド起動
pnpm dev

# 6. バックエンド起動 (別ターミナル)
pnpm dev:backend

# または Docker で全サービス起動
docker-compose up -d --build
```

### C. ドキュメント更新履歴

| 日付         | 版    | 内容                                  |
|-------------|------|---------------------------------------|
| 2026-02-15  | 1.0  | 初版作成                               |
