# AI Interview Tool

GRCアドバイザリー業務向けAIインタビューシステム

## 機能概要

- **AIによる対話形式インタビュー** - 質問自動生成、フォローアップ質問
- **リアルタイム音声認識・合成** - STT/TTS（Azure, AWS, GCP対応）
- **多言語対応** - 日本語・英語・中国語・韓国語、リアルタイム同時通訳
- **レポート自動生成** - 業務記述書、RCM、監査調書、要約レポート
- **ナレッジマネジメント** - RAG検索、ベクトル埋め込み、類似インタビュー検索
- **エンタープライズ機能** - SSO認証（Azure AD, Okta）、監査ログ

## 技術スタック (2026年最新版)

### Backend

| パッケージ | バージョン | 説明 |
| ---------- | ---------- | ---- |
| Python | 3.12+ | ランタイム |
| FastAPI | 0.115.6+ | Web フレームワーク |
| Pydantic | 2.10.0 | データバリデーション |
| SQLAlchemy | 2.0.37+ | ORM (async対応) |
| PostgreSQL | 16 | データベース (pgvector対応) |
| Redis | 7.x | キャッシュ・キュー |

### Frontend

| パッケージ | バージョン | 説明 |
| ---------- | ---------- | ---- |
| Next.js | 15.1.0 | Reactフレームワーク (Turbopack対応) |
| React | 19.0.0 | UIライブラリ |
| TanStack Query | 5.62.0 | サーバー状態管理 |
| Zustand | 5.0.2 | クライアント状態管理 |
| Tailwind CSS | 3.4.17 | スタイリング |

### Mobile

| パッケージ | バージョン | 説明 |
| ---------- | ---------- | ---- |
| Expo | 52.0.0 | React Native フレームワーク |
| React Native | 0.76.5 | モバイルUI |
| Expo Router | 4.0.0 | ナビゲーション |

### AI/LLM (マルチプロバイダー対応) - 2026年最新モデル

| プロバイダー | 最新フラッグシップ | エコノミー | 用途 |
| ------------ | ------------------ | ---------- | ---- |
| Azure AI Foundry | GPT-5.2, Claude Sonnet 4.6 Opus | GPT-5 Nano | エンタープライズ向け |
| OpenAI | GPT-5.2, o3 | GPT-5 Nano | 汎用・推論 |
| Anthropic | Claude Sonnet 4.6 Opus | Claude 4.6 Haiku | インタビュー対話 |
| AWS Bedrock | Claude Sonnet 4.6 Opus | Amazon Nova Lite | AWS環境向け |
| GCP Vertex AI | Gemini 3.0 Pro Preview | Gemini 3.0 Flash Lite | GCP環境向け (2Mコンテキスト) |

### Infrastructure (マルチクラウド対応)

- **Azure**: App Service, PostgreSQL, Redis, Azure AI Foundry (GPT-5.2 + Claude), Speech Services
- **AWS**: ECS Fargate, RDS, ElastiCache, Bedrock (Claude 4.6), Transcribe/Polly
- **GCP**: Cloud Run, Cloud SQL, Memorystore, Vertex AI (Gemini 3.0), Speech-to-Text

## 開発環境セットアップ

### 前提条件

- Docker Desktop
- Node.js 20+
- Python 3.12+
- pnpm 9+

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd ai-interviewer
```

### 2. 環境変数の設定

```bash
cp .env.example .env
# .env ファイルを編集して必要な値を設定
```

必須環境変数:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/aiinterviewer
REDIS_URL=redis://localhost:6379

# AI Provider (選択)
AI_PROVIDER=azure  # azure | aws | gcp | local
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key

# Speech (選択)
SPEECH_PROVIDER=azure  # azure | aws | gcp
AZURE_SPEECH_KEY=your-speech-key
AZURE_SPEECH_REGION=japaneast
```

### 3. 依存関係のインストール

```bash
# Node.js 依存関係
pnpm install

# Python 依存関係
cd apps/backend
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -e ".[dev]"
cd ../..
```

### 4. Docker サービスの起動

```bash
docker-compose up -d postgres redis
```

### 5. データベースマイグレーション

```bash
cd apps/backend
alembic upgrade head
cd ../..
```

### 6. 開発サーバーの起動

**Backend:**

```bash
cd apps/backend
uvicorn grc_backend.main:app --reload --port 8000
```

**Frontend (Web):**

```bash
cd apps/web
pnpm dev
```

**Frontend (Mobile):**

```bash
cd apps/mobile
pnpm start
```

### 7. アクセス

起動方法によってポート番号が異なります。

| 起動方法                    | Backend | Frontend | 説明             |
| --------------------------- | ------- | -------- | ---------------- |
| Direct (uvicorn / pnpm dev) | 8000    | 3000     | ローカル直接起動 |
| Docker (docker-compose up)  | 8001    | 3001     | Docker経由の起動 |

