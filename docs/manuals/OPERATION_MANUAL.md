# AI面接システム 運用マニュアル

**バージョン:** 1.0
**最終更新日:** 2026-02-15
**対象者:** システム運用担当者、SREチーム

---

## 目次

1. [システム構成](#1-システム構成)
2. [日常運用](#2-日常運用)
3. [監視設定](#3-監視設定)
4. [インシデント対応](#4-インシデント対応)
5. [スケーリング](#5-スケーリング)
6. [デプロイ運用](#6-デプロイ運用)
7. [セキュリティ運用](#7-セキュリティ運用)

---

## 1. システム構成

### 1.1 アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────────┐
│                         ユーザー                              │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTPS (443)
                        ▼
┌───────────────────────────────────────────────────────────────┐
│                     ロードバランサー                           │
│                    (ALB / Cloud LB)                           │
└────────────┬──────────────────────────────┬───────────────────┘
             │                              │
             │ Port 3001                    │ Port 8001
             ▼                              ▼
┌─────────────────────┐          ┌─────────────────────────┐
│   Webフロントエンド   │          │      APIバックエンド      │
│   Next.js 15        │◄────────►│      FastAPI           │
│   React 19          │ WebSocket│      Python 3.11+      │
│   pnpm + turbo      │          │      /api/v1/*         │
└─────────────────────┘          └───────────┬─────────────┘
                                             │
                        ┌────────────────────┼────────────────────┐
                        │                    │                    │
                        ▼                    ▼                    ▼
              ┌──────────────────┐  ┌──────────────┐  ┌──────────────────┐
              │   PostgreSQL 15+  │  │   Redis 7+   │  │   AI Provider    │
              │   Port 5432      │  │   Port 6379  │  │ Azure OpenAI /   │
              │   asyncpg        │  │   Cache      │  │ AWS Bedrock /    │
              │                  │  │              │  │ GCP Vertex AI    │
              └──────────────────┘  └──────────────┘  └──────────────────┘
```

### 1.2 コンポーネント一覧

| コンポーネント | 技術スタック | 役割 | 冗長構成 |
|-------------|------------|------|---------|
| **Webフロントエンド** | Next.js 15, React 19 | ユーザーインターフェース | 水平スケール可 (2台以上推奨) |
| **APIバックエンド** | FastAPI, Python 3.11+ | ビジネスロジック、API提供 | 水平スケール可 (3台以上推奨) |
| **データベース** | PostgreSQL 15+ | 永続データストレージ | Primary-Replica構成 |
| **キャッシュ** | Redis 7+ | セッション管理、キャッシュ | Redis Cluster / Sentinel |
| **AI Provider** | Azure OpenAI / Bedrock / Vertex AI | AI面接処理 | マルチプロバイダー対応 |
| **認証** | JWT (access + refresh token) | ユーザー認証、MFA対応 | ステートレス |
| **リアルタイム通信** | WebSocket | 面接セッション | 永続接続管理 |

### 1.3 ポート一覧

| サービス | ポート番号 | プロトコル | 用途 | アクセス制限 |
|---------|-----------|----------|------|------------|
| API Backend | 8001 | HTTP/WS | REST API、WebSocket | 内部ネットワーク |
| Web Frontend | 3001 | HTTP | Next.js開発サーバー | 内部ネットワーク |
| PostgreSQL | 5432 | TCP | データベース接続 | DB専用VLAN |
| Redis | 6379 | TCP | キャッシュ接続 | Cache専用VLAN |
| HTTPS (Production) | 443 | HTTPS | 外部公開 | インターネット |

### 1.4 環境変数一覧

#### バックエンド環境変数 (.env)

```bash
# アプリケーション基本設定
APP_NAME=AI Interview System
APP_VERSION=1.0.0
ENVIRONMENT=production  # development / staging / production
DEBUG=false
LOG_LEVEL=INFO  # DEBUG / INFO / WARNING / ERROR / CRITICAL

# API設定
API_HOST=0.0.0.0
API_PORT=8001
API_PREFIX=/api/v1
ALLOWED_ORIGINS=https://app.example.com,https://staging.example.com

# データベース設定
DATABASE_URL=postgresql+asyncpg://user:password@db-host:5432/ai_interviewer
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_TIMEOUT=30
DATABASE_ECHO=false

# Redis設定
REDIS_URL=redis://redis-host:6379/0
REDIS_PASSWORD=your_redis_password
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_TIMEOUT=5

# JWT認証設定
JWT_SECRET_KEY=your-super-secret-jwt-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# MFA設定
MFA_ENABLED=true
MFA_ISSUER=AI Interview System
TOTP_SECRET_KEY=your-totp-secret-key

# AI Provider設定 (Azure OpenAI)
AI_PROVIDER=azure_openai  # azure_openai / aws_bedrock / gcp_vertex
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_ENDPOINT=https://your-instance.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_MAX_RETRIES=3
AZURE_OPENAI_TIMEOUT=60

# AI Provider設定 (AWS Bedrock - オプション)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
BEDROCK_MODEL_ID=anthropic.claude-v2

# AI Provider設定 (GCP Vertex AI - オプション)
GCP_PROJECT_ID=your-gcp-project
GCP_LOCATION=us-central1
VERTEX_AI_MODEL=gemini-pro

# WebSocket設定
WS_HEARTBEAT_INTERVAL=30
WS_MAX_CONNECTIONS_PER_USER=3
WS_MESSAGE_MAX_SIZE=1048576  # 1MB

# セキュリティ設定
CORS_ALLOWED_ORIGINS=https://app.example.com
RATE_LIMIT_PER_MINUTE=60
SESSION_TIMEOUT_MINUTES=60
CSRF_SECRET_KEY=your-csrf-secret-key

# 監視設定
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# 通知設定
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/YOUR/WEBHOOK/URL
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_FROM_ADDRESS=noreply@example.com
```

#### フロントエンド環境変数 (.env.local)

```bash
# Next.js設定
NEXT_PUBLIC_APP_NAME=AI Interview System
NEXT_PUBLIC_APP_VERSION=1.0.0
NEXT_PUBLIC_ENVIRONMENT=production

# API接続設定
NEXT_PUBLIC_API_BASE_URL=https://api.example.com/api/v1
NEXT_PUBLIC_WS_BASE_URL=wss://api.example.com/api/v1/ws

# 認証設定
NEXT_PUBLIC_AUTH_ENABLED=true
NEXT_PUBLIC_MFA_ENABLED=true

# 機能フラグ
NEXT_PUBLIC_FEATURE_CHAT_ENABLED=true
NEXT_PUBLIC_FEATURE_VIDEO_ENABLED=true
NEXT_PUBLIC_FEATURE_ANALYTICS_ENABLED=true

# 監視設定
NEXT_PUBLIC_SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
NEXT_PUBLIC_GA_TRACKING_ID=G-XXXXXXXXXX
```

---

## 2. 日常運用

### 2.1 ヘルスチェック手順

#### 2.1.1 基本ヘルスチェック

APIのヘルスチェックエンドポイントを定期的に確認します。

**エンドポイント:**
```
GET /api/v1/health
```

**正常なレスポンス例:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production",
  "timestamp": "2026-02-15T10:30:00Z",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 12,
      "connection_pool": {
        "size": 20,
        "in_use": 5,
        "available": 15
      }
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 3,
      "connected": true,
      "memory_used_mb": 128
    },
    "ai_provider": {
      "status": "healthy",
      "provider": "azure_openai",
      "response_time_ms": 450,
      "quota_remaining": 95000
    }
  }
}
```

**異常時のレスポンス例:**
```json
{
  "status": "degraded",
  "version": "1.0.0",
  "environment": "production",
  "timestamp": "2026-02-15T10:30:00Z",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 15
    },
    "redis": {
      "status": "unhealthy",
      "error": "Connection timeout after 5000ms",
      "connected": false
    },
    "ai_provider": {
      "status": "healthy",
      "provider": "azure_openai",
      "response_time_ms": 520
    }
  }
}
```

#### 2.1.2 ヘルスチェックコマンド

**curlでの確認:**
```bash
curl -X GET https://api.example.com/api/v1/health \
  -H "Accept: application/json" \
  -w "\nHTTP Status: %{http_code}\nTotal Time: %{time_total}s\n"
```

**監視スクリプト例 (Bash):**
```bash
#!/bin/bash
# health_check.sh

HEALTH_URL="https://api.example.com/api/v1/health"
SLACK_WEBHOOK="your-slack-webhook-url"

response=$(curl -s -w "\n%{http_code}" "$HEALTH_URL")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" -ne 200 ]; then
  message="⚠️ Health Check Failed: HTTP $http_code\n$body"
  curl -X POST "$SLACK_WEBHOOK" \
    -H 'Content-Type: application/json' \
    -d "{\"text\":\"$message\"}"
  exit 1
fi

status=$(echo "$body" | jq -r '.status')
if [ "$status" != "healthy" ]; then
  message="⚠️ System Status: $status\n\`\`\`$body\`\`\`"
  curl -X POST "$SLACK_WEBHOOK" \
    -H 'Content-Type: application/json' \
    -d "{\"text\":\"$message\"}"
  exit 1
fi

echo "✅ Health Check Passed"
exit 0
```

**crontabでの定期実行設定:**
```bash
# 5分ごとにヘルスチェック実行
*/5 * * * * /opt/scripts/health_check.sh >> /var/log/health_check.log 2>&1
```

### 2.2 ログ確認方法

#### 2.2.1 ログ形式

本システムは構造化ログ (JSON形式) を採用しています。

**ログ出力例:**
```json
{
  "timestamp": "2026-02-15T10:30:00.123Z",
  "level": "INFO",
  "service": "api-backend",
  "module": "grc_backend.api.routes.interviews",
  "request_id": "req_abc123xyz",
  "user_id": "user_123",
  "message": "Interview session started",
  "context": {
    "interview_id": "interview_456",
    "session_id": "session_789",
    "duration_minutes": 30
  },
  "performance": {
    "response_time_ms": 245
  }
}
```

#### 2.2.2 ログレベル定義

| レベル | 用途 | 保存期間 |
|-------|------|---------|
| **DEBUG** | 開発時のデバッグ情報 | 3日 |
| **INFO** | 通常の動作ログ (API呼び出し、セッション開始等) | 30日 |
| **WARNING** | 警告 (リトライ成功、軽微なエラー) | 90日 |
| **ERROR** | エラー (処理失敗、例外発生) | 180日 |
| **CRITICAL** | 重大なエラー (システム停止レベル) | 365日 |

#### 2.2.3 ログ確認コマンド

**Dockerコンテナのログ確認:**
```bash
# APIバックエンドのログ (最新100行)
docker logs --tail 100 ai-interviewer-api

# リアルタイムでログを追跡
docker logs -f ai-interviewer-api

# 特定時間範囲のログ
docker logs --since "2026-02-15T10:00:00" --until "2026-02-15T11:00:00" ai-interviewer-api
```

**JSONログのフィルタリング (jq使用):**
```bash
# ERRORレベル以上のログのみ抽出
docker logs ai-interviewer-api | grep '^{' | jq 'select(.level == "ERROR" or .level == "CRITICAL")'

# 特定ユーザーのログを抽出
docker logs ai-interviewer-api | grep '^{' | jq 'select(.user_id == "user_123")'

# API応答時間が1秒以上のログを抽出
docker logs ai-interviewer-api | grep '^{' | jq 'select(.performance.response_time_ms > 1000)'

# 過去1時間のエラー数をカウント
docker logs --since "1h" ai-interviewer-api | grep '^{' | jq -r '.level' | grep ERROR | wc -l
```

**Kubernetes環境でのログ確認:**
```bash
# Pod一覧取得
kubectl get pods -n ai-interviewer

# 特定Podのログ確認
kubectl logs -n ai-interviewer ai-interviewer-api-7d9f8c5b6-abcde

# 全てのAPIレプリカのログを確認
kubectl logs -n ai-interviewer -l app=ai-interviewer-api --tail=50

# ログをファイルに保存
kubectl logs -n ai-interviewer ai-interviewer-api-7d9f8c5b6-abcde > /tmp/api-logs.json
```

### 2.3 バッチ処理

#### 2.3.1 定期バッチ一覧

| バッチ名 | 実行頻度 | 実行時間 | 目的 |
|---------|---------|---------|------|
| **expired_sessions_cleanup** | 毎時 | 毎時00分 | 期限切れセッションの削除 |
| **token_cleanup** | 毎日 | 02:00 | 期限切れトークンの削除 |
| **analytics_aggregation** | 毎日 | 03:00 | 分析データの集計 |
| **backup_verification** | 毎日 | 04:00 | バックアップの検証 |
| **log_rotation** | 毎日 | 05:00 | ログローテーション |
| **certificate_check** | 毎週月曜 | 06:00 | SSL証明書の有効期限チェック |
| **dependency_scan** | 毎週月曜 | 07:00 | 依存パッケージの脆弱性スキャン |
| **monthly_report** | 毎月1日 | 08:00 | 月次レポート生成 |

#### 2.3.2 バッチ実行コマンド

**手動実行例:**
```bash
# 期限切れセッションクリーンアップ
python -m grc_backend.batch.cleanup_sessions

# トークンクリーンアップ
python -m grc_backend.batch.cleanup_tokens

# 分析データ集計
python -m grc_backend.batch.aggregate_analytics --date 2026-02-15

# バックアップ検証
python -m grc_backend.batch.verify_backups --backup-path /backups/latest
```

**crontab設定例:**
```bash
# 毎時00分: 期限切れセッションクリーンアップ
0 * * * * cd /app && python -m grc_backend.batch.cleanup_sessions >> /var/log/batch/cleanup_sessions.log 2>&1

# 毎日02:00: トークンクリーンアップ
0 2 * * * cd /app && python -m grc_backend.batch.cleanup_tokens >> /var/log/batch/cleanup_tokens.log 2>&1

# 毎日03:00: 分析データ集計
0 3 * * * cd /app && python -m grc_backend.batch.aggregate_analytics >> /var/log/batch/analytics.log 2>&1

# 毎週月曜06:00: 証明書チェック
0 6 * * 1 cd /app && python -m grc_backend.batch.check_certificates >> /var/log/batch/cert_check.log 2>&1
```

---

## 3. 監視設定

### 3.1 メトリクス一覧

#### 3.1.1 インフラストラクチャメトリクス

| カテゴリ | メトリクス名 | 説明 | 収集間隔 | 保存期間 |
|---------|------------|------|---------|---------|
| **CPU** | `cpu_usage_percent` | CPU使用率 (%) | 15秒 | 30日 |
| **メモリ** | `memory_usage_percent` | メモリ使用率 (%) | 15秒 | 30日 |
| **メモリ** | `memory_available_mb` | 利用可能メモリ (MB) | 15秒 | 30日 |
| **ディスク** | `disk_usage_percent` | ディスク使用率 (%) | 1分 | 90日 |
| **ディスク** | `disk_io_read_bytes` | ディスクI/O読み取り (bytes) | 15秒 | 7日 |
| **ディスク** | `disk_io_write_bytes` | ディスクI/O書き込み (bytes) | 15秒 | 7日 |
| **ネットワーク** | `network_in_bytes` | ネットワーク受信 (bytes) | 15秒 | 7日 |
| **ネットワーク** | `network_out_bytes` | ネットワーク送信 (bytes) | 15秒 | 7日 |

#### 3.1.2 アプリケーションメトリクス

| カテゴリ | メトリクス名 | 説明 | 収集間隔 | 保存期間 |
|---------|------------|------|---------|---------|
| **API** | `api_request_count` | API リクエスト数 | 15秒 | 90日 |
| **API** | `api_request_duration_ms` | API応答時間 (ms) - P50/P95/P99 | 15秒 | 90日 |
| **API** | `api_error_rate` | APIエラー率 (%) | 15秒 | 90日 |
| **API** | `api_requests_per_endpoint` | エンドポイント別リクエスト数 | 1分 | 30日 |
| **WebSocket** | `websocket_active_connections` | アクティブなWebSocket接続数 | 15秒 | 7日 |
| **WebSocket** | `websocket_message_count` | WebSocketメッセージ数 | 15秒 | 7日 |
| **WebSocket** | `websocket_disconnect_count` | WebSocket切断回数 | 15秒 | 30日 |
| **認証** | `auth_login_count` | ログイン試行回数 | 1分 | 90日 |
| **認証** | `auth_login_success_rate` | ログイン成功率 (%) | 1分 | 90日 |
| **認証** | `auth_mfa_verification_count` | MFA検証回数 | 1分 | 90日 |
| **面接** | `interview_active_sessions` | アクティブな面接セッション数 | 15秒 | 30日 |
| **面接** | `interview_completion_rate` | 面接完了率 (%) | 1時間 | 90日 |

#### 3.1.3 データベースメトリクス

| カテゴリ | メトリクス名 | 説明 | 収集間隔 | 保存期間 |
|---------|------------|------|---------|---------|
| **接続** | `db_connection_pool_size` | DB接続プールサイズ | 15秒 | 30日 |
| **接続** | `db_connection_pool_in_use` | DB接続プール使用中 | 15秒 | 30日 |
| **接続** | `db_connection_pool_available` | DB接続プール利用可能 | 15秒 | 30日 |
| **パフォーマンス** | `db_query_duration_ms` | DBクエリ実行時間 (ms) - P50/P95/P99 | 15秒 | 30日 |
| **パフォーマンス** | `db_slow_query_count` | スロークエリ数 (>1秒) | 1分 | 90日 |
| **リソース** | `db_active_transactions` | アクティブなトランザクション数 | 15秒 | 7日 |
| **リソース** | `db_locks_count` | ロック数 | 15秒 | 7日 |

#### 3.1.4 Redisメトリクス

| カテゴリ | メトリクス名 | 説明 | 収集間隔 | 保存期間 |
|---------|------------|------|---------|---------|
| **メモリ** | `redis_memory_used_mb` | Redis使用メモリ (MB) | 15秒 | 30日 |
| **メモリ** | `redis_memory_fragmentation_ratio` | メモリフラグメンテーション比率 | 1分 | 30日 |
| **パフォーマンス** | `redis_commands_per_second` | 秒間コマンド実行数 | 15秒 | 7日 |
| **パフォーマンス** | `redis_hit_rate` | キャッシュヒット率 (%) | 1分 | 30日 |
| **接続** | `redis_connected_clients` | 接続中クライアント数 | 15秒 | 7日 |
| **接続** | `redis_blocked_clients` | ブロック中クライアント数 | 15秒 | 7日 |

#### 3.1.5 AI Providerメトリクス

| カテゴリ | メトリクス名 | 説明 | 収集間隔 | 保存期間 |
|---------|------------|------|---------|---------|
| **リクエスト** | `ai_request_count` | AIリクエスト数 | 15秒 | 90日 |
| **リクエスト** | `ai_request_duration_ms` | AI応答時間 (ms) - P50/P95/P99 | 15秒 | 90日 |
| **リクエスト** | `ai_error_count` | AIエラー数 | 15秒 | 90日 |
| **リクエスト** | `ai_rate_limit_count` | レート制限発生回数 | 1分 | 90日 |
| **コスト** | `ai_token_usage_total` | トークン使用量 (累計) | 1時間 | 365日 |
| **コスト** | `ai_estimated_cost_usd` | 推定コスト (USD) | 1時間 | 365日 |

### 3.2 アラート閾値推奨値

#### 3.2.1 重要度レベル定義

| 重要度 | レベル | 対応時間 | 通知先 |
|-------|-------|---------|-------|
| **P1 - Critical** | システム停止、データ損失リスク | 即座 (15分以内) | SREチーム + 管理者 + Slack/Teams |
| **P2 - High** | 機能制限、パフォーマンス著しい低下 | 1時間以内 | SREチーム + Slack/Teams |
| **P3 - Medium** | 部分的な機能低下 | 4時間以内 | SREチーム + Slack |
| **P4 - Low** | 警告レベル、予防的措置 | 翌営業日 | Slack (通知のみ) |

#### 3.2.2 アラート閾値設定

| メトリクス | Warning (P4) | High (P3) | Critical (P2) | Emergency (P1) |
|-----------|-------------|-----------|--------------|---------------|
| **CPU使用率** | 70% (5分間) | 80% (5分間) | 90% (3分間) | 95% (1分間) |
| **メモリ使用率** | 75% (5分間) | 85% (5分間) | 90% (3分間) | 95% (1分間) |
| **ディスク使用率** | 70% | 80% | 90% | 95% |
| **API応答時間 (P95)** | 1000ms | 2000ms | 3000ms | 5000ms |
| **API応答時間 (P99)** | 2000ms | 3000ms | 5000ms | 10000ms |
| **APIエラー率** | 1% (5分間) | 3% (5分間) | 5% (3分間) | 10% (1分間) |
| **DB接続プール使用率** | 70% | 85% | 95% | 100% |
| **DBクエリ時間 (P95)** | 500ms | 1000ms | 2000ms | 5000ms |
| **Redis メモリ使用率** | 70% | 80% | 90% | 95% |
| **Redisキャッシュヒット率** | <80% (10分間) | <70% (10分間) | <60% (5分間) | <50% (3分間) |
| **WebSocket接続数** | - | - | 1000 (同時接続) | 1500 (同時接続) |
| **AI応答時間 (P95)** | 3000ms | 5000ms | 10000ms | 15000ms |
| **AIエラー率** | 2% (10分間) | 5% (10分間) | 10% (5分間) | 20% (3分間) |
| **証明書有効期限** | 30日以内 | 14日以内 | 7日以内 | 3日以内 |

### 3.3 Slack/Teams通知設定

#### 3.3.1 Slack Webhook設定

**1. Slack Appの作成:**
```
1. https://api.slack.com/apps にアクセス
2. "Create New App" → "From scratch"
3. App名: "AI Interviewer Monitoring"
4. Workspace選択
```

**2. Incoming Webhookの有効化:**
```
1. "Incoming Webhooks" をクリック
2. "Activate Incoming Webhooks" をオンに
3. "Add New Webhook to Workspace"
4. 通知先チャンネル選択 (例: #ai-interviewer-alerts)
5. Webhook URLをコピー (例: https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX)
```

**3. 環境変数に設定:**
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**4. 通知テスト:**
```bash
curl -X POST "${SLACK_WEBHOOK_URL}" \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "🧪 Test Alert from AI Interview System",
    "blocks": [
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text": "*Test Alert*\nThis is a test message from AI Interview System monitoring."
        }
      }
    ]
  }'
```

#### 3.3.2 Microsoft Teams Webhook設定

**1. Teams Connectorの追加:**
```
1. Teamsチャンネルを開く (例: AI Interviewer Alerts)
2. チャンネル名の [...] → "Connectors"
3. "Incoming Webhook" を検索 → "Configure"
4. 名前: "AI Interviewer Monitoring"
5. アイコンをアップロード (オプション)
6. "Create"
7. Webhook URLをコピー
```

**2. 環境変数に設定:**
```bash
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/YOUR/WEBHOOK/URL
```

**3. 通知テスト:**
```bash
curl -X POST "${TEAMS_WEBHOOK_URL}" \
  -H 'Content-Type: application/json' \
  -d '{
    "@type": "MessageCard",
    "@context": "https://schema.org/extensions",
    "summary": "Test Alert",
    "themeColor": "0078D4",
    "title": "🧪 Test Alert from AI Interview System",
    "sections": [
      {
        "activityTitle": "Test Message",
        "text": "This is a test message from AI Interview System monitoring.",
        "facts": [
          {
            "name": "Environment:",
            "value": "Production"
          },
          {
            "name": "Timestamp:",
            "value": "2026-02-15T10:30:00Z"
          }
        ]
      }
    ]
  }'
```

#### 3.3.3 アラート通知フォーマット例

**Critical Alert (P1) - Slack:**
```json
{
  "text": "🚨 CRITICAL: API Backend Down",
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "🚨 CRITICAL ALERT (P1)"
      }
    },
    {
      "type": "section",
      "fields": [
        {
          "type": "mrkdwn",
          "text": "*Service:*\nAPI Backend"
        },
        {
          "type": "mrkdwn",
          "text": "*Status:*\nDown"
        },
        {
          "type": "mrkdwn",
          "text": "*Environment:*\nProduction"
        },
        {
          "type": "mrkdwn",
          "text": "*Time:*\n2026-02-15 10:30:00 JST"
        }
      ]
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Error:* Health check endpoint /api/v1/health returned HTTP 503"
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Action Required:* Check container logs and restart if necessary\n`docker logs ai-interviewer-api`"
      }
    },
    {
      "type": "actions",
      "elements": [
        {
          "type": "button",
          "text": {
            "type": "plain_text",
            "text": "View Logs"
          },
          "url": "https://logs.example.com/api-backend"
        },
        {
          "type": "button",
          "text": {
            "type": "plain_text",
            "text": "View Dashboard"
          },
          "url": "https://monitoring.example.com/dashboard"
        }
      ]
    }
  ]
}
```

---

## 4. インシデント対応

### 4.1 障害レベル定義

| レベル | 定義 | 影響範囲 | 対応時間 | 例 |
|-------|------|---------|---------|---|
| **P1 - Critical** | システム全体停止、重大なセキュリティ侵害 | 全ユーザー | 即座 (15分以内) | API全停止、データベース停止、情報漏洩 |
| **P2 - High** | 主要機能停止、重大なパフォーマンス低下 | 多数のユーザー | 1時間以内 | 面接セッション開始不可、認証機能停止 |
| **P3 - Medium** | 部分的な機能停止、軽微なパフォーマンス低下 | 一部のユーザー | 4時間以内 | 特定機能のエラー、応答遅延 |
| **P4 - Low** | 軽微な問題、将来的な問題の予兆 | 限定的 | 翌営業日 | ログ警告、リソース使用率上昇 |

### 4.2 よくある障害パターンと対処法

#### 4.2.1 データベース接続タイムアウト

**症状:**
```
Error: asyncpg.exceptions.ConnectionTimeoutError: timeout acquiring a connection from the pool
```

**原因:**
- DB接続プールの枯渇
- 長時間実行されるクエリによるコネクション占有
- データベースサーバーの高負荷

**確認手順:**
```bash
# 1. 現在の接続プール状態を確認
curl https://api.example.com/api/v1/health | jq '.checks.database.connection_pool'

