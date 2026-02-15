# =============================================================================
# AI Interview Tool - Azure デモ環境デプロイスクリプト (PowerShell版)
# =============================================================================
# 使用方法（PowerShell ターミナルで実行）:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\scripts\deploy-azure-demo.ps1
#
# 前提条件:
#   - Azure CLI がインストール済みで az login 済み
#   - Docker がインストール済み・起動済み
#   - プロジェクトルートから実行
# =============================================================================

$ErrorActionPreference = "Stop"

# -----------------------------------------------------------------------------
# 設定
# -----------------------------------------------------------------------------
$RESOURCE_GROUP = "ai-interviewer-demo-rg"
$LOCATION = "japaneast"
$SUFFIX = (Get-Date -Format "HHmmss")
$ACR_NAME = "aiinterviewerdemo$SUFFIX"
$DB_SERVER_NAME = "ai-interviewer-demo-db-$SUFFIX"
$DB_ADMIN_USER = "aiinterviewer"
$DB_ADMIN_PASSWORD = "Demo$([guid]::NewGuid().ToString().Substring(0,12))!"
$DB_NAME = "aiinterviewer"
$REDIS_NAME = "ai-interviewer-demo-redis-$SUFFIX"
$APP_PLAN_NAME = "ai-interviewer-demo-plan"
$BACKEND_APP_NAME = "ai-interviewer-demo-api-$SUFFIX"
$FRONTEND_APP_NAME = "ai-interviewer-demo-web-$SUFFIX"
$SECRET_KEY = [guid]::NewGuid().ToString() + [guid]::NewGuid().ToString()

function Write-Step($msg) {
    Write-Host "`n========================================" -ForegroundColor Blue
    Write-Host "  $msg" -ForegroundColor Blue
    Write-Host "========================================`n" -ForegroundColor Blue
}