Direct 起動の場合:

- Frontend: <http://localhost:3000>
- Backend API: <http://localhost:8000>
- API Docs: <http://localhost:8000/api/docs>

Docker 起動の場合:

- Frontend: <http://localhost:3001>
- Backend API: <http://localhost:8001>
- API Docs: <http://localhost:8001/api/docs>

## プロジェクト構造

```text
ai-interviewer/
├── apps/
│   ├── backend/                 # FastAPI バックエンド
│   │   ├── src/grc_backend/
│   │   │   ├── api/routes/      # REST API エンドポイント
│   │   │   ├── api/websocket/   # WebSocket (リアルタイム対話)
│   │   │   └── services/        # ビジネスロジック
│   │   ├── tests/               # ユニット・結合テスト
│   │   └── migrations/          # Alembic マイグレーション
│   ├── web/                     # Next.js Webフロントエンド
│   │   └── src/
│   │       ├── app/             # App Router ページ
│   │       ├── components/      # Reactコンポーネント
│   │       ├── lib/             # ユーティリティ
│   │       └── locales/         # 多言語リソース
│   └── mobile/                  # React Native モバイルアプリ
│       └── src/
│           └── app/             # Expo Router ページ
├── packages/
│   └── @grc/
│       ├── core/                # ドメインモデル・リポジトリ
│       ├── ai/                  # AIプロバイダー抽象化
│       │   └── src/grc_ai/
│       │       ├── providers/   # Azure, AWS, GCP, Anthropic
│       │       ├── speech/      # STT/TTS抽象化
│       │       └── models.py    # LLMモデル定義
│       └── infrastructure/      # ストレージ・キュー抽象化
├── infrastructure/
│   └── terraform/               # マルチクラウドIaC
│       ├── modules/
│       │   ├── azure/           # Azure インフラ
│       │   ├── aws/             # AWS インフラ
│       │   └── gcp/             # GCP インフラ
│       └── environments/        # dev/staging/prod設定
├── docker-compose.yml
├── pnpm-workspace.yaml
└── pyproject.toml
```

## API エンドポイント

### Auth (`/api/v1/auth`)

| エンドポイント | メソッド | 説明 |
| -------------- | -------- | ---- |
| `/api/v1/auth/login` | POST | ログイン |
| `/api/v1/auth/register` | POST | ユーザー登録 |
| `/api/v1/auth/refresh` | POST | トークンリフレッシュ |
| `/api/v1/auth/me` | GET | 現在のユーザー情報 |

### Projects (`/api/v1/projects`)

| エンドポイント | メソッド | 説明 |
| -------------- | -------- | ---- |
| `/api/v1/projects` | GET | 案件一覧 |
| `/api/v1/projects` | POST | 案件作成 |
| `/api/v1/projects/{id}` | GET | 案件詳細 |
| `/api/v1/projects/{id}` | PUT | 案件更新 |
| `/api/v1/projects/{id}` | DELETE | 案件削除 |

### Tasks (`/api/v1/tasks`)

| エンドポイント | メソッド | 説明 |
| -------------- | -------- | ---- |
| `/api/v1/tasks` | GET | タスク一覧 |
| `/api/v1/tasks` | POST | タスク作成 |
| `/api/v1/tasks/{id}` | GET | タスク詳細 |
| `/api/v1/tasks/{id}` | PUT | タスク更新 |
| `/api/v1/tasks/{id}` | DELETE | タスク削除 |

### Interviews (`/api/v1/interviews`)

| エンドポイント | メソッド | 説明 |
| -------------- | -------- | ---- |
| `/api/v1/interviews` | GET | インタビュー一覧 |
| `/api/v1/interviews` | POST | インタビュー作成 |
| `/api/v1/interviews/{id}` | GET | インタビュー詳細 |
| `/api/v1/interviews/{id}` | PUT | インタビュー更新 |
| `/api/v1/interviews/{id}/start` | POST | インタビュー開始 |
| `/api/v1/interviews/{id}/pause` | POST | インタビュー一時停止 |
| `/api/v1/interviews/{id}/resume` | POST | インタビュー再開 |
| `/api/v1/interviews/{id}/complete` | POST | インタビュー完了 |
| `/api/v1/interviews/{id}/transcript` | GET | 文字起こし取得 |

### Templates (`/api/v1/templates`)

| エンドポイント | メソッド | 説明 |
| -------------- | -------- | ---- |
| `/api/v1/templates` | GET | テンプレート一覧 |
| `/api/v1/templates` | POST | テンプレート作成 |
| `/api/v1/templates/{id}` | GET | テンプレート詳細 |
| `/api/v1/templates/{id}` | PUT | テンプレート更新 |
| `/api/v1/templates/{id}` | DELETE | テンプレート削除 |
| `/api/v1/templates/{id}/clone` | POST | テンプレート複製 |
| `/api/v1/templates/{id}/publish` | POST | テンプレート公開 |
| `/api/v1/templates/{id}/unpublish` | POST | テンプレート非公開 |