# 2. データベースの現在の接続数を確認
docker exec -it postgres psql -U postgres -d ai_interviewer -c \
  "SELECT count(*) FROM pg_stat_activity WHERE datname = 'ai_interviewer';"

# 3. 長時間実行中のクエリを確認
docker exec -it postgres psql -U postgres -d ai_interviewer -c \
  "SELECT pid, now() - query_start as duration, query FROM pg_stat_activity
   WHERE state = 'active' AND now() - query_start > interval '5 seconds'
   ORDER BY duration DESC;"
```

**対処法:**

**即座の対応:**
```bash
# 1. 長時間実行中のクエリを強制終了 (慎重に実行)
docker exec -it postgres psql -U postgres -d ai_interviewer -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity
   WHERE state = 'active' AND now() - query_start > interval '30 seconds'
   AND query NOT LIKE '%pg_stat_activity%';"

# 2. APIサーバーを再起動 (接続プールをリセット)
docker restart ai-interviewer-api

# 3. 接続プールサイズを一時的に増やす (環境変数を更新して再起動)
# DATABASE_POOL_SIZE=30 (デフォルト20から増加)
```

**恒久的な対応:**
```bash
# 1. スロークエリログを有効化してクエリ最適化
# postgresql.conf に追加:
# log_min_duration_statement = 1000  # 1秒以上のクエリをログ