function Write-OK($msg)   { Write-Host "[OK]   $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "[ERR]  $msg" -ForegroundColor Red }

# -----------------------------------------------------------------------------
# Step 0: 事前チェック
# -----------------------------------------------------------------------------
Write-Step "Step 0: 事前チェック"

# Azure ログイン確認
try {
    $account = az account show --output json 2>$null | ConvertFrom-Json
    Write-OK "Azure ログイン済み: $($account.id)"
} catch {
    Write-Warn "Azure にログインしていません。ブラウザでログインしてください..."
    az login
    $account = az account show --output json | ConvertFrom-Json
    Write-OK "Azure ログイン完了: $($account.id)"
}

# Docker 確認
try {
    docker info 2>$null | Out-Null
    Write-OK "Docker: OK"
} catch {
    Write-Err "Docker が起動していません。Docker Desktop を起動してください。"
    exit 1
}

# -----------------------------------------------------------------------------
# Step 1: リソースグループ作成
# -----------------------------------------------------------------------------
Write-Step "Step 1: リソースグループ作成"

az group create `
    --name $RESOURCE_GROUP `
    --location $LOCATION `
    --tags Project=ai-interviewer Environment=demo ManagedBy=script `
    --output none

Write-OK "リソースグループ: $RESOURCE_GROUP ($LOCATION)"

# -----------------------------------------------------------------------------
# Step 2: Azure Container Registry 作成
# -----------------------------------------------------------------------------
Write-Step "Step 2: Azure Container Registry 作成"

az acr create `
    --resource-group $RESOURCE_GROUP `
    --name $ACR_NAME `
    --sku Basic `
    --admin-enabled true `
    --output none

$ACR_LOGIN_SERVER = az acr show --name $ACR_NAME --query loginServer -o tsv
Write-OK "ACR: $ACR_LOGIN_SERVER"

az acr login --name $ACR_NAME
Write-OK "ACR ログイン完了"

# -----------------------------------------------------------------------------
# Step 3: PostgreSQL Flexible Server 作成
# -----------------------------------------------------------------------------
Write-Step "Step 3: PostgreSQL Flexible Server 作成 (約5分)"

az postgres flexible-server create `
    --resource-group $RESOURCE_GROUP `
    --name $DB_SERVER_NAME `
    --location $LOCATION `
    --admin-user $DB_ADMIN_USER `
    --admin-password $DB_ADMIN_PASSWORD `
    --sku-name Standard_B1ms `
    --tier Burstable `
    --storage-size 32 `
    --version 16 `
    --public-access 0.0.0.0 `
    --yes `
    --output none

# pgvector 拡張を有効化
az postgres flexible-server parameter set `
    --resource-group $RESOURCE_GROUP `
    --server-name $DB_SERVER_NAME `
    --name azure.extensions `
    --value "vector,uuid-ossp" `
    --output none

# データベース作成
az postgres flexible-server db create `
    --resource-group $RESOURCE_GROUP `
    --server-name $DB_SERVER_NAME `
    --database-name $DB_NAME `
    --output none

$DB_HOST = "$DB_SERVER_NAME.postgres.database.azure.com"
$DATABASE_URL = "postgresql+asyncpg://${DB_ADMIN_USER}:${DB_ADMIN_PASSWORD}@${DB_HOST}:5432/${DB_NAME}?sslmode=require"
Write-OK "PostgreSQL: $DB_HOST"

# -----------------------------------------------------------------------------
# Step 4: Redis Cache 作成
# -----------------------------------------------------------------------------
Write-Step "Step 4: Redis Cache 作成 (約5分)"

az redis create `
    --resource-group $RESOURCE_GROUP `
    --name $REDIS_NAME `
    --location $LOCATION `
    --sku Basic `
    --vm-size c0 `
    --minimum-tls-version 1.2 `
    --output none

$REDIS_HOST = az redis show --resource-group $RESOURCE_GROUP --name $REDIS_NAME --query hostName -o tsv
$REDIS_KEY = az redis list-keys --resource-group $RESOURCE_GROUP --name $REDIS_NAME --query primaryKey -o tsv
$REDIS_PORT = az redis show --resource-group $RESOURCE_GROUP --name $REDIS_NAME --query sslPort -o tsv
$REDIS_URL = "rediss://:${REDIS_KEY}@${REDIS_HOST}:${REDIS_PORT}/0"
Write-OK "Redis: $REDIS_HOST"

# -----------------------------------------------------------------------------
# Step 5: Docker イメージのビルド & プッシュ
# -----------------------------------------------------------------------------
Write-Step "Step 5: Docker イメージのビルド & プッシュ (約10分)"

Write-Host "  Backend イメージをビルド中..." -ForegroundColor Gray
docker build `
    -t "${ACR_LOGIN_SERVER}/ai-interviewer-api:latest" `
    -f apps/backend/Dockerfile `
    --target production `
    .

Write-Host "  Backend イメージをプッシュ中..." -ForegroundColor Gray
docker push "${ACR_LOGIN_SERVER}/ai-interviewer-api:latest"

Write-Host "  Frontend イメージをビルド中..." -ForegroundColor Gray
docker build `
    -t "${ACR_LOGIN_SERVER}/ai-interviewer-web:latest" `
    -f apps/web/Dockerfile `
    --target production `
    --build-arg NEXT_PUBLIC_ENVIRONMENT=demo `
    .

Write-Host "  Frontend イメージをプッシュ中..." -ForegroundColor Gray
docker push "${ACR_LOGIN_SERVER}/ai-interviewer-web:latest"

Write-OK "Docker イメージのプッシュ完了"

# -----------------------------------------------------------------------------
# Step 6: App Service Plan & Web App 作成
# -----------------------------------------------------------------------------
Write-Step "Step 6: App Service 作成"

az appservice plan create `
    --resource-group $RESOURCE_GROUP `
    --name $APP_PLAN_NAME `
    --is-linux `
    --sku B2 `
    --output none

Write-OK "App Service Plan: $APP_PLAN_NAME (B2)"

# ACR 認証情報を取得
$ACR_USERNAME = az acr credential show --name $ACR_NAME --query username -o tsv
$ACR_PASSWORD = az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv

# Backend Web App
az webapp create `
    --resource-group $RESOURCE_GROUP `
    --plan $APP_PLAN_NAME `
    --name $BACKEND_APP_NAME `
    --docker-registry-server-url "https://$ACR_LOGIN_SERVER" `
    --docker-registry-server-user $ACR_USERNAME `
    --docker-registry-server-password $ACR_PASSWORD `
    --container-image-name "${ACR_LOGIN_SERVER}/ai-interviewer-api:latest" `
    --output none

$BACKEND_URL = "https://$BACKEND_APP_NAME.azurewebsites.net"
Write-OK "Backend App: $BACKEND_URL"

# Frontend Web App
az webapp create `
    --resource-group $RESOURCE_GROUP `
    --plan $APP_PLAN_NAME `
    --name $FRONTEND_APP_NAME `
    --docker-registry-server-url "https://$ACR_LOGIN_SERVER" `
    --docker-registry-server-user $ACR_USERNAME `
    --docker-registry-server-password $ACR_PASSWORD `
    --container-image-name "${ACR_LOGIN_SERVER}/ai-interviewer-web:latest" `
    --output none

$FRONTEND_URL = "https://$FRONTEND_APP_NAME.azurewebsites.net"
Write-OK "Frontend App: $FRONTEND_URL"

# -----------------------------------------------------------------------------
# Step 7: 環境変数の設定
# -----------------------------------------------------------------------------
Write-Step "Step 7: 環境変数の設定"

az webapp config appsettings set `
    --resource-group $RESOURCE_GROUP `
    --name $BACKEND_APP_NAME `
    --settings `
        ENVIRONMENT=demo `
        SECRET_KEY=$SECRET_KEY `
        DEBUG=false `
        LOG_LEVEL=INFO `
        JSON_LOGS=true `
        DATABASE_URL=$DATABASE_URL `
        REDIS_URL=$REDIS_URL `
        "CORS_ORIGINS=[`"$FRONTEND_URL`",`"http://localhost:3001`"]" `
        SEED_DEMO=true `
        AI_PROVIDER=local `
        STORAGE_PROVIDER=local `
        RATE_LIMIT_ENABLED=false `
        WEBSITES_PORT=8000 `
    --output none

Write-OK "Backend 環境変数設定完了"

az webapp config appsettings set `
    --resource-group $RESOURCE_GROUP `
    --name $FRONTEND_APP_NAME `
    --settings `
        NEXT_PUBLIC_API_URL=$BACKEND_URL `
        NEXT_PUBLIC_WS_URL="wss://$BACKEND_APP_NAME.azurewebsites.net" `
        NEXT_PUBLIC_ENVIRONMENT=demo `
        WEBSITES_PORT=3000 `
    --output none

Write-OK "Frontend 環境変数設定完了"

# -----------------------------------------------------------------------------
# Step 8: アプリの再起動 & ヘルスチェック
# -----------------------------------------------------------------------------
Write-Step "Step 8: アプリの再起動 & ヘルスチェック"

az webapp restart --resource-group $RESOURCE_GROUP --name $BACKEND_APP_NAME
az webapp restart --resource-group $RESOURCE_GROUP --name $FRONTEND_APP_NAME

Write-Host "  アプリを再起動しました。起動を待機中 (60秒)..." -ForegroundColor Gray
Start-Sleep -Seconds 60

Write-Host "  ヘルスチェック実行中..." -ForegroundColor Gray
for ($i = 1; $i -le 5; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "$BACKEND_URL/api/v1/health" -TimeoutSec 10 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-OK "Backend ヘルスチェック: OK (200)"
            break
        }
    } catch {
        Write-Warn "ヘルスチェック試行 $i/5: 起動中..."
        Start-Sleep -Seconds 30
    }
}

# -----------------------------------------------------------------------------
# Step 9: デモデータ投入
# -----------------------------------------------------------------------------
Write-Step "Step 9: デモデータ投入"

try {
    $seedResponse = Invoke-WebRequest -Uri "$BACKEND_URL/api/v1/demo/seed" -Method POST -TimeoutSec 30 -UseBasicParsing
    Write-OK "デモデータ投入成功 (HTTP $($seedResponse.StatusCode))"
} catch {
    Write-Warn "デモデータ投入: SEED_DEMO=true で起動時に自動投入される場合があります"
}

# -----------------------------------------------------------------------------
# 完了
# -----------------------------------------------------------------------------
Write-Step "デプロイ完了！"

Write-Host ""
Write-Host "  ============================================" -ForegroundColor Cyan
Write-Host "    Azure デモ環境情報" -ForegroundColor Cyan
Write-Host "  ============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Frontend URL : $FRONTEND_URL" -ForegroundColor White
Write-Host "  Backend URL  : $BACKEND_URL" -ForegroundColor White
Write-Host "  API Docs     : $BACKEND_URL/api/docs" -ForegroundColor White
Write-Host ""
Write-Host "  デモユーザー (パスワード: demo1234)" -ForegroundColor White
Write-Host "  ────────────────────────────────" -ForegroundColor Gray
Write-Host "  admin@demo.example.com       (管理者)" -ForegroundColor White
Write-Host "  manager@demo.example.com     (マネージャー)" -ForegroundColor White
Write-Host "  interviewer@demo.example.com (インタビュアー)" -ForegroundColor White
Write-Host "  viewer@demo.example.com      (閲覧者)" -ForegroundColor White
Write-Host ""
Write-Host "  リソースグループ : $RESOURCE_GROUP" -ForegroundColor Gray
Write-Host ""
Write-Host "  ============================================" -ForegroundColor Cyan
Write-Host ""

# 接続情報をファイルに保存
$infoContent = @"
# Azure デモ環境接続情報
# 作成日時: $(Get-Date)
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
"@
$infoContent | Out-File -FilePath ".azure-demo-info.txt" -Encoding UTF8

Write-OK "接続情報を .azure-demo-info.txt に保存しました"
Write-Warn "このファイルには機密情報が含まれています。Git にコミットしないでください。"

Write-Host ""
Write-Host "リソースを削除する場合:" -ForegroundColor Yellow
Write-Host "  az group delete --name $RESOURCE_GROUP --yes --no-wait" -ForegroundColor Gray
Write-Host ""