### Reports (`/api/v1/reports`)

| エンドポイント | メソッド | 説明 |
| -------------- | -------- | ---- |
| `/api/v1/reports` | GET | レポート一覧 |
| `/api/v1/reports/generate` | POST | レポート生成 |
| `/api/v1/reports/{id}` | GET | レポート詳細 |
| `/api/v1/reports/{id}` | PUT | レポート更新 |
| `/api/v1/reports/{id}/export` | GET | レポートエクスポート |
| `/api/v1/reports/{id}/submit-review` | POST | レビュー提出 |
| `/api/v1/reports/{id}/approve` | POST | レポート承認 |

### Knowledge (`/api/v1/knowledge`)

| エンドポイント | メソッド | 説明 |
| -------------- | -------- | ---- |
| `/api/v1/knowledge` | GET | ナレッジ一覧 |
| `/api/v1/knowledge` | POST | ナレッジ登録 |
| `/api/v1/knowledge/search` | POST | ナレッジ検索 (RAG) |
| `/api/v1/knowledge/{id}` | GET | ナレッジ詳細 |
| `/api/v1/knowledge/{id}` | DELETE | ナレッジ削除 |

### Models (`/api/v1/models`)

| エンドポイント | メソッド | 説明 |
| -------------- | -------- | ---- |
| `/api/v1/models` | GET | モデル一覧 |
| `/api/v1/models/recommended` | GET | 推奨モデル取得 |
| `/api/v1/models/providers` | GET | プロバイダー一覧 |
| `/api/v1/models/test-connection` | POST | 接続テスト |

### WebSocket

| エンドポイント | 説明 |
| -------------- | ---- |
| `/api/v1/interviews/{id}/stream` | リアルタイムインタビュー対話 |

## LLMモデル選択 (2026年最新版)

### リアルタイム対話戦略

インタビュー対話では**レイテンシ（応答速度）**が重要です。自然な会話体験を実現するため、モデルを用途別に使い分けます。

| レイテンシクラス | TTFT目標 | 用途 | 推奨モデル |
| ---------------- | -------- | ---- | ---------- |
| **ULTRA_FAST** | <200ms | リアルタイム対話 | Claude 4.6 Haiku, GPT-5 Nano, Gemini Flash Lite |
| **FAST** | 200-500ms | 高品質対話 | Claude 4.6 Sonnet, GPT-4o, Gemini 3.0 Flash |
| **STANDARD** | 500ms-1s | 分析・レポート | GPT-5.2, Gemini 3.0 Pro |
| **SLOW** | >1s | 深い推論（非同期） | o3, Claude Sonnet 4.6 Opus |

### 用途別推奨モデル

```python
RECOMMENDED_MODELS = {
    # =========================================================================
    # リアルタイム対話（低レイテンシ必須）
    # インタビュー会話には ULTRA_FAST/FAST モデルを使用
    # =========================================================================
    "interview_dialogue": "claude-4.6-haiku",        # ULTRA_FAST - リアルタイム対話
    "interview_dialogue_premium": "claude-4.6-sonnet", # FAST - 高品質対話
    "quick_response": "gpt-5-nano",                  # ULTRA_FAST - 超高速

    # プロバイダー別リアルタイム推奨
    "azure_realtime": "azure-gpt-5-nano",            # Azure上のULTRA_FAST
    "aws_realtime": "bedrock-claude-4.6-haiku",      # Bedrock上のULTRA_FAST
    "gcp_realtime": "gemini-3.0-flash-lite",         # GCP上のULTRA_FAST

    # =========================================================================
    # 事後分析（レイテンシ非重視）
    # レポート生成・深い分析にはフラッグシップモデルを使用
    # =========================================================================
    "report_generation": "gpt-5.2",                  # 強力な構造化出力
    "interview_summary": "claude-sonnet-4.6-opus",   # 最高品質の要約
    "complex_analysis": "o3",                        # 深い推論（非同期）
    "embedding": "text-embedding-3-large",           # セマンティック検索
    "long_document": "gemini-3.0-pro-preview",       # 2Mコンテキスト
}
```

### ハイブリッドアプローチ（推奨）

最適なユーザー体験を実現するため、以下のハイブリッド戦略を採用：

1. **リアルタイム対話**: Claude 4.6 Haiku / GPT-5 Nano（<200ms応答）
2. **バックグラウンド分析**: Claude Sonnet 4.6 Opus（高品質要約を非同期生成）

これにより、レスポンシブなUXと分析品質を両立します。

### 価格帯・レイテンシ別モデル