# 2. 接続プールサイズの調整
# .env ファイル:
DATABASE_POOL_SIZE=30
DATABASE_MAX_OVERFLOW=20

# 3. データベースインデックスの追加 (スロークエリに基づく)
```

#### 4.2.2 Redis接続断

**症状:**
```
Error: redis.exceptions.ConnectionError: Error while reading from socket: ('Connection lost',)
```

**原因:**
- Redisサーバーの再起動
- ネットワーク不安定
- Redisメモリ不足によるクラッシュ
- maxclients制限到達

**確認手順:**
```bash
# 1. Redisサーバーの状態確認
docker exec -it redis redis-cli ping
# 期待される応答: PONG

# 2. Redis接続数確認
docker exec -it redis redis-cli INFO clients

# 3. Redisメモリ使用状況確認
docker exec -it redis redis-cli INFO memory

# 4. Redis設定確認
docker exec -it redis redis-cli CONFIG GET maxmemory
docker exec -it redis redis-cli CONFIG GET maxclients
```

**対処法:**

**即座の対応:**
```bash
# 1. Redisサーバー再起動
docker restart redis

# 2. Redis接続のクリア
docker exec -it redis redis-cli CLIENT LIST
docker exec -it redis redis-cli CLIENT KILL TYPE normal  # 通常接続をクリア

