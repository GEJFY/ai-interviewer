# トラブルシューティングガイド

AI Interview Tool の開発・デプロイで遭遇する実際の問題と解決策をまとめたガイドです。

> **対象読者**: 開発者・インフラ担当者
> **前提**: プロジェクト構成は [DEVELOPMENT.md](./DEVELOPMENT.md) を参照

---

## 目次

1. [ローカル開発 (Local Development)](#1-ローカル開発-local-development)
2. [Azure デプロイ (Azure Deployment)](#2-azure-デプロイ-azure-deployment)
3. [データベース (Database)](#3-データベース-database)
4. [AI/LLM 関連 (AI/LLM)](#4-aillm-関連-aillm)
5. [フロントエンド (Frontend)](#5-フロントエンド-frontend)
6. [診断コマンド一覧 (Diagnostic Commands)](#6-診断コマンド一覧-diagnostic-commands)

---

## 1. ローカル開発 (Local Development)

### 1.1 Docker Compose 起動時に "relation does not exist" エラー

**症状**

```
sqlalchemy.exc.ProgrammingError: (asyncpg.exceptions.UndefinedTableError)
relation "projects" does not exist
```

**原因**

データベースのテーブルが未作成の状態で API がクエリを実行している。
`ENVIRONMENT=development` の場合、アプリケーション起動時に `lifespan` 内で `db.create_tables()` が呼ばれるが、
環境変数が正しく設定されていないとテーブル作成がスキップされることがある。

**解決策**

```bash
# .env で ENVIRONMENT を確認
grep ENVIRONMENT .env
# 出力: ENVIRONMENT=development

# Docker Compose を完全にリセットして再起動
docker compose down -v
docker compose up -d --build
```

**補足**: `main.py` の lifespan では `await db.create_tables()` が全環境で実行される（idempotent）。
テーブルが作成されない場合は PostgreSQL コンテナのヘルスチェックが完了する前にバックエンドが接続を試みている可能性がある。
`depends_on` の `condition: service_healthy` が正しく設定されているか確認すること。

```bash
# PostgreSQL コンテナのヘルスチェック状態を確認
docker inspect ai-interviewer-db | grep -A 5 '"Health"'
```

---

### 1.2 CORS エラー (403 Forbidden)

**症状**

ブラウザのコンソールに以下が表示される:

```
Access to fetch at 'http://localhost:8001/api/v1/...' from origin 'http://localhost:3000'
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present.
```

**原因**

`CORS_ORIGINS` に開発サーバーの URL が含まれていない。
Docker 起動 (port 8001/3001) と直接起動 (port 8000/3000) でポートが異なる点に注意。

**解決策**

`.env` に以下を追加:

```ini
# Docker 起動と直接起動の両方をカバー
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001
```

**検証**

```bash
# バックエンドの CORS 設定を確認
curl -i -X OPTIONS http://localhost:8001/api/v1/health \
  -H "Origin: http://localhost:3001" \
  -H "Access-Control-Request-Method: GET"
# Access-Control-Allow-Origin ヘッダーが返ることを確認
```

**補足**: `config.py` の `parse_cors_origins` バリデータは、カンマ区切り文字列と JSON 配列の両方を受け付ける。
Docker Compose 内では JSON 配列形式 `["http://localhost:3001"]` がデフォルトで設定されている。

---

### 1.3 pnpm install が失敗する

**症状**

```
ERR_PNPM_UNSUPPORTED_ENGINE  Unsupported environment (bad pnpm and/or Node.js version)
```

**原因**

Node.js のバージョンが合っていない。本プロジェクトの Dockerfile は `node:20-alpine` を使用しており、
Node.js 20.x が必要。

**解決策**

```bash
# nvm を使用している場合
nvm install 20
nvm use 20

# volta を使用している場合
volta install node@20

# バージョン確認
node -v   # v20.x.x であること
pnpm -v   # 9.x.x であること

# pnpm が入っていない場合
corepack enable
corepack prepare pnpm@9.14.0 --activate

# 再インストール
pnpm install
```

---

### 1.4 ImportError: No module named 'grc_core'

**症状**

```
ModuleNotFoundError: No module named 'grc_core'
```

または

```
ModuleNotFoundError: No module named 'grc_ai'
```

**原因**

モノレポ内部パッケージ (`packages/@grc/core`, `packages/@grc/ai`) が未インストール。
`pyproject.toml` で `grc-core` と `grc-ai` をワークスペース依存として宣言しているが、
editable install が必要。

**解決策**

```bash
# uv を使って全パッケージを editable install
uv pip install \
  -e "./packages/@grc/core" \
  -e "./packages/@grc/ai" \
  -e "./packages/@grc/infrastructure" \
  -e "./apps/backend[dev]"

# インストール確認
python -c "import grc_core; print('grc_core OK')"
python -c "import grc_ai; print('grc_ai OK')"
python -c "import grc_backend; print('grc_backend OK')"
```

**補足**: Docker 環境では `Dockerfile` 内で `PYTHONPATH` が設定されているため、この問題は発生しない。
ローカルの仮想環境で直接実行する場合のみ注意が必要。

```
# Dockerfile で設定されている PYTHONPATH
ENV PYTHONPATH="/app/src:/app/packages/@grc/core/src:/app/packages/@grc/ai/src"
```

---

### 1.5 bcrypt / passlib エラー

**症状**

```
ValueError: password cannot be longer than 72 bytes
```

または

```
AttributeError: module 'bcrypt' has no attribute '__about__'
```

**原因**

`bcrypt` 4.1 以降と `passlib` 1.7.4 の互換性問題。
`bcrypt` 4.1+ では内部 API が変更され、`passlib` の `detect_wrap_bug` ロジックがクラッシュする。

**解決策**

`pyproject.toml` で `bcrypt` のバージョンをピン:

```toml
# apps/backend/pyproject.toml (既に設定済み)
"bcrypt>=4.0.0,<4.1.0",  # passlib compatibility
```

```bash
# 現在のバージョンを確認
pip show bcrypt
# Version: 4.0.x であること

# もし 4.1+ が入っている場合
pip install "bcrypt>=4.0.0,<4.1.0"
```

---

## 2. Azure デプロイ (Azure Deployment)

### 2.1 Azure CLI がハングする (日本語 Windows)

**症状**

`az` コマンドを実行すると無限に待機状態になり、何も出力されない。
特に `az ml` 関連のコマンドや拡張が読み込まれるタイミングで発生する。

**原因**

- `ml` 拡張の無限 import loop
- Python 3.13 と一部 Azure CLI パッケージの競合
- 日本語 Windows 環境でのエンコーディング問題

**解決策**

`az-fixed.sh` ラッパースクリプトを使用する:

```bash
# ラッパーの内容 (scripts/az-fixed.sh 相当)
python -IBm azure.cli "$@"
```

```bash
# ラッパー経由で実行
bash scripts/az-fixed.sh account show

# または環境変数でダイレクト実行
PYTHONDONTWRITEBYTECODE=1 python -IBm azure.cli account show
```

**代替策**: PowerShell で直接実行する:

```powershell
# PowerShell から
python -IBm azure.cli account show
```

---

### 2.2 ACR ビルドで cp932 UnicodeEncodeError

**症状**

```
UnicodeEncodeError: 'cp932' codec can't encode character '\u2502' in position 0
```

ACR (`az acr build`) や Docker ビルド時に、pnpm のログ出力に含まれる Unicode 罫線文字が
日本語 Windows のデフォルトエンコーディング (cp932) でクラッシュする。

**原因**

pnpm のログ出力に含まれる Unicode 文字 (`\u2502`, `\u2514` 等) が、
Windows の `colorama` ライブラリ経由で cp932 エンコードされる際にエラーになる。

**解決策**

```bash
# 方法1: ACR ビルド時に --no-logs でストリーミングを回避
az acr build \
  --registry <acr-name> \
  --image ai-interviewer-web:latest \
  --file apps/web/Dockerfile \
  --no-logs \
  .

# ビルドログは後から確認
az acr task logs --registry <acr-name>

# 方法2: ローカルでビルド & プッシュ (推奨)
docker build -t <acr>.azurecr.io/ai-interviewer-web:latest -f apps/web/Dockerfile --target production .
docker push <acr>.azurecr.io/ai-interviewer-web:latest

# 方法3: 環境変数で UTF-8 を強制
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
chcp 65001
```

---

### 2.3 Container App が起動しない (CrashLoopBackOff)

**症状**

Container App または App Service が起動後すぐにクラッシュを繰り返す。

**原因**

- 必要な環境変数が未設定 (`DATABASE_URL`, `SECRET_KEY` 等)
- 依存パッケージの不足 (Docker イメージのビルド問題)
- ポート設定の不一致 (`WEBSITES_PORT` が設定されていない)

**解決策**

```bash
# Container Apps のログを確認
az containerapp logs show \
  --name <app-name> \
  --resource-group <rg-name> \
  --type console \
  --follow

# App Service のログを確認
az webapp log tail \
  --name <app-name> \
  --resource-group <rg-name>

# 環境変数の一覧を確認
az webapp config appsettings list \
  --name <app-name> \
  --resource-group <rg-name> \
  --output table

# 必要な環境変数を設定 (Backend)
az webapp config appsettings set \
  --name <backend-app-name> \
  --resource-group <rg-name> \
  --settings \
    ENVIRONMENT=demo \
    DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db?sslmode=require" \
    SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(64))')" \
    WEBSITES_PORT=8000
```

**チェックリスト (Backend 必須環境変数)**:

| 変数名 | 説明 | 例 |
|---|---|---|
| `DATABASE_URL` | PostgreSQL 接続文字列 | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis 接続文字列 | `redis://...` または `rediss://...` |
| `SECRET_KEY` | JWT 署名用キー | `secrets.token_urlsafe(64)` |
| `ENVIRONMENT` | 実行環境 | `production`, `demo`, `development` |
| `WEBSITES_PORT` | App Service 用ポート | `8000` |
| `CORS_ORIGINS` | 許可オリジン | `["https://your-domain.com"]` |

---

### 2.4 CORS_ORIGINS="*" で SettingsError

**症状**

```
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
cors_origins
  ...
```

または起動時に CORS 関連の設定エラー。

**原因**

`pydantic-settings` v2 が `cors_origins: str | list[str]` 型に対して `"*"` をパースする際、
JSON 配列として解釈しようとして失敗する。`config.py` のバリデータは JSON 配列とカンマ区切りの
両方に対応しているが、`"*"` 単体はどちらにも該当しない特殊ケース。

**解決策**

```bash
# 方法1: JSON 配列形式 (推奨)
CORS_ORIGINS='["https://your-frontend.azurewebsites.net","http://localhost:3001"]'

# 方法2: カンマ区切り形式
CORS_ORIGINS=https://your-frontend.azurewebsites.net,http://localhost:3001

# NG: ワイルドカードは使用しない (セキュリティ的にも非推奨)
# CORS_ORIGINS="*"
```

**Azure App Service での設定**:

```bash
# JSON 配列形式で設定 (シェルのエスケープに注意)
az webapp config appsettings set \
  --name <backend-app-name> \
  --resource-group <rg-name> \
  --settings CORS_ORIGINS='["https://your-frontend.azurewebsites.net"]'
```

---

### 2.5 ヘルスチェック失敗

**症状**

App Service または Container App のヘルスチェックが失敗し、コンテナが再起動される。

```
Unhealthy: GET /api/v1/health returned 404 or timeout
```

**原因**

- ヘルスチェックのパスが実際のエンドポイントと不一致
- データベース未接続でヘルスチェックが `degraded` を返している
- 起動に時間がかかり `start_period` を超過

**解決策**

```bash
# 正しいヘルスチェックパスを確認
# main.py: app.include_router(health.router, prefix="/api/v1", ...)
# health.py: @router.get("/health")
# → 完全パス: /api/v1/health

# ローカルで直接確認
curl -v http://localhost:8001/api/v1/health

# 期待される正常レスポンス:
# {
#   "status": "healthy",
#   "database": "healthy",
#   "redis": "healthy",
#   "ai_provider": "local:configured",
#   "version": "0.1.0",
#   "environment": "development"
# }

# Docker Compose のヘルスチェック設定を確認
docker inspect ai-interviewer-backend | grep -A 10 '"Healthcheck"'

# App Service のヘルスチェック設定
az webapp config set \
  --name <backend-app-name> \
  --resource-group <rg-name> \
  --generic-configurations '{"healthCheckPath": "/api/v1/health"}'
```

---

## 3. データベース (Database)

### 3.1 PostgreSQL 接続タイムアウト

**症状**

```
asyncpg.exceptions.ConnectionDoesNotExistError: connection was closed
sqlalchemy.exc.TimeoutError: QueuePool limit of size 10 overflow 20 reached
```

**原因**

接続プールが枯渇している。デフォルト設定 (`DB_POOL_SIZE=10`, `DB_MAX_OVERFLOW=20`) では
同時接続数の上限が 30。ワーカー数が多い場合、各ワーカーが独自のプールを持つため合計接続数が増大する。

**解決策**

```bash
# 現在のプール設定を確認
grep DB_POOL .env
# DB_POOL_SIZE=10
# DB_MAX_OVERFLOW=20

# ワーカー数に応じて調整 (pool_size x workers <= max_connections)
# 例: 4 workers の場合
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
# → 最大接続数: (5 + 10) x 4 = 60

# PostgreSQL 側の最大接続数を確認
docker exec ai-interviewer-db psql -U grc_user -d ai_interviewer \
  -c "SHOW max_connections;"

# 現在のアクティブ接続数を確認
docker exec ai-interviewer-db psql -U grc_user -d ai_interviewer \
  -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"
```

---

### 3.2 "SSL connection is required" エラー

**症状**

```
asyncpg.exceptions.ConnectionDoesNotExistError:
  SSL connection is required. Please specify SSL options and retry.
```

Azure PostgreSQL Flexible Server に接続する際に発生。

**原因**

Azure PostgreSQL はデフォルトで SSL 接続を必須としている。
ローカル開発用の `DATABASE_URL` には `?sslmode=require` が含まれていない。

**解決策**

```bash
# Azure PostgreSQL 用の DATABASE_URL に sslmode=require を追加
DATABASE_URL="postgresql+asyncpg://user:password@host.postgres.database.azure.com:5432/dbname?sslmode=require"
```

**検証**:

```bash
# SSL 接続のテスト
python -c "
import asyncio
import asyncpg

async def test():
    conn = await asyncpg.connect(
        'postgresql://user:pass@host:5432/db?sslmode=require'
    )
    print(await conn.fetchval('SELECT version()'))
    await conn.close()

asyncio.run(test())
"
```

**補足**: デプロイスクリプト `scripts/deploy-azure-demo.sh` では、`DATABASE_URL` に
`?sslmode=require` が自動付与される。

---

## 4. AI/LLM 関連 (AI/LLM)

### 4.1 Ollama 接続エラー

**症状**

```
httpx.ConnectError: [Errno 111] Connection refused
```

または

```
ollama._types.ResponseError: model 'gemma3:1b' not found
```

**原因**

- Ollama サーバーが起動していない
- モデルが未ダウンロード
- Docker 内から `localhost` でアクセスしている (ネットワーク分離)

**解決策**

```bash
# Ollama サーバーを起動
ollama serve

# 別ターミナルでモデルをダウンロード
ollama pull gemma3:1b

# 動作確認
ollama list
# NAME           SIZE
# gemma3:1b      815 MB

# API の疎通確認
curl http://localhost:11434/api/tags
```

**Docker Compose で Ollama を使う場合**:

```bash
# local-llm プロファイルで起動
docker compose --profile local-llm up -d

# .env の設定を確認
# AI_PROVIDER=local
# OLLAMA_BASE_URL=http://ollama:11434  # Docker 内ではサービス名で接続
# OLLAMA_MODEL=gemma3:1b

# Docker 内の Ollama にモデルをダウンロード
docker exec ai-interviewer-ollama ollama pull gemma3:1b
```

**ホスト側の Ollama を Docker から使う場合**:

```bash
# .env で以下を設定
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

---

### 4.2 Azure OpenAI 429 Too Many Requests

**症状**

```
openai.RateLimitError: Error code: 429 - Rate limit reached for deployment 'gpt-5-nano'
```

**原因**

Azure OpenAI デプロイメントのレート制限 (TPM: Tokens Per Minute / RPM: Requests Per Minute)
を超過している。

**解決策**

```bash
# 1. Azure Portal でデプロイメントの TPM/RPM を確認・引き上げ
az cognitiveservices account deployment show \
  --name <openai-resource-name> \
  --resource-group <rg-name> \
  --deployment-name gpt-5-nano

# 2. リトライロジックが有効であることを確認
# grc_ai パッケージ内の LLM クライアントにリトライが実装されているか確認

# 3. デプロイメントの制限を引き上げ (Azure Portal または CLI)
az cognitiveservices account deployment create \
  --name <openai-resource-name> \
  --resource-group <rg-name> \
  --deployment-name gpt-5-nano \
  --model-name gpt-5-nano \
  --model-version "latest" \
  --sku-capacity 120  # TPM in thousands (120K TPM)
```

**一時的な回避策**:

```bash
# ローカル LLM にフォールバック
AI_PROVIDER=local
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:1b
```

---

## 5. フロントエンド (Frontend)

### 5.1 NEXT_PUBLIC_API_URL が反映されない

**症状**

デプロイ後にフロントエンドが `http://localhost:8000` に API リクエストを送り続ける。
環境変数を変更しても反映されない。

**原因**

Next.js は `NEXT_PUBLIC_*` 環境変数を**ビルド時**に JavaScript バンドルにインライン化 (bake) する。
実行時に環境変数を変更しても、ビルド済みの JavaScript には反映されない。

**解決策**

```dockerfile
# apps/web/Dockerfile の builder ステージで ARG → ENV → build の順序を確認
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_WS_URL
ARG NEXT_PUBLIC_ENVIRONMENT=production

ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL
ENV NEXT_PUBLIC_ENVIRONMENT=$NEXT_PUBLIC_ENVIRONMENT

RUN pnpm build  # ここで環境変数がバンドルに埋め込まれる
```

```bash
# ビルド時に値を渡す
docker build \
  -t ai-interviewer-web:latest \
  -f apps/web/Dockerfile \
  --target production \
  --build-arg NEXT_PUBLIC_API_URL=https://api.example.com \
  --build-arg NEXT_PUBLIC_WS_URL=wss://api.example.com \
  --build-arg NEXT_PUBLIC_ENVIRONMENT=production \
  .
```

**検証**:

```bash
# ビルド済みの JavaScript から環境変数が正しく埋め込まれているか確認
docker run --rm ai-interviewer-web:latest \
  grep -r "NEXT_PUBLIC_API_URL" /app/apps/web/.next/ | head -5
```

---

### 5.2 WebSocket 接続失敗

**症状**

ブラウザのコンソールに以下が表示される:

```
WebSocket connection to 'ws://...' failed:
```

またはインタビュー画面でリアルタイム通信が機能しない。

**原因**

- `NEXT_PUBLIC_WS_URL` が未設定
- HTTPS 環境で `ws://` (非暗号化) を使用している
- リバースプロキシが WebSocket をサポートしていない

**解決策**

```bash
# .env の設定を確認
# 開発環境
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Docker 環境
NEXT_PUBLIC_WS_URL=ws://localhost:8001

# 本番環境 (HTTPS の場合は wss:// を使用)
NEXT_PUBLIC_WS_URL=wss://api.example.com
```

**Azure App Service の場合**:

```bash
# WebSocket を有効化
az webapp config set \
  --name <backend-app-name> \
  --resource-group <rg-name> \
  --web-sockets-enabled true

# フロントエンドの環境変数を設定 (ビルド時に渡す)
# NEXT_PUBLIC_WS_URL=wss://<backend-app-name>.azurewebsites.net
```

**プロトコル対応表**:

| 環境 | HTTP プロトコル | WebSocket プロトコル |
|---|---|---|
| ローカル開発 | `http://` | `ws://` |
| Docker Compose | `http://` | `ws://` |
| Azure (本番) | `https://` | `wss://` |

---

## 6. 診断コマンド一覧 (Diagnostic Commands)

開発・運用時に使える診断コマンドをまとめる。

### ローカル環境の状態確認

```bash
# 全コンテナの状態を一覧表示
docker compose ps

# 全サービスのログを追従表示
docker compose logs -f

# 特定サービスのログのみ表示
docker compose logs -f backend
docker compose logs -f web
docker compose logs -f postgres

# コンテナのリソース使用量
docker stats --no-stream

# ヘルスチェック API の確認
curl -s http://localhost:8001/api/v1/health | python -m json.tool
```

### データベース診断

```bash
# PostgreSQL に直接接続
docker exec -it ai-interviewer-db psql -U grc_user -d ai_interviewer

# テーブル一覧
docker exec ai-interviewer-db psql -U grc_user -d ai_interviewer \
  -c "\dt"

# アクティブ接続数
docker exec ai-interviewer-db psql -U grc_user -d ai_interviewer \
  -c "SELECT state, count(*) FROM pg_stat_activity GROUP BY state;"

# データベースサイズ
docker exec ai-interviewer-db psql -U grc_user -d ai_interviewer \
  -c "SELECT pg_size_pretty(pg_database_size('ai_interviewer'));"

# pgvector 拡張の確認
docker exec ai-interviewer-db psql -U grc_user -d ai_interviewer \
  -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

### Redis 診断

```bash
# Redis に接続
docker exec -it ai-interviewer-redis redis-cli

# Redis の状態確認
docker exec ai-interviewer-redis redis-cli info server | head -20

# メモリ使用量
docker exec ai-interviewer-redis redis-cli info memory | grep used_memory_human

# キー数
docker exec ai-interviewer-redis redis-cli dbsize
```

### ネットワーク診断

```bash
# Docker ネットワーク一覧
docker network ls | grep ai-interviewer

# ネットワーク内のコンテナ間接続テスト
docker exec ai-interviewer-backend curl -s http://postgres:5432 || echo "Port open"
docker exec ai-interviewer-backend curl -s http://redis:6379 || echo "Port open"

# ポート使用状況の確認 (Windows)
netstat -ano | findstr "8001 3001 5432 6379"
```

### Azure 環境の診断

```bash
# App Service のログをリアルタイムで確認
az webapp log tail \
  --name <app-name> \
  --resource-group <rg-name>

# App Service の設定ダンプ
az webapp config appsettings list \
  --name <app-name> \
  --resource-group <rg-name> \
  --output table

# Container App のログ
az containerapp logs show \
  --name <app-name> \
  --resource-group <rg-name> \
  --type console

# リソースグループ内の全リソース
az resource list \
  --resource-group <rg-name> \
  --output table

# PostgreSQL のファイアウォールルール確認
az postgres flexible-server firewall-rule list \
  --resource-group <rg-name> \
  --name <db-server-name> \
  --output table
```

### パッケージ / 依存関係の確認

```bash
# Python パッケージのバージョン確認
pip show bcrypt passlib fastapi pydantic-settings sqlalchemy

# Node.js パッケージの確認
pnpm list --depth 0

# uv でインストール済みパッケージ
uv pip list | grep grc
```

---

## クイックリファレンス: よくあるエラーと対応

| エラーメッセージ | セクション | 一言対応 |
|---|---|---|
| `relation "xxx" does not exist` | [1.1](#11-docker-compose-起動時に-relation-does-not-exist-エラー) | `docker compose down -v && docker compose up -d --build` |
| `CORS policy: No 'Access-Control-Allow-Origin'` | [1.2](#12-cors-エラー-403-forbidden) | `CORS_ORIGINS` に URL を追加 |
| `ERR_PNPM_UNSUPPORTED_ENGINE` | [1.3](#13-pnpm-install-が失敗する) | `nvm use 20` |
| `No module named 'grc_core'` | [1.4](#14-importerror-no-module-named-grc_core) | `uv pip install -e` で editable install |
| `bcrypt: password cannot be longer than 72 bytes` | [1.5](#15-bcrypt--passlib-エラー) | `bcrypt>=4.0.0,<4.1.0` にピン |
| `az` コマンドがハング | [2.1](#21-azure-cli-がハングする-日本語-windows) | `python -IBm azure.cli` で実行 |
| `UnicodeEncodeError: 'cp932'` | [2.2](#22-acr-ビルドで-cp932-unicodeencodeerror) | `--no-logs` または local build & push |
| `CrashLoopBackOff` | [2.3](#23-container-app-が起動しない-crashloopbackoff) | ログ確認 → 環境変数設定 |
| `ValidationError for Settings cors_origins` | [2.4](#24-cors_origins-で-settingserror) | JSON 配列形式で指定 |
| `GET /api/v1/health 404` | [2.5](#25-ヘルスチェック失敗) | パス `/api/v1/health` を確認 |
| `QueuePool limit reached` | [3.1](#31-postgresql-接続タイムアウト) | `DB_POOL_SIZE` を調整 |
| `SSL connection is required` | [3.2](#32-ssl-connection-is-required-エラー) | `?sslmode=require` を追加 |
| `Connection refused` (Ollama) | [4.1](#41-ollama-接続エラー) | `ollama serve && ollama pull gemma3:1b` |
| `429 Too Many Requests` | [4.2](#42-azure-openai-429-too-many-requests) | TPM/RPM 上限引き上げ |
| `NEXT_PUBLIC_*` が反映されない | [5.1](#51-next_public_api_url-が反映されない) | `--build-arg` で渡してリビルド |
| WebSocket 接続失敗 | [5.2](#52-websocket-接続失敗) | HTTPS では `wss://` を使用 |
