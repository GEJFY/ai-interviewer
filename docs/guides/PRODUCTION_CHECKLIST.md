# 本番デプロイチェックリスト

AI Interview Tool を本番環境にデプロイする際の確認事項。
各項目は `apps/backend/src/grc_backend/config.py` および `.env.example` の設定値に基づく。

---

## クイックスタート - 本番環境の最小構成

以下の環境変数を設定すればアプリケーションが起動する。

```bash
# 必須 - アプリケーション基本設定
ENVIRONMENT=production
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(64))")
DEBUG=false

# 必須 - データストア
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/aiinterviewer?sslmode=require
REDIS_URL=rediss://:password@host:6380

# 必須 - AIプロバイダー (azure / aws / gcp から選択)
AI_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key

# 必須 - 音声サービス
SPEECH_PROVIDER=azure
AZURE_SPEECH_KEY=your-speech-key
AZURE_SPEECH_REGION=japaneast

# 必須 - フロントエンド接続先
CORS_ORIGINS=https://your-domain.com
NEXT_PUBLIC_API_URL=https://api.your-domain.com
NEXT_PUBLIC_WS_URL=wss://api.your-domain.com
```

---

## 1. セキュリティ (Security)

| 状態 | 項目 | 詳細 |
|------|------|------|
| [ ] | **SECRET_KEY を本番用に変更** | `python -c "import secrets; print(secrets.token_urlsafe(64))"` で生成。`config.py` の `_validate_production_secrets` により、デフォルト値 `dev-secret-key-change-in-production` は production 環境で起動時にブロックされる |
| [ ] | **ENVIRONMENT=production に設定** | `development` / `staging` / `production` から選択。production 以外では SECRET_KEY バリデーションが無効 |
| [ ] | **DEBUG=false** | 本番では必ず `false`。デフォルトは `False` (config.py) だが `.env` で明示的に設定すること |
| [ ] | **CORS_ORIGINS を本番ドメインのみに制限** | カンマ区切りで複数指定可。開発用の `localhost` を必ず除去 |
| [ ] | **RATE_LIMIT_ENABLED=true** | デフォルト `false`。`docker-compose.prod.yml` では `RATE_LIMIT_REQUESTS=60` に設定済み |
| [ ] | **JWT トークン有効期限の確認** | `ACCESS_TOKEN_EXPIRE_MINUTES=30` (デフォルト)、`REFRESH_TOKEN_EXPIRE_DAYS=7` (デフォルト)。要件に応じて調整 |
| [ ] | **HTTPS 強制** | Azure App Service は `https_only = true` (Terraform)。Traefik 使用時は Let's Encrypt で自動証明書取得 |
| [ ] | **SSO設定 (任意)** | Azure AD: `AZURE_AD_CLIENT_ID`, `AZURE_AD_CLIENT_SECRET`, `AZURE_AD_TENANT_ID`。Okta: `OKTA_DOMAIN`, `OKTA_CLIENT_ID`, `OKTA_CLIENT_SECRET` |

---

## 2. データベース (Database)

| 状態 | 項目 | 詳細 |
|------|------|------|
| [ ] | **DATABASE_URL を本番 PostgreSQL に変更** | 形式: `postgresql+asyncpg://user:password@host:5432/dbname?sslmode=require`。Terraform output `database_connection` から取得可能 |
| [ ] | **DB_POOL_SIZE / DB_MAX_OVERFLOW の調整** | デフォルト: `pool_size=10`, `max_overflow=20`。計算式: `pool_size x workers <= DB max_connections`。Dockerfile のデフォルトは workers=4 |
| [ ] | **SSL接続の有効化** | DATABASE_URL に `?sslmode=require` を付与。Azure PostgreSQL Flexible Server はデフォルトで SSL 必須 |
| [ ] | **バックアップ設定の確認** | Terraform 設定: prod 環境は `backup_retention_days=35` + `geo_redundant_backup_enabled=true`、dev/staging は 7日 |
| [ ] | **pgvector 拡張の有効化** | Terraform で `azure.extensions = "vector,uuid-ossp"` を設定済み。手動の場合: `CREATE EXTENSION IF NOT EXISTS vector` |
| [ ] | **マイグレーション実行** | デプロイ前に `alembic upgrade head` を実行。SEED_DEMO=false を確認（本番にデモデータを入れない） |

---

## 3. キャッシュ (Cache)