# 3. APIサーバー再起動 (Redis再接続)
docker restart ai-interviewer-api
```

**恒久的な対応:**
```bash
# 1. Redisメモリ制限の増加
# redis.conf:
maxmemory 2gb
maxmemory-policy allkeys-lru

# 2. Redis Sentinel / Cluster構成の導入 (高可用性)

# 3. 接続タイムアウト設定の調整
# .env ファイル:
REDIS_SOCKET_TIMEOUT=10
REDIS_MAX_CONNECTIONS=100
```

#### 4.2.3 AI API Rate Limit

**症状:**
```
Error: openai.error.RateLimitError: Rate limit reached for gpt-4 in organization org-xxx
```

**原因:**
- AIプロバイダーのレート制限超過
- 想定以上のリクエスト数
- リトライロジックの不備

**確認手順:**
```bash
# 1. 現在のAI使用状況確認
curl https://api.example.com/api/v1/health | jq '.checks.ai_provider'

# 2. 過去1時間のAIリクエスト数確認
docker logs --since "1h" ai-interviewer-api | grep '^{' | \
  jq -r 'select(.module == "ai_provider") | .message' | \
  grep -c "AI request"

# 3. エラー率の確認
docker logs --since "1h" ai-interviewer-api | grep '^{' | \
  jq -r 'select(.level == "ERROR" and .message | contains("RateLimitError"))' | wc -l
```

**対処法:**

**即座の対応:**
```bash
# 1. リクエストキューイングの有効化 (一時的な制限)
# アプリケーション設定で同時リクエスト数を制限

# 2. フォールバックAIプロバイダーへの切り替え
# 例: Azure OpenAI → AWS Bedrock
# 環境変数を更新:
AI_PROVIDER=aws_bedrock

# 3. キャッシュの活用 (同じ質問の再利用)
```

**恒久的な対応:**
```bash
# 1. レート制限を考慮したリトライロジック実装
# Exponential backoff + jitter

# 2. AIプロバイダーのクォータ増加申請

# 3. マルチプロバイダー構成 (負荷分散)
# Azure OpenAI + AWS Bedrock + GCP Vertex AI

# 4. リクエストバッファリング/キューイングシステム導入
# Redis Queue / Celery 等
```

#### 4.2.4 WebSocket切断頻発

**症状:**
```
Warning: WebSocket connection closed unexpectedly
Error: WebSocket ping timeout
```

**原因:**
- ロードバランサーのタイムアウト設定
- クライアント側のネットワーク不安定
- サーバー側のリソース不足
- Heartbeat設定の不備

**確認手順:**
```bash
# 1. アクティブなWebSocket接続数確認
curl https://api.example.com/api/v1/health | jq '.checks.websocket.active_connections'

# 2. 過去1時間の切断ログ確認
docker logs --since "1h" ai-interviewer-api | grep '^{' | \
  jq -r 'select(.message | contains("WebSocket disconnect"))' | \
  jq -r '[.timestamp, .context.disconnect_reason] | @tsv'

# 3. サーバーリソース確認
docker stats ai-interviewer-api --no-stream
```

**対処法:**

**即座の対応:**
```bash
# 1. ロードバランサーのタイムアウト設定確認・延長
# AWS ALB例:
aws elbv2 modify-target-group-attributes \
  --target-group-arn arn:aws:elasticloadbalancing:... \
  --attributes Key=deregistration_delay.timeout_seconds,Value=300

# 2. Heartbeat間隔の調整
# .env ファイル:
WS_HEARTBEAT_INTERVAL=20  # デフォルト30秒から短縮

# 3. 再接続ロジックの確認 (クライアント側)
```

**恒久的な対応:**
```bash
# 1. WebSocketプロキシ設定最適化
# nginx.conf例:
proxy_read_timeout 3600s;
proxy_send_timeout 3600s;
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";

# 2. WebSocket専用サーバーの分離

