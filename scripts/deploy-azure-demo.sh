#!/bin/bash
# =============================================================================
# AI Interview Tool - Azure デモ環境デプロイスクリプト
# =============================================================================
# 使用方法:
#   bash scripts/deploy-azure-demo.sh
#
# 前提条件:
#   - Azure CLI がインストール済みで az login 済み
#   - Docker がインストール済み
#   - プロジェクトルートから実行
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# 設定
# -----------------------------------------------------------------------------
RESOURCE_GROUP="ai-interviewer-demo-rg"
LOCATION="japaneast"
SUFFIX=$(date +%s | tail -c 7)  # ユニークなサフィックス
ACR_NAME="aiinterviewerdemo${SUFFIX}"
DB_SERVER_NAME="ai-interviewer-demo-db-${SUFFIX}"
DB_ADMIN_USER="aiinterviewer"
DB_ADMIN_PASSWORD="Demo$(openssl rand -hex 12)!"
DB_NAME="aiinterviewer"
REDIS_NAME="ai-interviewer-demo-redis-${SUFFIX}"
APP_PLAN_NAME="ai-interviewer-demo-plan"
BACKEND_APP_NAME="ai-interviewer-demo-api-${SUFFIX}"
FRONTEND_APP_NAME="ai-interviewer-demo-web-${SUFFIX}"
SECRET_KEY=$(openssl rand -hex 32)

# 色付き出力
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step()  { echo -e "\n${BLUE}========================================${NC}"; echo -e "${BLUE}  $1${NC}"; echo -e "${BLUE}========================================${NC}"; }

# -----------------------------------------------------------------------------
# Step 0: 事前チェック
# -----------------------------------------------------------------------------
log_step "Step 0: 事前チェック"

if ! command -v az &> /dev/null; then
    log_error "Azure CLI が見つかりません。インストールしてください。"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    log_error "Docker が見つかりません。インストールしてください。"
    exit 1
fi

# Azure ログイン確認
SUBSCRIPTION_ID=$(az account show --query id -o tsv 2>/dev/null || true)
if [ -z "$SUBSCRIPTION_ID" ]; then
    log_warn "Azure にログインしていません。ログインします..."
    az login
    SUBSCRIPTION_ID=$(az account show --query id -o tsv)
fi
log_info "サブスクリプション: $SUBSCRIPTION_ID"

# Docker 起動確認
if ! docker info &> /dev/null; then
    log_error "Docker が起動していません。Docker Desktop を起動してください。"
    exit 1
fi
log_info "Docker: OK"

# -----------------------------------------------------------------------------
# Step 1: リソースグループ作成
# -----------------------------------------------------------------------------
log_step "Step 1: リソースグループ作成"

az group create \
    --name "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --tags Project=ai-interviewer Environment=demo ManagedBy=script \
    --output none

log_info "リソースグループ: $RESOURCE_GROUP ($LOCATION)"

# -----------------------------------------------------------------------------
# Step 2: Azure Container Registry 作成
# -----------------------------------------------------------------------------
log_step "Step 2: Azure Container Registry 作成"

az acr create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$ACR_NAME" \
    --sku Basic \
    --admin-enabled true \
    --output none

ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --query loginServer -o tsv)
log_info "ACR: $ACR_LOGIN_SERVER"

# ACR にログイン
az acr login --name "$ACR_NAME"
log_info "ACR ログイン完了"

# -----------------------------------------------------------------------------
# Step 3: PostgreSQL Flexible Server 作成
# -----------------------------------------------------------------------------
log_step "Step 3: PostgreSQL Flexible Server 作成"

az postgres flexible-server create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$DB_SERVER_NAME" \
    --location "$LOCATION" \
    --admin-user "$DB_ADMIN_USER" \
    --admin-password "$DB_ADMIN_PASSWORD" \
    --sku-name Standard_B1ms \
    --tier Burstable \
    --storage-size 32 \
    --version 16 \
    --public-access 0.0.0.0 \
    --yes \
    --output none

# pgvector 拡張を有効化
az postgres flexible-server parameter set \
    --resource-group "$RESOURCE_GROUP" \
    --server-name "$DB_SERVER_NAME" \
    --name azure.extensions \
    --value "vector,uuid-ossp" \
    --output none

# データベース作成
az postgres flexible-server db create \
    --resource-group "$RESOURCE_GROUP" \
    --server-name "$DB_SERVER_NAME" \
    --database-name "$DB_NAME" \
    --output none

DB_HOST="${DB_SERVER_NAME}.postgres.database.azure.com"
DATABASE_URL="postgresql+asyncpg://${DB_ADMIN_USER}:${DB_ADMIN_PASSWORD}@${DB_HOST}:5432/${DB_NAME}?sslmode=require"
log_info "PostgreSQL: $DB_HOST"