| 状態 | 項目 | 詳細 |
|------|------|------|
| [ ] | **REDIS_URL を本番 Redis に変更** | SSL接続: `rediss://:password@host:6380`。Terraform output `redis_connection` から取得可能 |
| [ ] | **Redis 認証の設定** | Azure Redis Cache は `non_ssl_port_enabled=false`, `minimum_tls_version=1.2` で構成済み |
| [ ] | **maxmemory ポリシーの確認** | Terraform 設定: `volatile-lru`。prod 環境は Standard SKU (capacity=2)、dev は Basic (capacity=0) |

---

## 4. AIプロバイダー (AI Provider)

プロバイダーを1つ選択し、対応する認証情報を設定する。`AI_PROVIDER` は `azure` / `aws` / `gcp` / `local` から選択。

### Microsoft Foundry (旧 Azure OpenAI)

| 状態 | 項目 | 詳細 |
|------|------|------|
| [ ] | **AZURE_OPENAI_ENDPOINT** | `https://your-resource.openai.azure.com/` |
| [ ] | **AZURE_OPENAI_API_KEY** | Terraform output `openai_key` から取得、または Azure Portal から |
| [ ] | **AZURE_OPENAI_API_VERSION** | config.py デフォルト: `2025-12-01-preview`、.env.example: `2024-12-01` |
| [ ] | **モデルデプロイメントの確認** | フラグシップ: `gpt-5.2`、エコノミカル: `gpt-5-nano`、Embedding: `text-embedding-3-large` |

### AWS Bedrock

| 状態 | 項目 | 詳細 |
|------|------|------|
| [ ] | **AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY** | IAM ユーザーまたは Instance Profile を使用 |
| [ ] | **AWS_REGION** | デフォルト: `ap-northeast-1` |
| [ ] | **AWS_BEDROCK_MODEL_ID** | フラグシップ: Claude Opus 4.6、エコノミカル: Claude Haiku 4.5 |

### GCP Vertex AI

| 状態 | 項目 | 詳細 |
|------|------|------|
| [ ] | **GCP_PROJECT_ID** | GCP プロジェクトID |
| [ ] | **GCP_LOCATION** | デフォルト: `asia-northeast1` |
| [ ] | **GOOGLE_APPLICATION_CREDENTIALS** | サービスアカウントキーのパス |

### 音声サービス (Speech Provider)

| 状態 | 項目 | 詳細 |
|------|------|------|
| [ ] | **SPEECH_PROVIDER** | `azure` / `aws` / `gcp` から選択 |
| [ ] | **AZURE_SPEECH_KEY** | Terraform output `speech_key` から取得 |
| [ ] | **AZURE_SPEECH_REGION** | デフォルト: `japaneast` |

---

## 5. ストレージ (Storage)

| 状態 | 項目 | 詳細 |
|------|------|------|
| [ ] | **STORAGE_PROVIDER の選択** | `azure` / `aws` / `gcp` / `local` から選択。本番では `local` 以外を使用 |
| [ ] | **Azure Blob Storage** | `AZURE_STORAGE_CONNECTION_STRING` を設定。コンテナ: `audio-files`, `reports` (Terraform で作成済み) |
| [ ] | **バージョニングの確認** | Terraform 設定: `versioning_enabled=true`, 削除保持7日間 |

---

## 6. ログ・監視 (Logging & Monitoring)

| 状態 | 項目 | 詳細 |
|------|------|------|
| [ ] | **LOG_LEVEL=INFO** | 本番では `INFO` を推奨。デバッグ時のみ `DEBUG` に変更 |
| [ ] | **JSON_LOGS=true** | 構造化ログ出力を有効化。ログ集約サービスでのパースが容易になる |
| [ ] | **OTEL_ENABLED=true (任意)** | OpenTelemetry トレーシング。`OTEL_EXPORTER_OTLP_ENDPOINT` と `OTEL_SERVICE_NAME=ai-interviewer` を設定 |
| [ ] | **Application Insights 接続文字列** | `APPLICATIONINSIGHTS_CONNECTION_STRING` を設定。Terraform output `application_insights_key` から取得 |
| [ ] | **Diagnostic Settings の確認** | Terraform 設定済み: AppServiceHTTPLogs, AppServiceConsoleLogs, AppServiceAppLogs, PostgreSQLLogs, AllMetrics |

---

## 7. インフラ (Infrastructure)

### Terraform デプロイ