# 3. 接続管理の改善
# - 自動再接続機能
# - セッション状態の永続化
# - グレースフルシャットダウン
```

### 4.3 エスカレーションフロー

```
┌─────────────────────────────────────────────────────────────┐
│                     インシデント発生                          │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│   Level 1: 自動アラート検知 → Slack/Teams通知                 │
│   担当: 監視システム                                          │
│   アクション: 初動対応 (ログ確認、再起動等)                     │
│   時間: 即座～15分                                            │
└────────────────────────────┬────────────────────────────────┘
                             │
                             │ 15分以内に解決しない場合
                             ▼
┌─────────────────────────────────────────────────────────────┐
│   Level 2: オンコールSREエンジニア                             │
│   担当: SREチーム (交代制)                                     │
│   アクション: 詳細調査、緊急対応、回避策実施                     │
│   時間: 15分～1時間                                           │
└────────────────────────────┬────────────────────────────────┘
                             │
                             │ P1/P2で1時間以内に解決しない場合
                             ▼
┌─────────────────────────────────────────────────────────────┐
│   Level 3: シニアSRE + 開発チームリード                        │
│   担当: シニアエンジニア + アーキテクト                         │
│   アクション: 根本原因分析、アーキテクチャレベルの対応            │
│   時間: 1時間～4時間                                          │
└────────────────────────────┬────────────────────────────────┘
                             │
                             │ P1で4時間以内に解決しない場合
                             ▼
┌─────────────────────────────────────────────────────────────┐
│   Level 4: 経営層 + ベンダーサポート                           │
│   担当: CTO/VPoE + 外部専門家                                 │
│   アクション: 経営判断、顧客への公式アナウンス、外部支援要請      │
│   時間: 4時間以降                                             │
└─────────────────────────────────────────────────────────────┘
```

**連絡先リスト (テンプレート):**

| Level | 役割 | 担当者 | 連絡先 | 対応時間 |
|-------|------|--------|--------|---------|
| L1 | 監視システム | 自動 | Slack: #ai-interviewer-alerts | 24/7 |
| L2 | オンコールSRE | [名前] | Email: sre@example.com / Tel: xxx-xxxx-xxxx | 24/7 (交代制) |
| L3 | シニアSRE | [名前] | Email: senior-sre@example.com / Tel: xxx-xxxx-xxxx | 平日9-21時 |
| L3 | 開発リード | [名前] | Email: dev-lead@example.com / Tel: xxx-xxxx-xxxx | 平日9-21時 |
| L4 | CTO | [名前] | Email: cto@example.com / Tel: xxx-xxxx-xxxx | オンデマンド |

---

## 5. スケーリング

### 5.1 水平スケール (Horizontal Scaling)

#### 5.1.1 APIバックエンドのスケーリング

**スケーリング判断基準:**
- CPU使用率が70%を超えた状態が5分以上継続
- API応答時間P95が1000msを超える
- リクエストキューが溜まり始める

**Docker Composeでのスケール例:**
```bash
# 現在の状態確認
docker-compose ps

# APIレプリカを3台に増やす
docker-compose up -d --scale api=3

# 確認
docker-compose ps api
```

**Kubernetes (HPA) でのオートスケール設定:**
```yaml
# api-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ai-interviewer-api-hpa
  namespace: ai-interviewer
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-interviewer-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: api_request_duration_ms_p95
      target:
        type: AverageValue
        averageValue: "1000"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 25
        periodSeconds: 60
```

**適用:**
```bash
kubectl apply -f api-hpa.yaml

# HPA状態確認
kubectl get hpa -n ai-interviewer

# 詳細確認
kubectl describe hpa ai-interviewer-api-hpa -n ai-interviewer
```

#### 5.1.2 Webフロントエンドのスケーリング

**Next.js のスケーリング:**
```yaml
# web-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ai-interviewer-web-hpa
  namespace: ai-interviewer
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-interviewer-web
  minReplicas: 2
  maxReplicas: 8
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 75
```

**CDN活用によるスケーラビリティ向上:**
```bash
# 静的アセット (画像、CSS、JS) をCDNにオフロード
# CloudFront / Cloudflare / Fastly 等

# Next.js設定例 (next.config.js):
module.exports = {
  assetPrefix: process.env.CDN_URL || '',
  images: {
    domains: ['cdn.example.com'],
  },
}
```

### 5.2 垂直スケール (Vertical Scaling)

#### 5.2.1 PostgreSQLのスケーリング

**リソース増強の判断基準:**
- CPU使用率が80%を超える
- メモリ使用率が85%を超える
- ディスクI/O待ちが発生

**Docker Composeでのリソース調整:**
```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:15
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '2.0'
          memory: 4G
    environment:
      POSTGRES_SHARED_BUFFERS: 2GB
      POSTGRES_EFFECTIVE_CACHE_SIZE: 6GB
      POSTGRES_WORK_MEM: 64MB
      POSTGRES_MAINTENANCE_WORK_MEM: 512MB
```

**PostgreSQL設定最適化 (postgresql.conf):**
```conf
# メモリ設定 (サーバーメモリ8GBの場合)
shared_buffers = 2GB
effective_cache_size = 6GB
work_mem = 64MB
maintenance_work_mem = 512MB

# 接続設定
max_connections = 200

# WAL設定
wal_buffers = 16MB
checkpoint_completion_target = 0.9
max_wal_size = 2GB

# クエリプランナー
random_page_cost = 1.1  # SSD使用時
effective_io_concurrency = 200
```

**適用:**
```bash
# PostgreSQLコンテナ再起動
docker-compose restart postgres

# 設定確認
docker exec -it postgres psql -U postgres -c "SHOW shared_buffers;"
docker exec -it postgres psql -U postgres -c "SHOW max_connections;"
```

#### 5.2.2 Redisのスケーリング

**リソース増強の判断基準:**
- メモリ使用率が80%を超える
- メモリフラグメンテーション比率が1.5を超える
- スワップ使用が発生

**Docker Composeでのリソース調整:**
```yaml
# docker-compose.yml
services:
  redis:
    image: redis:7
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
    command: >
      redis-server
      --maxmemory 3gb
      --maxmemory-policy allkeys-lru
      --save ""
      --appendonly yes
```

**Redis Cluster構成 (高可用性 + スケーラビリティ):**
```bash
# Redis Cluster 6ノード構成 (3 primary + 3 replica)
# docker-compose.cluster.yml
version: '3.8'
services:
  redis-node-1:
    image: redis:7
    command: redis-server --cluster-enabled yes --port 7001
    ports: ["7001:7001"]
  redis-node-2:
    image: redis:7
    command: redis-server --cluster-enabled yes --port 7002
    ports: ["7002:7002"]
  redis-node-3:
    image: redis:7
    command: redis-server --cluster-enabled yes --port 7003
    ports: ["7003:7003"]
  redis-node-4:
    image: redis:7
    command: redis-server --cluster-enabled yes --port 7004
    ports: ["7004:7004"]
  redis-node-5:
    image: redis:7
    command: redis-server --cluster-enabled yes --port 7005
    ports: ["7005:7005"]
  redis-node-6:
    image: redis:7
    command: redis-server --cluster-enabled yes --port 7006
    ports: ["7006:7006"]

# クラスター初期化
docker exec -it redis-node-1 redis-cli --cluster create \
  redis-node-1:7001 redis-node-2:7002 redis-node-3:7003 \
  redis-node-4:7004 redis-node-5:7005 redis-node-6:7006 \
  --cluster-replicas 1