# -----------------------------------------------------------------------------
# Step 4: Redis Cache 作成
# -----------------------------------------------------------------------------
log_step "Step 4: Redis Cache 作成"

az redis create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$REDIS_NAME" \
    --location "$LOCATION" \
    --sku Basic \
    --vm-size c0 \
    --minimum-tls-version 1.2 \
    --output none

REDIS_HOST=$(az redis show --resource-group "$RESOURCE_GROUP" --name "$REDIS_NAME" --query hostName -o tsv)
REDIS_KEY=$(az redis list-keys --resource-group "$RESOURCE_GROUP" --name "$REDIS_NAME" --query primaryKey -o tsv)
REDIS_PORT=$(az redis show --resource-group "$RESOURCE_GROUP" --name "$REDIS_NAME" --query sslPort -o tsv)
REDIS_URL="rediss://:${REDIS_KEY}@${REDIS_HOST}:${REDIS_PORT}/0"
log_info "Redis: $REDIS_HOST"

# -----------------------------------------------------------------------------
# Step 5: Docker イメージのビルド & プッシュ
# -----------------------------------------------------------------------------
log_step "Step 5: Docker イメージのビルド & プッシュ"

# Backend イメージ
log_info "Backend イメージをビルド中..."
docker build \
    -t "${ACR_LOGIN_SERVER}/ai-interviewer-api:latest" \
    -f apps/backend/Dockerfile \
    --target production \
    .

log_info "Backend イメージをプッシュ中..."
docker push "${ACR_LOGIN_SERVER}/ai-interviewer-api:latest"

# Frontend イメージ
log_info "Frontend イメージをビルド中..."
docker build \
    -t "${ACR_LOGIN_SERVER}/ai-interviewer-web:latest" \
    -f apps/web/Dockerfile \
    --target production \
    --build-arg NEXT_PUBLIC_ENVIRONMENT=demo \
    .

log_info "Frontend イメージをプッシュ中..."
docker push "${ACR_LOGIN_SERVER}/ai-interviewer-web:latest"

log_info "Docker イメージのプッシュ完了"

# -----------------------------------------------------------------------------
# Step 6: App Service Plan & Web App 作成
# -----------------------------------------------------------------------------
log_step "Step 6: App Service 作成"

# App Service Plan
az appservice plan create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$APP_PLAN_NAME" \
    --is-linux \
    --sku B2 \
    --output none

log_info "App Service Plan: $APP_PLAN_NAME (B2)"

# ACR 認証情報を取得
ACR_USERNAME=$(az acr credential show --name "$ACR_NAME" --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query "passwords[0].value" -o tsv)

# Backend Web App
az webapp create \
    --resource-group "$RESOURCE_GROUP" \
    --plan "$APP_PLAN_NAME" \
    --name "$BACKEND_APP_NAME" \
    --docker-registry-server-url "https://${ACR_LOGIN_SERVER}" \
    --docker-registry-server-user "$ACR_USERNAME" \
    --docker-registry-server-password "$ACR_PASSWORD" \
    --container-image-name "${ACR_LOGIN_SERVER}/ai-interviewer-api:latest" \
    --output none

BACKEND_URL="https://${BACKEND_APP_NAME}.azurewebsites.net"
log_info "Backend App: $BACKEND_URL"

# Frontend Web App
az webapp create \
    --resource-group "$RESOURCE_GROUP" \
    --plan "$APP_PLAN_NAME" \
    --name "$FRONTEND_APP_NAME" \
    --docker-registry-server-url "https://${ACR_LOGIN_SERVER}" \
    --docker-registry-server-user "$ACR_USERNAME" \
    --docker-registry-server-password "$ACR_PASSWORD" \
    --container-image-name "${ACR_LOGIN_SERVER}/ai-interviewer-web:latest" \
    --output none

FRONTEND_URL="https://${FRONTEND_APP_NAME}.azurewebsites.net"
log_info "Frontend App: $FRONTEND_URL"

# -----------------------------------------------------------------------------
# Step 7: 環境変数の設定
# -----------------------------------------------------------------------------
log_step "Step 7: 環境変数の設定"

# Backend の環境変数
az webapp config appsettings set \
    --resource-group "$RESOURCE_GROUP" \
    --name "$BACKEND_APP_NAME" \
    --settings \
        ENVIRONMENT=demo \
        SECRET_KEY="$SECRET_KEY" \
        DEBUG=false \
        LOG_LEVEL=INFO \
        JSON_LOGS=true \
        DATABASE_URL="$DATABASE_URL" \
        REDIS_URL="$REDIS_URL" \
        CORS_ORIGINS="[\"${FRONTEND_URL}\",\"http://localhost:3001\"]" \
        SEED_DEMO=true \
        AI_PROVIDER=local \
        STORAGE_PROVIDER=local \
        RATE_LIMIT_ENABLED=false \
        WEBSITES_PORT=8000 \
    --output none