| Tier | モデル例 | 入力/1K | 出力/1K | レイテンシ | コンテキスト |
| ---- | -------- | ------- | ------- | ---------- | ------------ |
| Economy | GPT-5 Nano, Claude 4.6 Haiku | ~$0.0001 | ~$0.0004 | ULTRA_FAST | 128K-200K |
| Standard | GPT-4o, Gemini 2.0 Flash | ~$0.001 | ~$0.004 | FAST | 128K-1M |
| Premium | Claude 4.6 Sonnet, Gemini 3.0 Flash | ~$0.004 | ~$0.02 | FAST | 400K-1M |
| Flagship | GPT-5.2, Claude Sonnet 4.6 Opus, Gemini 3.0 Pro | ~$0.018 | ~$0.09 | SLOW | 500K-2M |

## テスト

```bash
# ユニットテスト
cd apps/backend
pytest tests/ -v

# 結合テスト
pytest tests/integration/ -v

# カバレッジ
pytest tests/ --cov=src/grc_backend --cov-report=html

# AIパッケージテスト
cd packages/@grc/ai
pytest tests/ -v

# Coreパッケージテスト
cd packages/@grc/core
pytest tests/ -v

# フロントエンドテスト
cd apps/web
pnpm test

# E2Eテスト
pnpm test:e2e
```

## クラウドデプロイ

### Terraform によるインフラ構築

```bash
cd infrastructure/terraform

# 開発環境
terraform init
terraform plan -var-file=environments/dev/terraform.tfvars
terraform apply -var-file=environments/dev/terraform.tfvars

# 本番環境
terraform plan -var-file=environments/prod/terraform.tfvars
terraform apply -var-file=environments/prod/terraform.tfvars
```

### プロバイダー選択

```hcl
# terraform.tfvars
cloud_provider = "azure"      # azure | aws | gcp
ai_provider    = "azure_openai"  # azure_openai | aws_bedrock | gcp_vertex
region         = "japaneast"
```

## 開発コマンド

```bash
# Lint
pnpm lint

# Type check
pnpm type-check

# Format
pnpm format

# Build
pnpm build

# All checks
pnpm lint && pnpm type-check && pnpm build
```

## エンタープライズ機能

### セキュリティ

- **認証・認可**: JWT + OAuth2.0 / SSO (Azure AD, Okta)
- **API セキュリティ**: レート制限、CORS、CSP、HSTS
- **監査ログ**: 全操作の追跡可能性
- **シークレット管理**: Azure Key Vault / AWS Secrets Manager / GCP Secret Manager

### 監視・ログ

- **構造化ログ**: JSON形式、相関ID、センシティブデータマスキング
- **分散トレーシング**: OpenTelemetry対応
- **メトリクス**: レスポンス時間、エラーレート、リソース使用率
- **アラート**: 閾値超過時の自動通知

### CI/CD パイプライン

```yaml
# .github/workflows/ci.yml - 自動実行
- リント & 型チェック (Python/TypeScript)
- ユニットテスト & カバレッジ
- セキュリティスキャン (Trivy, Gitleaks)
- Dockerイメージビルド
- Terraform検証

# .github/workflows/deploy.yml - デプロイ
- マルチクラウドデプロイ (Azure/AWS/GCP)
- ブルー/グリーンデプロイ
- 自動ロールバック
```

### Docker 運用

```bash
# 開発環境
docker-compose up -d

# 本番環境
docker-compose -f docker-compose.prod.yml up -d

# スケール
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

## ドキュメント

### ガイド（初心者向け）

- [セットアップガイド](docs/guides/SETUP.md) - 開発環境の構築手順
- [開発ガイド](docs/guides/DEVELOPMENT.md) - コーディング規約、テスト方法
- [デプロイガイド](docs/guides/DEPLOYMENT.md) - 本番環境へのデプロイ

### エンタープライズ仕様書（学習用テキスト）

- [ログ管理仕様書](docs/specifications/LOGGING.md) - 構造化ログ、相関ID、マスキング
- [エラー処理仕様書](docs/specifications/ERROR_HANDLING.md) - エラー階層、リトライ、サーキットブレーカー
- [セキュリティ仕様書](docs/specifications/SECURITY.md) - JWT認証、RBAC、OWASP対策
- [インフラ仕様書](docs/specifications/INFRASTRUCTURE.md) - Docker、CI/CD、Terraform
- [AIプロバイダー仕様書](docs/specifications/AI_PROVIDERS.md) - マルチクラウドAI、音声サービス

## ライセンス

Proprietary - All Rights Reserved

本ソフトウェアは Go Yoshizawa の独占的所有物です。
Go Yoshizawa による明示的な書面による許可なく、本ソフトウェアを使用、複製、改変、配布することは一切禁止されています。

詳細は [LICENSE](LICENSE) ファイルを参照してください。