```

### 5.3 オートスケール設定例

#### 5.3.1 AWS ECS Fargate オートスケール

```json
{
  "serviceArn": "arn:aws:ecs:ap-northeast-1:123456789012:service/ai-interviewer/api",
  "scalableTarget": {
    "minCapacity": 3,
    "maxCapacity": 10,
    "resourceId": "service/ai-interviewer/api",
    "scalableDimension": "ecs:service:DesiredCount"
  },
  "scalingPolicies": [
    {
      "policyName": "cpu-scale-up",
      "policyType": "TargetTrackingScaling",
      "targetTrackingScalingPolicyConfiguration": {
        "targetValue": 70.0,
        "predefinedMetricSpecification": {
          "predefinedMetricType": "ECSServiceAverageCPUUtilization"
        },
        "scaleOutCooldown": 60,
        "scaleInCooldown": 300
      }
    },
    {
      "policyName": "memory-scale-up",
      "policyType": "TargetTrackingScaling",
      "targetTrackingScalingPolicyConfiguration": {
        "targetValue": 80.0,
        "predefinedMetricSpecification": {
          "predefinedMetricType": "ECSServiceAverageMemoryUtilization"
        },
        "scaleOutCooldown": 60,
        "scaleInCooldown": 300
      }
    },
    {
      "policyName": "request-count-scale",
      "policyType": "TargetTrackingScaling",
      "targetTrackingScalingPolicyConfiguration": {
        "targetValue": 1000.0,
        "customizedMetricSpecification": {
          "metricName": "RequestCountPerTarget",
          "namespace": "AWS/ApplicationELB",
          "statistic": "Sum"
        },
        "scaleOutCooldown": 60,
        "scaleInCooldown": 300
      }
    }
  ]
}
```

#### 5.3.2 GCP Cloud Run オートスケール

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: ai-interviewer-api
  namespace: default
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "3"
        autoscaling.knative.dev/maxScale: "10"
        autoscaling.knative.dev/target: "70"
        autoscaling.knative.dev/metric: "cpu"
    spec:
      containers:
      - image: gcr.io/project-id/ai-interviewer-api:latest
        resources:
          limits:
            cpu: "2"
            memory: "4Gi"
          requests:
            cpu: "1"
            memory: "2Gi"
        env:
        - name: ENVIRONMENT
          value: "production"
```

---

## 6. デプロイ運用

### 6.1 CI/CD (GitHub Actions)

#### 6.1.1 CI/CDワークフロー概要

```
┌─────────────────────────────────────────────────────────────┐
│  Git Push (feature branch)                                  │
└────────────────────────────┬────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  CI: Linting + Unit Tests                                   │
│  - ruff (Python), eslint (TypeScript)                       │
│  - pytest (backend), vitest (frontend)                      │
│  - カバレッジ80%以上必須                                       │
└────────────────────────────┬────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  Pull Request作成                                            │
└────────────────────────────┬────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  CI: Integration Tests                                      │
│  - API統合テスト (pytest + httpx)                            │
│  - E2Eテスト (Playwright)                                    │
└────────────────────────────┬────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  Code Review + Approval                                     │
└────────────────────────────┬────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  Merge to main branch                                       │
└────────────────────────────┬────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  CD: Build & Deploy to Staging                              │
│  - Dockerイメージビルド                                       │
│  - Stagingへデプロイ                                          │
│  - Smoke Test実行                                            │
└────────────────────────────┬────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  Manual Approval (Staging検証完了)                           │
└────────────────────────────┬────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  CD: Deploy to Production                                   │
│  - Blue/Green Deployment                                    │
│  - Health Check                                             │
│  - Rollback準備完了                                          │
└─────────────────────────────────────────────────────────────┘
```

#### 6.1.2 GitHub Actions設定

**.github/workflows/ci.yml:**
```yaml
name: CI

on:
  push:
    branches: [main, develop, 'feature/**']
  pull_request:
    branches: [main, develop]

jobs:
  lint-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd apps/backend
          pip install -r requirements.txt
          pip install ruff pytest pytest-cov
      - name: Run ruff
        run: cd apps/backend && ruff check .
      - name: Run ruff format check
        run: cd apps/backend && ruff format --check .

  lint-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
        with:
          version: 8
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'
      - name: Install dependencies
        run: pnpm install
      - name: Run eslint
        run: pnpm lint
      - name: Run type check
        run: pnpm type-check

  test-backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd apps/backend
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      - name: Run tests
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:testpass@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0
        run: |
          cd apps/backend
          pytest --cov=grc_backend --cov-report=xml --cov-report=term
      - name: Check coverage
        run: |
          cd apps/backend
          coverage report --fail-under=80

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
        with:
          version: 8
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'
      - name: Install dependencies
        run: pnpm install
      - name: Run unit tests
        run: pnpm test:unit
      - name: Check coverage
        run: pnpm test:coverage --reporter=text --reporter=json-summary

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
        with:
          version: 8
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'
      - name: Install dependencies
        run: pnpm install
      - name: Install Playwright
        run: pnpm exec playwright install --with-deps
      - name: Start services
        run: docker-compose up -d
      - name: Wait for services
        run: |
          timeout 60 bash -c 'until curl -f http://localhost:8001/api/v1/health; do sleep 2; done'
      - name: Run E2E tests
        run: pnpm test:e2e
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: playwright-report/
```

**.github/workflows/cd-staging.yml:**
```yaml
name: CD - Staging

on:
  push:
    branches: [main]

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-northeast-1

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build and push backend image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: ai-interviewer-api
          IMAGE_TAG: ${{ github.sha }}
        run: |
          cd apps/backend
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:staging
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:staging

      - name: Build and push frontend image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: ai-interviewer-web
          IMAGE_TAG: ${{ github.sha }}
        run: |
          cd apps/web
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:staging
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:staging

      - name: Deploy to ECS Staging
        run: |
          aws ecs update-service \
            --cluster ai-interviewer-staging \
            --service api \
            --force-new-deployment

          aws ecs update-service \
            --cluster ai-interviewer-staging \
            --service web \
            --force-new-deployment

      - name: Wait for deployment
        run: |
          aws ecs wait services-stable \
            --cluster ai-interviewer-staging \
            --services api web

      - name: Run smoke tests
        run: |
          curl -f https://staging-api.example.com/api/v1/health || exit 1
          curl -f https://staging.example.com/ || exit 1

      - name: Notify Slack
        if: always()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "Staging Deployment: ${{ job.status }}",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Staging Deployment ${{ job.status }}*\nCommit: ${{ github.sha }}\nAuthor: ${{ github.actor }}"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

**.github/workflows/cd-production.yml:**
```yaml
name: CD - Production

on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to deploy (git tag or commit SHA)'
        required: true

jobs:
  deploy-production:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.inputs.version }}

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-northeast-1

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Pull staging images
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        run: |
          docker pull $ECR_REGISTRY/ai-interviewer-api:staging
          docker pull $ECR_REGISTRY/ai-interviewer-web:staging

      - name: Tag for production
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          VERSION: ${{ github.event.inputs.version }}
        run: |
          docker tag $ECR_REGISTRY/ai-interviewer-api:staging $ECR_REGISTRY/ai-interviewer-api:$VERSION
          docker tag $ECR_REGISTRY/ai-interviewer-api:staging $ECR_REGISTRY/ai-interviewer-api:production
          docker tag $ECR_REGISTRY/ai-interviewer-web:staging $ECR_REGISTRY/ai-interviewer-web:$VERSION
          docker tag $ECR_REGISTRY/ai-interviewer-web:staging $ECR_REGISTRY/ai-interviewer-web:production

          docker push $ECR_REGISTRY/ai-interviewer-api:$VERSION
          docker push $ECR_REGISTRY/ai-interviewer-api:production
          docker push $ECR_REGISTRY/ai-interviewer-web:$VERSION
          docker push $ECR_REGISTRY/ai-interviewer-web:production

      - name: Deploy to ECS Production (Blue/Green)
        run: |
          # Blue/Green デプロイメントの開始
          aws deploy create-deployment \
            --application-name ai-interviewer \
            --deployment-group-name production \
            --deployment-config-name CodeDeployDefault.ECSAllAtOnce \
            --description "Deploying version ${{ github.event.inputs.version }}"

      - name: Wait for deployment
        run: |
          # デプロイメント完了待機 (タイムアウト: 30分)
          timeout 1800 bash -c 'until aws ecs wait services-stable --cluster ai-interviewer-production --services api web; do sleep 10; done'

      - name: Health check
        run: |
          for i in {1..10}; do
            if curl -f https://api.example.com/api/v1/health; then
              echo "Health check passed"
              exit 0
            fi
            echo "Health check failed, retrying in 10s..."
            sleep 10
          done
          echo "Health check failed after 10 attempts"
          exit 1

      - name: Notify Slack
        if: always()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "Production Deployment: ${{ job.status }}",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Production Deployment ${{ job.status }}*\nVersion: ${{ github.event.inputs.version }}\nTriggered by: ${{ github.actor }}"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### 6.2 デプロイ手順

#### 6.2.1 Staging環境へのデプロイ