log_info "Backend 環境変数設定完了"

# Frontend の環境変数
az webapp config appsettings set \
    --resource-group "$RESOURCE_GROUP" \
    --name "$FRONTEND_APP_NAME" \
    --settings \
        NEXT_PUBLIC_API_URL="$BACKEND_URL" \
        NEXT_PUBLIC_WS_URL="wss://${BACKEND_APP_NAME}.azurewebsites.net" \
        NEXT_PUBLIC_ENVIRONMENT=demo \
        WEBSITES_PORT=3000 \
    --output none

log_info "Frontend 環境変数設定完了"

# -----------------------------------------------------------------------------
# Step 8: アプリの再起動 & ヘルスチェック
# -----------------------------------------------------------------------------
log_step "Step 8: アプリの再起動 & ヘルスチェック"

az webapp restart --resource-group "$RESOURCE_GROUP" --name "$BACKEND_APP_NAME"
az webapp restart --resource-group "$RESOURCE_GROUP" --name "$FRONTEND_APP_NAME"

log_info "アプリを再起動しました。起動を待機中..."
sleep 60

# ヘルスチェック
log_info "ヘルスチェック実行中..."
HEALTH_RETRIES=5
for i in $(seq 1 $HEALTH_RETRIES); do
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "${BACKEND_URL}/api/v1/health" 2>/dev/null || echo "000")
    if [ "$HTTP_STATUS" = "200" ]; then
        log_info "Backend ヘルスチェック: OK (200)"
        break
    else
        log_warn "ヘルスチェック試行 $i/$HEALTH_RETRIES: HTTP $HTTP_STATUS (起動中...)"
        sleep 30
    fi
done

# -----------------------------------------------------------------------------
# Step 9: デモデータ投入
# -----------------------------------------------------------------------------
log_step "Step 9: デモデータ投入"

SEED_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 30 \
    -X POST "${BACKEND_URL}/api/v1/demo/seed" 2>/dev/null || echo "000")

if [ "$SEED_STATUS" = "200" ] || [ "$SEED_STATUS" = "201" ]; then
    log_info "デモデータ投入成功"
else
    log_warn "デモデータ投入ステータス: HTTP $SEED_STATUS (SEED_DEMO=true で起動時に自動投入される場合があります)"
fi

# -----------------------------------------------------------------------------
# 完了
# -----------------------------------------------------------------------------
log_step "デプロイ完了！"

echo ""
echo "============================================"
echo "  Azure デモ環境情報"
echo "============================================"
echo ""
echo "  Frontend URL : $FRONTEND_URL"
echo "  Backend URL  : $BACKEND_URL"
echo "  API Docs     : ${BACKEND_URL}/api/docs"
echo ""
echo "  デモユーザー (パスワード: demo1234)"
echo "  ─────────────────────────────────"
echo "  admin@demo.example.com      (管理者)"
echo "  manager@demo.example.com    (マネージャー)"
echo "  interviewer@demo.example.com (インタビュアー)"
echo "  viewer@demo.example.com     (閲覧者)"
echo ""
echo "  リソースグループ : $RESOURCE_GROUP"
echo "  DB ホスト        : $DB_HOST"
echo "  Redis ホスト     : $REDIS_HOST"
echo ""
echo "============================================"
echo ""

# 接続情報をファイルに保存
cat > ".azure-demo-info.txt" << DEMOEOF
# Azure デモ環境接続情報
# 作成日時: $(date)
RESOURCE_GROUP=$RESOURCE_GROUP
BACKEND_URL=$BACKEND_URL
FRONTEND_URL=$FRONTEND_URL
DB_HOST=$DB_HOST
DB_ADMIN_USER=$DB_ADMIN_USER
DB_ADMIN_PASSWORD=$DB_ADMIN_PASSWORD
DATABASE_URL=$DATABASE_URL
REDIS_HOST=$REDIS_HOST
REDIS_URL=$REDIS_URL
ACR_LOGIN_SERVER=$ACR_LOGIN_SERVER
BACKEND_APP_NAME=$BACKEND_APP_NAME
FRONTEND_APP_NAME=$FRONTEND_APP_NAME
DEMOEOF

log_info "接続情報を .azure-demo-info.txt に保存しました"
log_warn "このファイルには機密情報が含まれています。Git にコミットしないでください。"

echo ""
echo "リソースを削除する場合:"
echo "  az group delete --name $RESOURCE_GROUP --yes --no-wait"
echo ""