| 状態 | 項目 | 詳細 |
|------|------|------|
| [ ] | **Terraform backend をリモートに変更** | `infrastructure/terraform/main.tf` の `backend "local" {}` を `backend "azurerm" {}` に変更。`resource_group_name`, `storage_account_name`, `container_name`, `key` を設定 |
| [ ] | **environment 変数を prod に設定** | `terraform.tfvars` に `environment = "prod"` を設定。SKU が自動的に本番スペックに切り替わる (DB: `GP_Standard_D4s_v3`, Redis: Standard, ACR: Premium, App Service: `P2v3`) |
| [ ] | **alert_email の設定** | `variable "alert_email"` のデフォルト `admin@example.com` を実際のメールアドレスに変更 |

### コンテナデプロイ

| 状態 | 項目 | 詳細 |
|------|------|------|
| [ ] | **コンテナイメージのビルド** | Backend: `docker build --target production -f apps/backend/Dockerfile -t ai-interviewer-api:latest .` Frontend: `docker build --target production -f apps/web/Dockerfile --build-arg NEXT_PUBLIC_API_URL=... -t ai-interviewer-web:latest .` |
| [ ] | **レジストリへのプッシュ** | `docker tag ... <registry>/ai-interviewer-api:latest && docker push ...`。Terraform output `container_registry` でレジストリURLを確認 |
| [ ] | **ヘルスチェックの確認** | Backend: `GET /api/v1/health` (DB, Redis, AI Provider の状態を返却)。Frontend: `GET /` |
| [ ] | **ワーカー数の確認** | Dockerfile デフォルト: `--workers 4`。必要に応じて CMD を上書き |

### Docker Compose (セルフホスト)

| 状態 | 項目 | 詳細 |
|------|------|------|
| [ ] | **docker-compose.prod.yml で起動** | `docker-compose -f docker-compose.prod.yml up -d` |
| [ ] | **リソース制限の確認** | Backend: CPU 1 / Memory 2G、Frontend: CPU 0.5 / Memory 512M |
| [ ] | **Traefik プロキシ (任意)** | `--profile with-proxy` で有効化。ACME_EMAIL を設定して Let's Encrypt 証明書を自動取得 |

### フロントエンド

| 状態 | 項目 | 詳細 |
|------|------|------|
| [ ] | **NEXT_PUBLIC_API_URL** | 本番 API の URL (ビルド時引数) |
| [ ] | **NEXT_PUBLIC_WS_URL** | WebSocket の URL (`wss://` プロトコル) |
| [ ] | **NEXT_PUBLIC_ENVIRONMENT=production** | Dockerfile のデフォルト引数で設定済み |

---

## 8. 運用準備 (Operations)

| 状態 | 項目 | 詳細 |
|------|------|------|
| [ ] | **バックアップリストア手順の確認** | Azure PostgreSQL: ポイントインタイムリストア (最大35日)。Storage Account: バージョニング + 削除保持 |
| [ ] | **ロールバック手順の確認** | `docker-compose.prod.yml` の `update_config.failure_action: rollback` で自動ロールバック。手動: 前バージョンのイメージタグを指定して再デプロイ |
| [ ] | **アラート設定の確認** | Terraform 設定済み: API Health (severity 1), API Response Time > 5s (severity 2), DB CPU > 80% (severity 2), Redis Memory > 80% (severity 2) |
| [ ] | **ログローテーション** | Docker: `max-size=10m`, `max-file=3`。Azure: Log Analytics ワークスペースに `retention_in_days=30` |
| [ ] | **インシデント対応手順** | 障害発生時の連絡先、エスカレーションパス、復旧手順書を準備 |
| [ ] | **負荷テスト** | 本番相当の環境でスケール構成 (`--scale backend=3`) を検証 |

---

## デプロイコマンド一覧

```bash
# 1. Terraform で Azure リソースを作成
cd infrastructure/terraform
terraform init
terraform plan -var="environment=prod"
terraform apply -var="environment=prod"

# 2. Terraform output から接続情報を取得
terraform output -json

# 3. コンテナイメージをビルド & プッシュ
REGISTRY=$(terraform output -raw container_registry)
docker build --target production -f apps/backend/Dockerfile -t $REGISTRY/ai-interviewer-api:v1.0.0 .
docker build --target production -f apps/web/Dockerfile \
  --build-arg NEXT_PUBLIC_API_URL=https://api.your-domain.com \
  --build-arg NEXT_PUBLIC_WS_URL=wss://api.your-domain.com \
  -t $REGISTRY/ai-interviewer-web:v1.0.0 .
docker push $REGISTRY/ai-interviewer-api:v1.0.0
docker push $REGISTRY/ai-interviewer-web:v1.0.0

# 4. ヘルスチェック確認
curl https://api.your-domain.com/api/v1/health
```