**自動デプロイ (main branchへのマージで自動実行):**
```bash
# 1. feature branchで開発
git checkout -b feature/new-feature

# 2. 変更をコミット
git add .
git commit -m "Add new feature"

# 3. GitHub にpush
git push origin feature/new-feature

# 4. Pull Request作成 (GitHub UI)

# 5. CI通過 & Code Review完了後、main へマージ
# → 自動的にStagingへデプロイ
```

**手動確認:**
```bash
# Staging環境のヘルスチェック
curl https://staging-api.example.com/api/v1/health

# Stagingでの動作確認
# - ログイン機能テスト
# - 面接セッション開始テスト
# - WebSocket接続テスト
```

#### 6.2.2 Production環境へのデプロイ

**手動承認によるデプロイ:**
```bash
# 1. GitHub Actions の "CD - Production" ワークフローを実行
# https://github.com/your-org/ai-interviewer/actions/workflows/cd-production.yml

# 2. "Run workflow" をクリック
# 3. デプロイするバージョンを入力 (例: v1.2.3 または commit SHA)
# 4. "Run workflow" で実行開始

# 5. デプロイ監視
# GitHub Actions のログをリアルタイムで確認

# 6. デプロイ完了後、Health Check
curl https://api.example.com/api/v1/health

# 7. 本番環境での動作確認
# - ユーザー向け機能テスト
# - パフォーマンス確認
# - ログ監視
```

### 6.3 ロールバック手順

#### 6.3.1 緊急ロールバック (Production)

**手順:**
```bash
# 1. 現在のデプロイ状況確認
aws ecs describe-services \
  --cluster ai-interviewer-production \
  --services api web

# 2. 直前の安定バージョンを確認
aws ecr describe-images \
  --repository-name ai-interviewer-api \
  --query 'sort_by(imageDetails,& imagePushedAt)[-5:]'

# 3. ロールバック実行 (前バージョンのタグに戻す)
PREVIOUS_VERSION="v1.2.2"  # ロールバック先のバージョン

# APIサービスのロールバック
aws ecs update-service \
  --cluster ai-interviewer-production \
  --service api \
  --task-definition ai-interviewer-api:$(aws ecs describe-task-definition --task-definition ai-interviewer-api --query 'taskDefinition.revision' --output text)

# タスク定義を前バージョンに戻す
aws ecs register-task-definition \
  --cli-input-json file://task-definition-api-$PREVIOUS_VERSION.json

aws ecs update-service \
  --cluster ai-interviewer-production \
  --service api \
  --task-definition ai-interviewer-api:$(aws ecs describe-task-definition --task-definition ai-interviewer-api --query 'taskDefinition.revision' --output text) \
  --force-new-deployment

# 4. サービス安定化待機
aws ecs wait services-stable \
  --cluster ai-interviewer-production \
  --services api web

# 5. Health Check
curl https://api.example.com/api/v1/health

# 6. Slack通知
curl -X POST $SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "🔄 Rollback completed to version '"$PREVIOUS_VERSION"'",
    "blocks": [
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text": "*Rollback Completed*\nVersion: '"$PREVIOUS_VERSION"'\nPerformed by: '"$USER"'"
        }
      }
    ]
  }'
```

#### 6.3.2 データベースマイグレーションのロールバック

**注意:** データベースのロールバックは慎重に行う必要があります。

```bash
# 1. 現在のマイグレーション状態確認
docker exec -it ai-interviewer-api alembic current

# 2. マイグレーション履歴確認
docker exec -it ai-interviewer-api alembic history

# 3. 1つ前のマイグレーションに戻す
docker exec -it ai-interviewer-api alembic downgrade -1

# 4. 特定のリビジョンに戻す
docker exec -it ai-interviewer-api alembic downgrade abc123def456

# 5. データ整合性確認
docker exec -it postgres psql -U postgres -d ai_interviewer -c "SELECT COUNT(*) FROM users;"
docker exec -it postgres psql -U postgres -d ai_interviewer -c "SELECT COUNT(*) FROM interviews;"

# 6. アプリケーション再起動
docker restart ai-interviewer-api
```

---

## 7. セキュリティ運用

### 7.1 証明書更新 (TLS)

#### 7.1.1 Let's Encrypt証明書の自動更新

**Certbot自動更新設定:**
```bash
# Certbotインストール (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# 証明書取得 (初回)
sudo certbot --nginx -d api.example.com -d example.com

# 自動更新設定 (cron)
sudo crontab -e

# 毎日2:30に証明書更新チェック
30 2 * * * certbot renew --quiet --post-hook "systemctl reload nginx"
```

**証明書有効期限チェックスクリプト:**
```bash
#!/bin/bash
# check_certificate.sh

DOMAIN="api.example.com"
SLACK_WEBHOOK="your-slack-webhook-url"
WARNING_DAYS=30

# 証明書の有効期限を取得
expiry_date=$(echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
expiry_epoch=$(date -d "$expiry_date" +%s)
current_epoch=$(date +%s)
days_remaining=$(( ($expiry_epoch - $current_epoch) / 86400 ))

echo "Certificate for $DOMAIN expires in $days_remaining days"

if [ $days_remaining -le $WARNING_DAYS ]; then
  severity="WARNING"
  icon="⚠️"

  if [ $days_remaining -le 7 ]; then
    severity="CRITICAL"
    icon="🚨"
  fi

  message="${icon} ${severity}: SSL Certificate for ${DOMAIN} expires in ${days_remaining} days"

  curl -X POST "$SLACK_WEBHOOK" \
    -H 'Content-Type: application/json' \
    -d "{
      \"text\": \"$message\",
      \"blocks\": [
        {
          \"type\": \"section\",
          \"text\": {
            \"type\": \"mrkdwn\",
            \"text\": \"*$message*\nExpiry Date: $expiry_date\"
          }
        }
      ]
    }"
fi
```

#### 7.1.2 ワイルドカード証明書の管理

**AWS Certificate Manager (ACM) の場合:**
```bash
# 証明書リスト確認
aws acm list-certificates --region ap-northeast-1

# 証明書詳細確認
aws acm describe-certificate \
  --certificate-arn arn:aws:acm:ap-northeast-1:123456789012:certificate/abc123 \
  --region ap-northeast-1

# 証明書有効期限チェック (CloudWatch Alarmで自動化推奨)
aws cloudwatch put-metric-alarm \
  --alarm-name acm-certificate-expiry \
  --alarm-description "Alert when ACM certificate is expiring" \
  --metric-name DaysToExpiry \
  --namespace AWS/CertificateManager \
  --statistic Minimum \
  --period 86400 \
  --evaluation-periods 1 \
  --threshold 30 \
  --comparison-operator LessThanThreshold \
  --alarm-actions arn:aws:sns:ap-northeast-1:123456789012:ops-alerts
```

### 7.2 APIキーローテーション

#### 7.2.1 JWT Secret Key ローテーション

**手順:**
```bash
# 1. 新しいJWT Secret Keyを生成
NEW_JWT_SECRET=$(openssl rand -hex 32)

# 2. 環境変数に両方のキーを設定 (一時的にデュアル運用)
# .env.production:
JWT_SECRET_KEY=old-secret-key
JWT_SECRET_KEY_NEW=new-secret-key-generated-above

# 3. アプリケーション側で両方のキーを検証できるように実装
# grc_backend/auth/jwt.py:
# - トークン生成: 新キーを使用
# - トークン検証: 新キー優先、失敗したら旧キーで検証

# 4. デプロイ
docker-compose up -d

# 5. 1週間後、旧キーを削除 (全トークンが新キーで再発行された後)
# .env.production:
JWT_SECRET_KEY=new-secret-key-generated-above
# JWT_SECRET_KEY_NEW を削除

# 6. 再デプロイ
docker-compose up -d
```

#### 7.2.2 AI Provider API Key ローテーション

**Azure OpenAI API Key:**
```bash
# 1. Azure Portalで新しいキーを生成
# Azure Portal → Azure OpenAI リソース → Keys and Endpoint → Regenerate Key 2

# 2. 環境変数を更新
# .env.production:
AZURE_OPENAI_API_KEY=new-api-key-from-azure-portal

# 3. アプリケーション再起動 (ダウンタイムなし)
docker-compose up -d --no-deps api

# 4. Health Check
curl https://api.example.com/api/v1/health | jq '.checks.ai_provider'

# 5. 旧キーを無効化 (Azure Portal)
```

