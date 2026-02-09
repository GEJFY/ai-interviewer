# AI Interview Tool - デプロイガイド

このガイドでは、本番環境へのデプロイ方法を説明します。Azure、AWS、GCPの3つのクラウドプロバイダーに対応しています。

## 目次

1. [デプロイ前の準備](#1-デプロイ前の準備)
2. [Azure へのデプロイ](#2-azure-へのデプロイ)
3. [AWS へのデプロイ](#3-aws-へのデプロイ)
4. [GCP へのデプロイ](#4-gcp-へのデプロイ)
5. [CI/CDパイプライン](#5-cicdパイプライン)
6. [監視・アラート設定](#6-監視・アラート設定)
7. [トラブルシューティング](#7-トラブルシューティング)

---

## 1. デプロイ前の準備

### 1.1 必要なツール

```bash
# Terraform
terraform --version  # v1.9.0以上

# Docker
docker --version

# クラウドCLI（使用するプロバイダーのみ）
az --version         # Azure CLI
aws --version        # AWS CLI
gcloud --version     # Google Cloud SDK
```

### 1.2 環境変数の準備

本番環境用の `.env.production` を作成：

```env
# =============================================================================
# 本番環境設定
# =============================================================================

ENVIRONMENT=production
SECRET_KEY=<非常に長いランダムな文字列>
DEBUG=false
LOG_LEVEL=INFO
JSON_LOGS=true

# AI Provider
AI_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://your-prod-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=<本番用APIキー>

# Speech
SPEECH_PROVIDER=azure
AZURE_SPEECH_KEY=<本番用キー>
AZURE_SPEECH_REGION=japaneast

# Security
CORS_ORIGINS=https://your-domain.com
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=60
```

### 1.3 シークレットの管理

**重要**: 本番のシークレットはGitに絶対にコミットしないでください。

各クラウドのシークレット管理サービスを使用：
- Azure: Key Vault
- AWS: Secrets Manager
- GCP: Secret Manager

---

## 2. Azure へのデプロイ

### 2.1 前提条件

1. Azureアカウント
2. Azure CLIのインストールと認証
3. サブスクリプションID

```bash
# Azure CLIでログイン
az login

# サブスクリプションを確認
az account list --output table

# 使用するサブスクリプションを設定
az account set --subscription "サブスクリプション名"
```

### 2.2 Terraformでインフラ構築

```bash
cd infrastructure/terraform

# 初期化
terraform init

# 開発環境
terraform plan -var-file=environments/dev/terraform.tfvars
terraform apply -var-file=environments/dev/terraform.tfvars

# 本番環境
terraform plan -var-file=environments/prod/terraform.tfvars
terraform apply -var-file=environments/prod/terraform.tfvars
```

### 2.3 terraform.tfvarsの設定

`environments/prod/terraform.tfvars`:
```hcl
# クラウドプロバイダー
cloud_provider = "azure"
ai_provider    = "azure_openai"

# 環境
environment     = "prod"
resource_prefix = "ai-interviewer"
location        = "japaneast"

# アラート通知先
alert_email = "admin@your-company.com"

# タグ
tags = {
  Project     = "AI Interview Tool"
  Environment = "Production"
  Owner       = "Go Yoshizawa"
}
```

### 2.4 アプリケーションのデプロイ

```bash
# Dockerイメージをビルド＆プッシュ
az acr login --name <レジストリ名>
docker build -t <レジストリ名>.azurecr.io/ai-interviewer-backend:latest -f apps/backend/Dockerfile .
docker push <レジストリ名>.azurecr.io/ai-interviewer-backend:latest

# App Serviceを再起動
az webapp restart --name <アプリ名> --resource-group <リソースグループ名>
```

### 2.5 構成されるリソース

| リソース | 説明 |
|---------|------|
| Resource Group | リソースをまとめる論理グループ |
| Virtual Network | ネットワーク隔離 |
| PostgreSQL Flexible Server | データベース |
| Redis Cache | キャッシュ・セッション |
| Azure OpenAI Service | LLMプロバイダー |
| Speech Services | STT/TTS |
| App Service | バックエンドAPI |
| Static Web App | フロントエンド |
| Key Vault | シークレット管理 |
| Application Insights | モニタリング |

---

## 3. AWS へのデプロイ

### 3.1 前提条件

1. AWSアカウント
2. AWS CLIのインストールと認証
3. 必要なIAM権限

```bash
# AWS CLIでログイン
aws configure

# 確認
aws sts get-caller-identity
```

### 3.2 Terraformでインフラ構築

```bash
cd infrastructure/terraform

terraform init

# terraform.tfvarsを編集
# cloud_provider = "aws"

terraform plan -var-file=environments/prod/terraform.tfvars
terraform apply -var-file=environments/prod/terraform.tfvars
```

### 3.3 ECSへのデプロイ

```bash
# ECRにログイン
aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin <アカウントID>.dkr.ecr.ap-northeast-1.amazonaws.com

# イメージをビルド＆プッシュ
docker build -t ai-interviewer-backend:latest -f apps/backend/Dockerfile .
docker tag ai-interviewer-backend:latest <アカウントID>.dkr.ecr.ap-northeast-1.amazonaws.com/ai-interviewer-backend:latest
docker push <アカウントID>.dkr.ecr.ap-northeast-1.amazonaws.com/ai-interviewer-backend:latest

# ECSサービスを更新
aws ecs update-service --cluster ai-interviewer --service backend --force-new-deployment
```

### 3.4 構成されるリソース

| リソース | 説明 |
|---------|------|
| VPC | ネットワーク隔離 |
| RDS (PostgreSQL) | データベース |
| ElastiCache (Redis) | キャッシュ |
| Bedrock | LLMプロバイダー |
| Transcribe/Polly | STT/TTS |
| ECS Fargate | コンテナ実行 |
| CloudFront | CDN |
| Secrets Manager | シークレット管理 |
| CloudWatch | モニタリング |

---

## 4. GCP へのデプロイ

### 4.1 前提条件

1. GCPアカウント
2. gcloud CLIのインストールと認証
3. プロジェクトの作成

```bash
# gcloudでログイン
gcloud auth login

# プロジェクトを設定
gcloud config set project <プロジェクトID>

# 必要なAPIを有効化
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

### 4.2 Terraformでインフラ構築

```bash
cd infrastructure/terraform

terraform init

# terraform.tfvarsを編集
# cloud_provider = "gcp"

terraform plan -var-file=environments/prod/terraform.tfvars
terraform apply -var-file=environments/prod/terraform.tfvars
```

### 4.3 Cloud Runへのデプロイ

```bash
# Artifact Registryにログイン
gcloud auth configure-docker asia-northeast1-docker.pkg.dev

# イメージをビルド＆プッシュ
docker build -t asia-northeast1-docker.pkg.dev/<プロジェクトID>/ai-interviewer/backend:latest -f apps/backend/Dockerfile .
docker push asia-northeast1-docker.pkg.dev/<プロジェクトID>/ai-interviewer/backend:latest

# Cloud Runにデプロイ
gcloud run deploy ai-interviewer-backend \
  --image asia-northeast1-docker.pkg.dev/<プロジェクトID>/ai-interviewer/backend:latest \
  --region asia-northeast1 \
  --platform managed
```

### 4.4 構成されるリソース

| リソース | 説明 |
|---------|------|
| VPC | ネットワーク隔離 |
| Cloud SQL (PostgreSQL) | データベース |
| Memorystore (Redis) | キャッシュ |
| Vertex AI | LLMプロバイダー |
| Speech-to-Text/Text-to-Speech | STT/TTS |
| Cloud Run | コンテナ実行 |
| Cloud CDN | CDN |
| Secret Manager | シークレット管理 |
| Cloud Monitoring | モニタリング |

---

## 5. CI/CDパイプライン

### 5.1 GitHub Actionsの設定

リポジトリの Settings > Secrets に以下を設定：

#### Azure用
```
AZURE_CREDENTIALS: Azure Service PrincipalのJSON
AZURE_BACKEND_APP_NAME: App Service名
AZURE_STATIC_WEB_APPS_API_TOKEN: Static Web Appsのトークン
```

#### AWS用
```
AWS_ACCESS_KEY_ID: IAMアクセスキー
AWS_SECRET_ACCESS_KEY: IAMシークレットキー
AWS_REGION: ap-northeast-1
AWS_ECS_CLUSTER: クラスター名
AWS_ECS_SERVICE_BACKEND: バックエンドサービス名
AWS_ECS_SERVICE_WEB: フロントエンドサービス名
```

#### GCP用
```
GCP_SA_KEY: サービスアカウントキーのJSON
GCP_PROJECT_ID: プロジェクトID
GCP_REGION: asia-northeast1
```

### 5.2 デプロイの実行

#### 自動デプロイ
- `main` ブランチへのマージで自動デプロイ

#### 手動デプロイ
1. GitHub > Actions > Deploy Pipeline
2. "Run workflow" をクリック
3. 環境とプロバイダーを選択
4. "Run workflow" をクリック

---

## 6. 監視・アラート設定

### 6.1 監視項目

| メトリクス | 警告閾値 | 重大閾値 |
|-----------|---------|---------|
| API応答時間 | >3秒 | >5秒 |
| エラーレート | >1% | >5% |
| CPU使用率 | >70% | >90% |
| メモリ使用率 | >70% | >90% |
| DB接続数 | >80% | >95% |

### 6.2 アラート通知先

Terraformの `alert_email` 変数で設定：
```hcl
alert_email = "admin@your-company.com"
```

Slackやteamsへの通知も可能（要追加設定）

### 6.3 ログの確認

```bash
# Azure
az webapp log tail --name <アプリ名> --resource-group <リソースグループ名>

# AWS
aws logs tail /ecs/ai-interviewer --follow

# GCP
gcloud run services logs read ai-interviewer-backend --region asia-northeast1
```

---

## 7. トラブルシューティング

### 問題: デプロイが失敗する

**確認事項**:
1. シークレットが正しく設定されているか
2. 権限が不足していないか
3. リソースのクォータに達していないか

```bash
# Azure
az webapp log download --name <アプリ名> --resource-group <RG名>

# AWS
aws ecs describe-services --cluster ai-interviewer --services backend

# GCP
gcloud run services describe ai-interviewer-backend --region asia-northeast1
```

### 問題: アプリケーションが起動しない

**確認事項**:
1. 環境変数が正しいか
2. データベースに接続できるか
3. ヘルスチェックが通るか

```bash
# ヘルスチェック
curl https://your-api-domain.com/api/v1/health
```

### 問題: 高負荷・遅延

**対処**:
1. スケールアウト（インスタンス数を増加）
2. スケールアップ（インスタンスサイズを増加）
3. キャッシュの確認
4. データベースクエリの最適化

---

## ロールバック手順

問題が発生した場合のロールバック：

```bash
# Docker イメージのタグを前バージョンに戻す
# Azure
az webapp config container set --name <アプリ名> --resource-group <RG名> --docker-custom-image-name <レジストリ>/backend:v1.0.0

# AWS
aws ecs update-service --cluster ai-interviewer --service backend --task-definition backend:前バージョン

# GCP
gcloud run services update-traffic ai-interviewer-backend --to-revisions=前リビジョン=100
```

---

## 次のステップ

- [セットアップガイド](./SETUP.md) - 開発環境のセットアップ
- [開発ガイド](./DEVELOPMENT.md) - 開発ワークフロー
- [セキュリティガイド](./SECURITY.md) - セキュリティベストプラクティス
