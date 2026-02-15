# AI面接システム 保守運用マニュアル

**バージョン**: 1.0
**最終更新日**: 2026-02-15
**対象者**: システム管理者、DevOpsエンジニア

---

## 目次

1. [データベース保守](#1-データベース保守)
2. [Redis保守](#2-redis保守)
3. [アプリケーション保守](#3-アプリケーション保守)
4. [インフラ保守](#4-インフラ保守)
5. [AIプロバイダー保守](#5-aiプロバイダー保守)
6. [ログ管理](#6-ログ管理)
7. [定期保守スケジュール](#7-定期保守スケジュール)
8. [障害復旧手順(DR)](#8-障害復旧手順dr)

---

## 1. データベース保守

### 1.1 Alembicマイグレーション管理

#### マイグレーションの適用

```bash
# 最新バージョンにアップグレード
cd apps/backend
alembic upgrade head

# 特定のリビジョンにアップグレード
alembic upgrade <revision_id>

# 現在のマイグレーション状態確認
alembic current

# マイグレーション履歴確認
alembic history --verbose
```

#### マイグレーションのロールバック

```bash
# 1つ前のバージョンにダウングレード
alembic downgrade -1

# 特定のリビジョンにダウングレード
alembic downgrade <revision_id>

# 初期状態に戻す（注意: 全データ削除）
alembic downgrade base
```

#### 新規マイグレーションの作成

```bash
# モデル変更を自動検出してマイグレーション生成
alembic revision --autogenerate -m "説明メッセージ"

# 空のマイグレーションファイル作成
alembic revision -m "カスタムマイグレーション"
```

**注意事項**:
- 本番環境でのマイグレーション実行前に必ずバックアップを取得
- `--autogenerate`は100%正確ではないため、生成されたファイルを必ず手動レビュー
- ダウングレード処理も必ず実装すること

### 1.2 データベースバックアップ/リストア

#### バックアップ手順

```bash
# 完全バックアップ（全データベース）
pg_dump -h localhost -U grc_user -d grc_db -F c -b -v -f backup_$(date +%Y%m%d_%H%M%S).dump

# スキーマのみバックアップ
pg_dump -h localhost -U grc_user -d grc_db -s -f schema_$(date +%Y%m%d).sql

# 特定のテーブルのみバックアップ
pg_dump -h localhost -U grc_user -d grc_db -t interview_sessions -F c -f sessions_backup.dump

# SQL形式でバックアップ（圧縮）
pg_dump -h localhost -U grc_user -d grc_db | gzip > backup_$(date +%Y%m%d).sql.gz
```

#### リストア手順

```bash
# カスタム形式からリストア
pg_restore -h localhost -U grc_user -d grc_db_new -v backup_20260215.dump

# SQL形式からリストア
psql -h localhost -U grc_user -d grc_db < backup_20260215.sql

# 圧縮ファイルからリストア
gunzip -c backup_20260215.sql.gz | psql -h localhost -U grc_user -d grc_db

# 特定のテーブルのみリストア
pg_restore -h localhost -U grc_user -d grc_db -t interview_sessions sessions_backup.dump
```

#### 自動バックアップスクリプト

```bash
#!/bin/bash
# daily_backup.sh

BACKUP_DIR="/var/backups/postgresql"
RETENTION_DAYS=30
DB_NAME="grc_db"
DB_USER="grc_user"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# バックアップ実行
pg_dump -h localhost -U $DB_USER -d $DB_NAME -F c -b -v \
  -f $BACKUP_DIR/backup_$TIMESTAMP.dump

# 古いバックアップを削除
find $BACKUP_DIR -name "backup_*.dump" -mtime +$RETENTION_DAYS -delete

# バックアップ成功をログに記録
echo "$(date): Backup completed - backup_$TIMESTAMP.dump" >> /var/log/db_backup.log
```

**cron設定例**（毎日午前3時に実行）:
```cron
0 3 * * * /path/to/daily_backup.sh
```

### 1.3 VACUUM/ANALYZE

#### 手動VACUUM実行

```sql
-- 通常のVACUUM（不要な行を削除）
VACUUM VERBOSE;

-- 特定テーブルのVACUUM
VACUUM VERBOSE interview_sessions;

-- VACUUM FULL（テーブル全体を再構築、ロック発生）
VACUUM FULL VERBOSE interview_sessions;

-- ANALYZE（統計情報更新）
ANALYZE;

-- VACUUM + ANALYZE
VACUUM ANALYZE;
```

#### 自動VACUUM設定確認

```sql
-- autovacuum設定確認
SHOW autovacuum;
SHOW autovacuum_max_workers;
SHOW autovacuum_naptime;

-- テーブル毎の統計情報確認
SELECT schemaname, relname, last_vacuum, last_autovacuum,
       last_analyze, last_autoanalyze
FROM pg_stat_user_tables
ORDER BY last_autovacuum NULLS FIRST;
```

#### VACUUM設定チューニング

```sql
-- postgresql.confでの推奨設定
-- autovacuum = on
-- autovacuum_max_workers = 3
-- autovacuum_naptime = 1min
-- autovacuum_vacuum_threshold = 50
-- autovacuum_analyze_threshold = 50
-- autovacuum_vacuum_scale_factor = 0.1
-- autovacuum_analyze_scale_factor = 0.05
```

### 1.4 インデックス再構築

#### インデックス状態確認

```sql
-- インデックスサイズとブロート確認
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
    idx_scan AS index_scans,
    idx_tup_read AS tuples_read,
    idx_tup_fetch AS tuples_fetched
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC;

-- 未使用インデックス検出
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexrelid::regclass::text NOT LIKE '%_pkey';
```

#### インデックス再構築

```sql
-- オンラインで再構築（ロック最小化）
REINDEX INDEX CONCURRENTLY idx_interview_sessions_user_id;

-- テーブル全体のインデックス再構築
REINDEX TABLE CONCURRENTLY interview_sessions;

-- データベース全体の再構築（メンテナンスウィンドウ時）
REINDEX DATABASE grc_db;
```

**注意事項**:
- `CONCURRENTLY`オプション使用時は、エラー時に無効なインデックスが残る可能性あり
- 本番環境では必ず`CONCURRENTLY`を使用してロックを最小化
- ディスク容量は既存インデックスの2倍以上必要

### 1.5 接続プール管理

#### asyncpgプール設定（backend/config.py）

```python
# 推奨設定
DATABASE_POOL_SIZE = 20          # 最大接続数
DATABASE_MAX_OVERFLOW = 10       # プールサイズ超過時の追加接続数
DATABASE_POOL_TIMEOUT = 30       # 接続待機タイムアウト（秒）
DATABASE_POOL_RECYCLE = 3600     # 接続再利用タイムアウト（秒）
DATABASE_ECHO = False            # SQLログ出力（開発時のみTrue）
```

#### PostgreSQL側の接続数設定

```sql
-- 現在の接続数確認
SELECT count(*) FROM pg_stat_activity;

-- データベース別の接続数
SELECT datname, count(*)
FROM pg_stat_activity
GROUP BY datname;

-- 最大接続数確認
SHOW max_connections;

-- アイドル接続の確認
SELECT pid, usename, datname, state, state_change
FROM pg_stat_activity
WHERE state = 'idle'
  AND state_change < now() - interval '5 minutes';
```

#### postgresql.conf推奨設定

```conf
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB
```

---

## 2. Redis保守

### 2.1 メモリ使用量監視

#### メモリ情報確認

```bash
# 詳細なメモリ統計
redis-cli INFO memory

# 主要メトリクス抽出
redis-cli INFO memory | grep -E "used_memory_human|used_memory_peak_human|maxmemory_human|mem_fragmentation_ratio"

# キーの統計情報
redis-cli --bigkeys

# キースペース情報
redis-cli INFO keyspace
```

#### メモリ使用量の可視化

```bash
# データベース毎のキー数とサイズ
for db in {0..15}; do
  echo "DB $db:"
  redis-cli -n $db DBSIZE
done

# 特定パターンのキーをサンプリング
redis-cli --scan --pattern 'session:*' | head -100

# キーのTTL確認
redis-cli --scan --pattern 'session:*' | xargs -I {} redis-cli TTL {}
```

### 2.2 キャッシュクリア手順

#### 安全なキャッシュクリア

```bash
# 特定パターンのキー削除
redis-cli --scan --pattern 'cache:*' | xargs redis-cli DEL

# セッションキャッシュクリア
redis-cli --scan --pattern 'session:*' | xargs redis-cli DEL

# 期限切れキーの強制削除
redis-cli --scan | xargs -I {} sh -c 'TTL=$(redis-cli TTL {}); if [ $TTL -eq -1 ]; then redis-cli DEL {}; fi'
```

#### データベース全体のクリア

```bash
# 現在のデータベースをクリア（注意: 全データ削除）
redis-cli FLUSHDB

# 全データベースをクリア（注意: 全データ削除）
redis-cli FLUSHALL

# 非同期でクリア（パフォーマンス影響を最小化）
redis-cli FLUSHDB ASYNC
redis-cli FLUSHALL ASYNC
```

**警告**: 本番環境での`FLUSHDB`/`FLUSHALL`実行前に必ず確認

### 2.3 永続化設定（RDB/AOF）

#### RDB（スナップショット）設定

```conf
# redis.conf
save 900 1      # 900秒間に1回以上の書き込みがあればスナップショット
save 300 10     # 300秒間に10回以上
save 60 10000   # 60秒間に10000回以上

stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /var/lib/redis
```

#### AOF（追記ログ）設定

```conf
# redis.conf
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec  # 推奨: 毎秒1回fsync

# AOF書き換え設定
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
```

#### 手動でのスナップショット作成

```bash
# バックグラウンドで保存
redis-cli BGSAVE

# 同期的に保存（ブロッキング）
redis-cli SAVE

# 保存状態確認
redis-cli LASTSAVE

# AOFファイルの書き換え
redis-cli BGREWRITEAOF
```

#### バックアップとリストア

```bash
# バックアップ
cp /var/lib/redis/dump.rdb /backup/redis/dump_$(date +%Y%m%d).rdb
cp /var/lib/redis/appendonly.aof /backup/redis/appendonly_$(date +%Y%m%d).aof

# リストア手順
# 1. Redisサービス停止
systemctl stop redis

# 2. バックアップファイルをリストア
cp /backup/redis/dump_20260215.rdb /var/lib/redis/dump.rdb
cp /backup/redis/appendonly_20260215.aof /var/lib/redis/appendonly.aof

# 3. 権限設定
chown redis:redis /var/lib/redis/dump.rdb
chown redis:redis /var/lib/redis/appendonly.aof

# 4. Redisサービス起動
systemctl start redis
```

### 2.4 接続数管理

#### 接続数確認

```bash
# 現在の接続数
redis-cli CLIENT LIST | wc -l

# 接続詳細
redis-cli CLIENT LIST

# 最大接続数確認
redis-cli CONFIG GET maxclients
```

#### 接続数制限設定

```conf
# redis.conf
maxclients 10000

# タイムアウト設定（秒）
timeout 300
```

#### アイドル接続の切断

```bash
# 特定の接続をキル
redis-cli CLIENT KILL <ip:port>

# アイドル時間が長い接続をキル（例: 3600秒以上）
redis-cli CLIENT LIST | grep 'idle=[3-9][0-9][0-9][0-9]' | \
  awk '{print $2}' | cut -d= -f2 | xargs -I {} redis-cli CLIENT KILL ADDR {}
```

---

## 3. アプリケーション保守

### 3.1 依存パッケージ更新

#### Frontend（pnpm）

```bash
# 現在の依存関係確認
cd apps/frontend
pnpm list --depth=0

# 更新可能なパッケージ確認
pnpm outdated

# パッチバージョン更新（安全）
pnpm update

# マイナーバージョン更新
pnpm update --latest

# 特定パッケージの更新
pnpm update react react-dom

# セキュリティ監査
pnpm audit

# セキュリティ脆弱性の自動修正
pnpm audit --fix
```

#### Backend（pip）

```bash
# 現在の依存関係確認
cd apps/backend
pip list

# 更新可能なパッケージ確認
pip list --outdated

# requirements.txtに基づいて更新
pip install --upgrade -r requirements.txt

# 特定パッケージの更新
pip install --upgrade fastapi sqlalchemy

# セキュリティチェック（pip-audit使用）
pip install pip-audit
pip-audit

# 依存関係の競合確認
pip check
```

#### Monorepo全体の更新

```bash
# ルートディレクトリから全パッケージ更新
pnpm -r update

# Turboキャッシュクリア
pnpm turbo clean

# 全パッケージの再インストール
rm -rf node_modules apps/*/node_modules
pnpm install
```

### 3.2 セキュリティパッチ適用

#### 脆弱性スキャン

```bash
# Frontend
cd apps/frontend
pnpm audit --production
npm audit --json > audit-report.json

# Backend
cd apps/backend
pip-audit --format json --output audit-report.json

# Dockerイメージスキャン
docker scan grc-backend:latest
docker scan grc-frontend:latest
```

#### Critical脆弱性の緊急対応手順

1. **影響範囲の特定**
   ```bash
   # 影響を受けるパッケージの依存関係確認
   pnpm why <vulnerable-package>
   pip show <vulnerable-package>
   ```

2. **パッチ適用**
   ```bash
   # 特定バージョンに更新
   pnpm add <package>@<safe-version>
   pip install <package>==<safe-version>
   ```

3. **動作確認**
   ```bash
   # テスト実行
   pnpm test
   pytest

   # ビルド確認
   pnpm build
   ```

4. **デプロイ**
   ```bash
   # ホットフィックスブランチ作成
   git checkout -b hotfix/security-patch-CVE-XXXX
   git add .
   git commit -m "security: fix CVE-XXXX vulnerability"
   git push origin hotfix/security-patch-CVE-XXXX
   ```

### 3.3 TypeScript/Python型チェック

#### TypeScript型チェック

```bash
cd apps/frontend

# 型チェック実行
pnpm tsc --noEmit

# 厳格モードで型チェック
pnpm tsc --noEmit --strict

# 特定ファイルの型チェック
pnpm tsc --noEmit src/components/InterviewChat.tsx

# 型エラーを監視モードで確認
pnpm tsc --noEmit --watch
```

#### Python型チェック（mypy）

```bash
cd apps/backend

# 型チェック実行
mypy src/

# 厳格モードで型チェック
mypy --strict src/

# 特定ファイルの型チェック
mypy src/grc_backend/api/routes/interview.py

# HTMLレポート生成
mypy --html-report ./mypy-report src/
```

### 3.4 Lint実行

#### Python（ruff）

```bash
cd apps/backend

# Lint実行
ruff check .

# 自動修正
ruff check --fix .

# フォーマット
ruff format .

# 設定確認
ruff check --show-settings

# 特定ルール無効化（pyproject.toml）
# [tool.ruff]
# ignore = ["E501", "F401"]
```

#### TypeScript/JavaScript（ESLint）

```bash
cd apps/frontend

# Lint実行
pnpm eslint .

# 自動修正
pnpm eslint --fix .

# 特定ファイルのみLint
pnpm eslint src/components/**/*.tsx

# キャッシュクリア
pnpm eslint --cache --cache-location .eslintcache .
```

#### Pre-commit Hooks設定

```bash
# pre-commitインストール
pip install pre-commit

# Hooks設定（.pre-commit-config.yaml）
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.11
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v9.0.0
    hooks:
      - id: eslint
        args: [--fix]
EOF

# Hooksインストール
pre-commit install

# 手動実行
pre-commit run --all-files
```

---

## 4. インフラ保守

### 4.1 Dockerイメージ更新

#### ベースイメージ更新

```dockerfile
# Backend Dockerfile
FROM python:3.11-slim-bookworm  # 定期的にタグを最新化

# Frontend Dockerfile
FROM node:20-alpine  # LTSバージョン使用
```

#### イメージのビルドとプッシュ

```bash
# イメージビルド
docker build -t grc-backend:latest -f apps/backend/Dockerfile .
docker build -t grc-frontend:latest -f apps/frontend/Dockerfile .

# イメージのタグ付け
docker tag grc-backend:latest your-registry/grc-backend:v1.2.3
docker tag grc-frontend:latest your-registry/grc-frontend:v1.2.3

# レジストリにプッシュ
docker push your-registry/grc-backend:v1.2.3
docker push your-registry/grc-frontend:v1.2.3
```

#### 未使用イメージのクリーンアップ

```bash
# 未使用イメージ削除
docker image prune -a

# 停止中のコンテナ削除
docker container prune

# 未使用ボリューム削除
docker volume prune

# システム全体のクリーンアップ
docker system prune -a --volumes
```

### 4.2 コスト最適化

#### 未使用リソースの特定

```bash
# 停止中のコンテナ確認
docker ps -a --filter "status=exited"

# 未使用ボリューム確認
docker volume ls -f dangling=true

# 未使用ネットワーク確認
docker network ls --filter "dangling=true"

# ディスク使用量確認
docker system df
docker system df -v
```

#### リソース使用量の監視

```bash
# コンテナのリソース使用状況
docker stats

# 特定コンテナの詳細
docker stats grc-backend

# メモリ制限設定（docker-compose.yml）
services:
  backend:
    mem_limit: 512m
    mem_reservation: 256m
    cpus: 0.5
```

### 4.3 SSL証明書管理

#### Let's Encrypt証明書の取得

```bash
# Certbot使用（自動更新）
certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# 証明書確認
certbot certificates

# 証明書の手動更新
certbot renew

# 自動更新設定（cron）
0 0 * * * certbot renew --quiet --post-hook "systemctl reload nginx"
```

#### 証明書の有効期限確認

```bash
# OpenSSLで確認
openssl x509 -in /etc/letsencrypt/live/your-domain.com/cert.pem -noout -dates

# 有効期限アラート（30日前）
EXPIRY=$(openssl x509 -in /etc/letsencrypt/live/your-domain.com/cert.pem -noout -enddate | cut -d= -f2)
EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s)
CURRENT_EPOCH=$(date +%s)
DAYS_LEFT=$(( ($EXPIRY_EPOCH - $CURRENT_EPOCH) / 86400 ))

if [ $DAYS_LEFT -lt 30 ]; then
  echo "Warning: SSL certificate expires in $DAYS_LEFT days"
fi
```

---

## 5. AIプロバイダー保守

### 5.1 APIバージョン更新

#### Azure OpenAI

```python
# backend/config.py
AZURE_OPENAI_API_VERSION = "2024-02-15-preview"  # 定期的に最新版に更新

# 更新時の確認事項
# 1. APIドキュメントで破壊的変更を確認
# 2. ステージング環境でテスト実行
# 3. レスポンス形式の変更を確認
```

#### AWS Bedrock

```python
# boto3バージョン更新
pip install --upgrade boto3 botocore

# モデルバージョン確認
import boto3
bedrock = boto3.client('bedrock')
response = bedrock.list_foundation_models()
```

#### GCP Vertex AI

```python
# google-cloud-aiplatformバージョン更新
pip install --upgrade google-cloud-aiplatform

# エンドポイント更新確認
from google.cloud import aiplatform
aiplatform.init(project='your-project', location='us-central1')
```

### 5.2 トークン使用量監視

#### 使用量ログの収集

```python
# backend/services/ai_service.py
import logging

logger = logging.getLogger(__name__)

async def call_ai_model(prompt: str, model: str):
    response = await client.chat.completions.create(...)

    # トークン使用量をログ記録
    logger.info(
        "AI API Call",
        extra={
            "model": model,
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    return response
```

#### ログ分析クエリ

```bash
# 日次トークン使用量集計
cat /var/log/grc/app.log | jq 'select(.message == "AI API Call") | .total_tokens' | \
  awk '{sum+=$1} END {print "Total tokens:", sum}'

# モデル別の使用量
cat /var/log/grc/app.log | jq -r 'select(.message == "AI API Call") | "\(.model) \(.total_tokens)"' | \
  awk '{arr[$1]+=$2} END {for (i in arr) print i, arr[i]}'
```

### 5.3 レート制限管理

#### レート制限設定（Redis使用）

```python
from redis import asyncio as aioredis
from fastapi import HTTPException

async def check_rate_limit(user_id: str, redis: aioredis.Redis):
    key = f"rate_limit:ai:{user_id}"
    current = await redis.get(key)

    if current and int(current) >= 100:  # 1時間あたり100リクエスト
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    pipe = redis.pipeline()
    pipe.incr(key)
    pipe.expire(key, 3600)  # 1時間
    await pipe.execute()
```

#### プロバイダー側のレート制限対応

```python
import asyncio
from tenacity import retry, wait_exponential, stop_after_attempt

@retry(
    wait=wait_exponential(multiplier=1, min=4, max=60),
    stop=stop_after_attempt(5)
)
async def call_ai_with_retry(prompt: str):
    try:
        return await ai_client.create_completion(prompt)
    except RateLimitError as e:
        logger.warning(f"Rate limit hit: {e}")
        raise
```

### 5.4 フォールバック設定

#### マルチプロバイダーフォールバック

```python
# backend/services/ai_service.py
class AIService:
    def __init__(self):
        self.providers = [
            AzureOpenAIProvider(),
            AWSBedrockProvider(),
            GCPVertexAIProvider()
        ]

    async def generate_response(self, prompt: str) -> str:
        for provider in self.providers:
            try:
                return await provider.generate(prompt)
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed: {e}")
                continue

        raise Exception("All AI providers failed")
```

---

## 6. ログ管理

### 6.1 構造化ログ（JSON形式）

#### Backend設定

```python
# backend/logging_config.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        if hasattr(record, 'extra'):
            log_data.update(record.extra)

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)

# 設定適用
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.root.addHandler(handler)
logging.root.setLevel(logging.INFO)
```

### 6.2 ログローテーション設定

#### ファイルベースのローテーション

```python
# backend/main.py
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    "/var/log/grc/app.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=10
)
```

#### logrotate設定（Linux）

```conf
# /etc/logrotate.d/grc
/var/log/grc/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    missingok
    create 0644 grc grc
    postrotate
        systemctl reload grc-backend
    endscript
}
```

### 6.3 ログ検索

#### grep検索

```bash
# エラーログ検索
grep "ERROR" /var/log/grc/app.log

# 特定ユーザーのログ
grep "user_id.*12345" /var/log/grc/app.log

# 日時範囲指定
grep "2026-02-15" /var/log/grc/app.log
```

#### jqによるJSON解析

```bash
# エラーレベルのログのみ抽出
cat /var/log/grc/app.log | jq 'select(.level == "ERROR")'

# 特定モジュールのログ
cat /var/log/grc/app.log | jq 'select(.module == "interview")'

# トップエラーメッセージ集計
cat /var/log/grc/app.log | jq -r 'select(.level == "ERROR") | .message' | \
  sort | uniq -c | sort -rn | head -10

# 時間帯別のエラー数
cat /var/log/grc/app.log | jq -r 'select(.level == "ERROR") | .timestamp' | \
  cut -d'T' -f2 | cut -d':' -f1 | sort | uniq -c
```

### 6.4 監査ログ

#### 監査ログの記録

```python
# backend/middleware/audit_log.py
from fastapi import Request
import logging

audit_logger = logging.getLogger("audit")

async def log_audit_event(
    request: Request,
    user_id: str,
    action: str,
    resource: str,
    result: str
):
    audit_logger.info(
        "Audit Event",
        extra={
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "result": result,
            "ip_address": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

#### 監査ログの検索

```bash
# ユーザーの全アクション履歴
cat /var/log/grc/audit.log | jq 'select(.user_id == "user-123")'

# 失敗した認証試行
cat /var/log/grc/audit.log | jq 'select(.action == "login" and .result == "failure")'

# リソースアクセス履歴
cat /var/log/grc/audit.log | jq 'select(.resource == "interview_session_456")'
```

---

## 7. 定期保守スケジュール

### 7.1 保守タスク一覧

| 頻度 | タスク | 担当者 | 所要時間 | 優先度 |
|------|--------|--------|----------|--------|
| **日次** | ヘルスチェック確認 | SRE | 5分 | 高 |
| 日次 | エラーログ確認 | SRE | 15分 | 高 |
| 日次 | バックアップ実行確認 | SRE | 5分 | 高 |
| 日次 | リソース使用量確認 | SRE | 10分 | 中 |
| **週次** | バックアップリストアテスト | DBA | 30分 | 高 |
| 週次 | セキュリティアラート確認 | セキュリティ | 20分 | 高 |
| 週次 | ログローテーション確認 | SRE | 10分 | 中 |
| 週次 | 未使用リソース削除 | DevOps | 15分 | 低 |
| **月次** | 依存パッケージ更新 | 開発者 | 2時間 | 高 |
| 月次 | セキュリティスキャン | セキュリティ | 1時間 | 高 |
| 月次 | パフォーマンスレビュー | SRE | 1時間 | 中 |
| 月次 | SSL証明書確認 | DevOps | 10分 | 高 |
| 月次 | データベースVACUUM | DBA | 30分 | 中 |
| **四半期** | DR訓練 | 全員 | 半日 | 高 |
| 四半期 | パフォーマンステスト | QA | 2時間 | 中 |
| 四半期 | コスト最適化レビュー | マネージャー | 1時間 | 中 |
| **年次** | セキュリティ監査 | 外部監査人 | 2日 | 高 |
| 年次 | アーキテクチャレビュー | アーキテクト | 1日 | 中 |

### 7.2 日次保守チェックリスト

```bash
#!/bin/bash
# daily_check.sh

echo "=== Daily Maintenance Check - $(date) ==="

# 1. ヘルスチェック
echo -n "Health Check: "
curl -s http://localhost:8000/health | jq -r '.status'

# 2. エラーログ確認（過去24時間）
echo "Error Count (last 24h):"
cat /var/log/grc/app.log | jq 'select(.level == "ERROR")' | wc -l

# 3. バックアップ確認
echo "Latest Backup:"
ls -lht /var/backups/postgresql/*.dump | head -1

# 4. ディスク使用量
echo "Disk Usage:"
df -h | grep -E "/$|/var"

# 5. データベース接続数
echo "DB Connections:"
psql -U grc_user -d grc_db -c "SELECT count(*) FROM pg_stat_activity;"

# 6. Redis メモリ使用量
echo "Redis Memory:"
redis-cli INFO memory | grep "used_memory_human"

echo "=== Check Complete ==="
```

### 7.3 週次保守チェックリスト

```bash
#!/bin/bash
# weekly_check.sh

echo "=== Weekly Maintenance Check - $(date) ==="

# 1. バックアップリストアテスト
echo "Testing backup restore..."
LATEST_BACKUP=$(ls -t /var/backups/postgresql/*.dump | head -1)
pg_restore --list $LATEST_BACKUP > /dev/null && echo "Backup OK" || echo "Backup FAILED"

# 2. セキュリティアラート
echo "Security Alerts:"
pnpm audit --production | grep -E "high|critical"
pip-audit | grep -E "high|critical"

# 3. 未使用Dockerリソース
echo "Unused Docker Resources:"
docker system df

# 4. ログファイルサイズ
echo "Log File Sizes:"
du -sh /var/log/grc/*.log

# 5. SSL証明書有効期限
echo "SSL Certificate Expiry:"
openssl x509 -in /etc/ssl/certs/your-domain.crt -noout -enddate

echo "=== Check Complete ==="
```

### 7.4 月次保守チェックリスト

```markdown
# 月次保守チェックリスト

## 1. 依存パッケージ更新
- [ ] Backend依存関係更新（pip update）
- [ ] Frontend依存関係更新（pnpm update）
- [ ] セキュリティ脆弱性スキャン
- [ ] テスト実行・動作確認

## 2. セキュリティ
- [ ] セキュリティパッチ適用
- [ ] アクセスログレビュー
- [ ] 異常なログインパターン確認
- [ ] API使用量の異常検知

## 3. データベース
- [ ] VACUUM実行
- [ ] インデックス使用状況確認
- [ ] スロークエリ分析
- [ ] 統計情報更新

## 4. パフォーマンス
- [ ] レスポンスタイム分析
- [ ] エラーレート確認
- [ ] リソース使用トレンド分析
- [ ] ボトルネック特定

## 5. コスト
- [ ] クラウドリソース使用量確認
- [ ] AIトークン使用量分析
- [ ] 未使用リソース削減
- [ ] コスト最適化施策実施
```

---

## 8. 障害復旧手順(DR)

### 8.1 RPO/RTO定義

| サービスレベル | RPO（目標復旧時点） | RTO（目標復旧時間） |
|---------------|-------------------|-------------------|
| 本番環境 | 1時間 | 4時間 |
| ステージング環境 | 24時間 | 8時間 |
| 開発環境 | 7日 | 24時間 |

**RPO（Recovery Point Objective）**: データ損失許容時間
**RTO（Recovery Time Objective）**: サービス停止許容時間

### 8.2 バックアップからのリストア手順

#### 完全システムリストア

```bash
#!/bin/bash
# disaster_recovery.sh

set -e

BACKUP_DATE=$1
if [ -z "$BACKUP_DATE" ]; then
  echo "Usage: $0 YYYYMMDD"
  exit 1
fi

echo "=== Starting Disaster Recovery - $(date) ==="
echo "Restoring from backup: $BACKUP_DATE"

# 1. サービス停止
echo "Stopping services..."
systemctl stop grc-backend
systemctl stop grc-frontend
systemctl stop redis

# 2. データベースリストア
echo "Restoring database..."
dropdb -U postgres grc_db
createdb -U postgres grc_db
pg_restore -U postgres -d grc_db /backup/postgresql/backup_${BACKUP_DATE}.dump

# 3. Redisリストア
echo "Restoring Redis..."
systemctl stop redis
cp /backup/redis/dump_${BACKUP_DATE}.rdb /var/lib/redis/dump.rdb
chown redis:redis /var/lib/redis/dump.rdb
systemctl start redis

# 4. アプリケーションファイルリストア（必要に応じて）
echo "Restoring application files..."
# rsync -av /backup/app/${BACKUP_DATE}/ /opt/grc/

# 5. マイグレーション実行
echo "Running migrations..."
cd /opt/grc/backend
alembic upgrade head

# 6. サービス起動
echo "Starting services..."
systemctl start redis
systemctl start grc-backend
systemctl start grc-frontend

# 7. ヘルスチェック
echo "Health check..."
sleep 10
curl -s http://localhost:8000/health | jq

echo "=== Disaster Recovery Complete - $(date) ==="
```

### 8.3 フェイルオーバー手順

#### データベースフェイルオーバー（PostgreSQL）

```bash
# 1. プライマリの状態確認
psql -U postgres -c "SELECT pg_is_in_recovery();"

# 2. スタンバイサーバーの昇格
pg_ctl promote -D /var/lib/postgresql/data

# 3. 接続文字列の更新
# backend/.env
DATABASE_URL=postgresql://user:pass@standby-server:5432/grc_db

# 4. アプリケーション再起動
systemctl restart grc-backend
```

#### Redisフェイルオーバー（Redis Sentinel使用時）

```bash
# 1. 現在のマスター確認
redis-cli -p 26379 SENTINEL get-master-addr-by-name mymaster

# 2. 手動フェイルオーバー
redis-cli -p 26379 SENTINEL failover mymaster

# 3. 新マスター確認
redis-cli -p 26379 SENTINEL get-master-addr-by-name mymaster
```

### 8.4 災害復旧訓練手順

#### 四半期DR訓練チェックリスト

```markdown
# DR訓練実施手順

## 事前準備（1週間前）
- [ ] 訓練日時の調整・通知
- [ ] 訓練環境の準備
- [ ] バックアップの最新化確認
- [ ] 参加者への手順書配布

## 訓練当日（4時間）

### フェーズ1: 障害検知（15分）
- [ ] 監視アラートの発火確認
- [ ] オンコール対応の確認
- [ ] エスカレーション手順の確認

### フェーズ2: 初動対応（30分）
- [ ] インシデント宣言
- [ ] ステークホルダー通知
- [ ] 影響範囲の特定
- [ ] 復旧戦略の決定

### フェーズ3: データリストア（1時間）
- [ ] データベースバックアップからのリストア
- [ ] Redisデータのリストア
- [ ] ファイルシステムのリストア
- [ ] データ整合性確認

### フェーズ4: サービス復旧（1時間）
- [ ] アプリケーションデプロイ
- [ ] マイグレーション実行
- [ ] サービス起動
- [ ] ヘルスチェック

### フェーズ5: 動作確認（45分）
- [ ] ログイン機能確認
- [ ] 面接セッション作成確認
- [ ] AI応答確認
- [ ] データ読み書き確認

### フェーズ6: 振り返り（30分）
- [ ] タイムライン作成
- [ ] 問題点の洗い出し
- [ ] 改善アクションの決定
- [ ] ドキュメント更新

## 訓練後（1週間以内）
- [ ] 訓練レポート作成
- [ ] 改善アクションの実施
- [ ] 手順書の更新
- [ ] 次回訓練日の設定
```

#### 訓練シナリオ例

**シナリオ1: データベース障害**
- 状況: プライマリDBサーバーのディスク障害
- 目標: スタンバイDBへのフェイルオーバー（RTO: 1時間）
- 確認項目: データ損失なし（RPO: 0）、全機能正常動作

**シナリオ2: リージョン障害**
- 状況: メインリージョン全体のネットワーク障害
- 目標: DRリージョンへの切り替え（RTO: 4時間）
- 確認項目: 1時間以内のデータ復旧（RPO: 1時間）

**シナリオ3: データ破損**
- 状況: アプリケーションバグによるデータ破損
- 目標: 特定時点へのポイントインタイムリカバリ
- 確認項目: 破損前の状態に復旧

---

## 付録

### A. トラブルシューティング

#### データベース接続エラー

```bash
# 接続確認
psql -h localhost -U grc_user -d grc_db

# 接続数確認
psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# 接続制限の一時的引き上げ
psql -U postgres -c "ALTER SYSTEM SET max_connections = 300;"
psql -U postgres -c "SELECT pg_reload_conf();"
```

#### Redis接続エラー

```bash
# Redis接続確認
redis-cli ping

# 接続数確認
redis-cli CLIENT LIST | wc -l

# メモリ不足の場合
redis-cli CONFIG SET maxmemory 2gb
redis-cli FLUSHDB  # 注意: データ削除
```

#### アプリケーション起動エラー

```bash
# ログ確認
journalctl -u grc-backend -n 100 --no-pager

# 環境変数確認
systemctl show grc-backend --property=Environment

# 手動起動でデバッグ
cd /opt/grc/backend
source venv/bin/activate
uvicorn grc_backend.main:app --reload
```

### B. 監視メトリクス

#### 推奨監視項目

| カテゴリ | メトリクス | 閾値 | アクション |
|---------|----------|------|-----------|
| API | レスポンスタイム | >2秒 | アラート |
| API | エラーレート | >5% | 緊急対応 |
| DB | 接続数 | >80% | スケールアップ |
| DB | レプリケーション遅延 | >10秒 | 調査 |
| Redis | メモリ使用率 | >90% | キャッシュクリア |
| インフラ | CPU使用率 | >80% | スケールアップ |
| インフラ | ディスク使用率 | >85% | クリーンアップ |
| AI | トークン使用量 | 予算の80% | コスト最適化 |

### C. 緊急連絡先

```markdown
# 緊急連絡先リスト

## 社内
- オンコールSRE: xxx-xxxx-xxxx
- DBA: xxx-xxxx-xxxx
- セキュリティ担当: xxx-xxxx-xxxx

## 外部ベンダー
- AWSサポート: Premium Support
- Azureサポート: Enterprise Support
- GCPサポート: Enhanced Support

## エスカレーションパス
1. オンコールSRE（即時）
2. チームリード（15分以内）
3. マネージャー（30分以内）
4. 経営層（重大インシデント時）
```

---

**文書改訂履歴**

| バージョン | 日付 | 変更内容 | 作成者 |
|-----------|------|---------|--------|
| 1.0 | 2026-02-15 | 初版作成 | システム管理チーム |

---

**本マニュアルに関する問い合わせ先**: sre-team@your-company.com