**AWS Bedrock Credentials:**
```bash
# 1. 新しいIAM Access Keyを生成
aws iam create-access-key --user-name ai-interviewer-service

# 2. 環境変数を更新
# .env.production:
AWS_ACCESS_KEY_ID=new-access-key-id
AWS_SECRET_ACCESS_KEY=new-secret-access-key

# 3. アプリケーション再起動
docker-compose up -d --no-deps api

# 4. 旧Access Keyを削除
aws iam delete-access-key --user-name ai-interviewer-service --access-key-id OLD_KEY_ID
```

### 7.3 依存パッケージセキュリティスキャン

#### 7.3.1 Dependabot設定

**.github/dependabot.yml:**
```yaml
version: 2
updates:
  # Pythonパッケージ (backend)
  - package-ecosystem: "pip"
    directory: "/apps/backend"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
    open-pull-requests-limit: 10
    reviewers:
      - "sre-team"
    labels:
      - "dependencies"
      - "python"
    commit-message:
      prefix: "chore(deps)"
    ignore:
      - dependency-name: "*"
        update-types: ["version-update:semver-major"]  # メジャーバージョンアップは手動確認

  # npmパッケージ (frontend)
  - package-ecosystem: "npm"
    directory: "/apps/web"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
    open-pull-requests-limit: 10
    reviewers:
      - "sre-team"
    labels:
      - "dependencies"
      - "javascript"
    commit-message:
      prefix: "chore(deps)"
    ignore:
      - dependency-name: "*"
        update-types: ["version-update:semver-major"]

  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "monthly"
    labels:
      - "dependencies"
      - "github-actions"
```

#### 7.3.2 手動セキュリティスキャン

**Python (backend):**
```bash
# pip-audit でセキュリティスキャン
cd apps/backend
pip install pip-audit
pip-audit

# Safetyでセキュリティスキャン
pip install safety
safety check --json

# Banditで静的解析 (セキュリティ脆弱性検出)
pip install bandit
bandit -r grc_backend/ -f json -o security-report.json
```

**Node.js (frontend):**
```bash
# npm audit
cd apps/web
pnpm audit

# 自動修正可能な脆弱性を修正
pnpm audit --fix

# 詳細レポート
pnpm audit --json > security-audit.json
```

**Docker イメージスキャン:**
```bash
# Trivyでコンテナイメージスキャン
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image ai-interviewer-api:latest

# 重大度HIGH以上のみ表示
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image --severity HIGH,CRITICAL ai-interviewer-api:latest

# JSON形式で出力
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image --format json --output trivy-report.json ai-interviewer-api:latest
```

### 7.4 アクセスログ監査

#### 7.4.1 アクセスログ形式

**Nginx アクセスログ (JSON形式):**
```nginx
# /etc/nginx/nginx.conf
log_format json_combined escape=json
  '{'
    '"time_local":"$time_local",'
    '"remote_addr":"$remote_addr",'
    '"remote_user":"$remote_user",'
    '"request":"$request",'
    '"status": "$status",'
    '"body_bytes_sent":"$body_bytes_sent",'
    '"request_time":"$request_time",'
    '"http_referrer":"$http_referer",'
    '"http_user_agent":"$http_user_agent",'
    '"http_x_forwarded_for":"$http_x_forwarded_for"'
  '}';

access_log /var/log/nginx/access.log json_combined;
```

#### 7.4.2 不審なアクセスパターンの検出

**監査スクリプト例:**
```bash
#!/bin/bash
# audit_access_logs.sh

LOG_FILE="/var/log/nginx/access.log"
SLACK_WEBHOOK="your-slack-webhook-url"

# 過去1時間のログを解析
since_time=$(date -d '1 hour ago' '+%d/%b/%Y:%H:%M:%S')

# 1. 大量の4xx/5xxエラー検出 (IP単位)
suspicious_ips=$(cat $LOG_FILE | \
  jq -r 'select(.status >= "400") | .remote_addr' | \
  sort | uniq -c | sort -rn | \
  awk '$1 > 100 {print $2}')

if [ ! -z "$suspicious_ips" ]; then
  echo "⚠️ Suspicious IPs with high error rate detected:"
  echo "$suspicious_ips"

  curl -X POST "$SLACK_WEBHOOK" \
    -H 'Content-Type: application/json' \
    -d "{
      \"text\": \"⚠️ Security Alert: Suspicious IPs detected\",
      \"blocks\": [
        {
          \"type\": \"section\",
          \"text\": {
            \"type\": \"mrkdwn\",
            \"text\": \"*IPs with >100 errors in the last hour:*\n\`\`\`$suspicious_ips\`\`\`\"
          }
        }
      ]
    }"
fi

# 2. 認証失敗の多いIP検出
auth_failures=$(cat $LOG_FILE | \
  jq -r 'select(.request | contains("/auth/login") and .status == "401") | .remote_addr' | \
  sort | uniq -c | sort -rn | \
  awk '$1 > 10 {print $2}')

if [ ! -z "$auth_failures" ]; then
  echo "🚨 Brute force attack detected:"
  echo "$auth_failures"

  # 該当IPをブロック (fail2ban等と連携)
  for ip in $auth_failures; do
    echo "Blocking IP: $ip"
    iptables -A INPUT -s $ip -j DROP
  done
fi

# 3. SQLインジェクション試行検出
sql_injection=$(cat $LOG_FILE | \
  jq -r 'select(.request | test("(SELECT|UNION|DROP|INSERT|UPDATE|DELETE|\\-\\-|;)"; "i")) | .remote_addr' | \
  sort | uniq)

if [ ! -z "$sql_injection" ]; then
  echo "🚨 SQL Injection attempt detected:"
  echo "$sql_injection"

  curl -X POST "$SLACK_WEBHOOK" \
    -H 'Content-Type: application/json' \
    -d "{
      \"text\": \"🚨 CRITICAL: SQL Injection attempt detected\",
      \"blocks\": [
        {
          \"type\": \"section\",
          \"text\": {
            \"type\": \"mrkdwn\",
            \"text\": \"*IPs attempting SQL injection:*\n\`\`\`$sql_injection\`\`\`\"
          }
        }
      ]
    }"
fi
```

**crontab設定:**
```bash
# 毎時00分にアクセスログ監査実行
0 * * * * /opt/scripts/audit_access_logs.sh >> /var/log/security/audit.log 2>&1
```

---

## 付録

### A. トラブルシューティングチェックリスト

**システム全体が応答しない場合:**
```
□ ロードバランサーのステータス確認
□ APIサーバーのプロセス確認 (docker ps / kubectl get pods)
□ ヘルスチェックエンドポイント確認 (/api/v1/health)
□ データベース接続確認
□ Redis接続確認
□ ネットワーク接続確認
□ リソース使用状況確認 (CPU/メモリ/ディスク)
□ ログ確認 (エラーメッセージの特定)
```

**パフォーマンス低下の場合:**
```
□ API応答時間の確認 (P50/P95/P99)
□ データベースクエリ時間の確認
□ スロークエリログの確認
□ Redis キャッシュヒット率の確認
□ AI Provider応答時間の確認
□ リソース使用率の確認 (CPU/メモリ)
□ 同時接続数の確認
□ ネットワーク帯域の確認
```

### B. 連絡先・参考リソース

**社内連絡先:**
| 担当 | Email | 電話 | 対応時間 |
|------|-------|------|---------|
| SREチーム | sre@example.com | xxx-xxxx-xxxx | 24/7 |
| 開発チーム | dev@example.com | xxx-xxxx-xxxx | 平日9-18時 |
| セキュリティチーム | security@example.com | xxx-xxxx-xxxx | 平日9-18時 |

**外部サポート:**
| サービス | サポート窓口 | SLA |
|---------|------------|-----|
| Azure OpenAI | https://azure.microsoft.com/support/ | Business: 1時間以内 |
| AWS | https://aws.amazon.com/premiumsupport/ | Business: 1時間以内 |
| PostgreSQL | https://www.postgresql.org/support/ | コミュニティ |

**ドキュメント:**
- システムアーキテクチャ: `/docs/architecture/ARCHITECTURE.md`
- API仕様: `/docs/api/API_SPECIFICATION.md`
- 開発者ガイド: `/docs/development/DEVELOPER_GUIDE.md`

---

**END OF OPERATION MANUAL**
