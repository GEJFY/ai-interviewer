# AI Interview Tool - セットアップガイド

このガイドでは、開発環境のセットアップ手順を**初心者向け**に詳しく説明します。

> **学習リソース**: エンタープライズレベルの実装詳細については、[仕様書一覧](../specifications/README.md)を参照してください。

## 目次

1. [必要なソフトウェア](#1-必要なソフトウェア)
2. [リポジトリのクローン](#2-リポジトリのクローン)
3. [環境変数の設定](#3-環境変数の設定)
4. [Dockerサービスの起動](#4-dockerサービスの起動)
5. [バックエンドのセットアップ](#5-バックエンドのセットアップ)
6. [フロントエンドのセットアップ](#6-フロントエンドのセットアップ)
7. [動作確認](#7-動作確認)
8. [トラブルシューティング](#8-トラブルシューティング)
9. [セキュリティ設定](#9-セキュリティ設定)

---

## 1. 必要なソフトウェア

以下のソフトウェアをインストールしてください。

### 1.1 Docker Desktop

**Dockerとは？**: コンテナ技術を使ってアプリケーションを簡単に起動・管理できるツールです。

1. [Docker Desktop](https://www.docker.com/products/docker-desktop/) をダウンロード
2. インストーラーを実行
3. 再起動（必要な場合）
4. Docker Desktopを起動

**確認方法**:
```bash
docker --version
# 出力例: Docker version 24.0.0, build xxxxxxx
```

### 1.2 Node.js (v20以上)

**Node.jsとは？**: JavaScriptをサーバーサイドで実行するための環境です。

1. [Node.js公式サイト](https://nodejs.org/) からLTS版をダウンロード
2. インストーラーを実行

**確認方法**:
```bash
node --version
# 出力例: v20.10.0

npm --version
# 出力例: 10.2.0
```

### 1.3 pnpm (パッケージマネージャー)

**pnpmとは？**: Node.jsのパッケージを効率的に管理するツールです。

```bash
# npmを使ってpnpmをインストール
npm install -g pnpm

# 確認
pnpm --version
# 出力例: 9.14.0
```

### 1.4 Python (v3.12以上)

**Pythonとは？**: バックエンドで使用するプログラミング言語です。

1. [Python公式サイト](https://www.python.org/downloads/) からダウンロード
2. インストール時に「Add Python to PATH」にチェック
3. インストーラーを実行

**確認方法**:
```bash
python --version
# 出力例: Python 3.12.0
```

### 1.5 Git

**Gitとは？**: ソースコードのバージョン管理ツールです。

1. [Git公式サイト](https://git-scm.com/) からダウンロード
2. インストーラーを実行

**確認方法**:
```bash
git --version
# 出力例: git version 2.42.0
```

---

## 2. リポジトリのクローン

### 2.1 作業ディレクトリに移動

```bash
# Windowsの場合
cd C:\Users\あなたのユーザー名\Documents

# Mac/Linuxの場合
cd ~/Documents
```

### 2.2 リポジトリをクローン

```bash
git clone <repository-url>
cd ai-interviewer
```

### 2.3 ブランチの確認

```bash
git branch
# * main と表示されればOK
```

---

## 3. 環境変数の設定

### 3.1 環境変数ファイルの作成

```bash
# テンプレートをコピー
cp .env.example .env
```

### 3.2 .envファイルを編集

お使いのテキストエディタ（VS Code推奨）で `.env` ファイルを開きます。

```bash
# VS Codeで開く場合
code .env
```

### 3.3 必須項目の設定

以下の項目を設定してください。

```env
# =============================================================================
# 基本設定（必須）
# =============================================================================

# データベース設定（ローカル開発用はそのままでOK）
POSTGRES_USER=grc_user
POSTGRES_PASSWORD=grc_password
POSTGRES_DB=ai_interviewer

# アプリケーション設定
ENVIRONMENT=development
SECRET_KEY=your-secret-key-change-this-in-production

# =============================================================================
# AIプロバイダー設定（いずれか1つ必須）
# =============================================================================

# Azure OpenAI を使う場合
AI_PROVIDER=azure_openai
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key

# または OpenAI を直接使う場合
# AI_PROVIDER=openai
# OPENAI_API_KEY=your-api-key

# または AWS Bedrock を使う場合
# AI_PROVIDER=aws_bedrock
# AWS_ACCESS_KEY_ID=your-access-key
# AWS_SECRET_ACCESS_KEY=your-secret-key
# AWS_REGION=ap-northeast-1

# または GCP Vertex AI を使う場合
# AI_PROVIDER=gcp_vertex
# GCP_PROJECT_ID=your-project-id
# GOOGLE_APPLICATION_CREDENTIALS=./credentials/gcp-credentials.json

# =============================================================================
# 音声サービス設定（オプション）
# =============================================================================

SPEECH_PROVIDER=azure
AZURE_SPEECH_KEY=your-speech-key
AZURE_SPEECH_REGION=japaneast
```

> **重要**: APIキーは絶対にGitにコミットしないでください！

---

## 4. Dockerサービスの起動

### 4.1 Docker Desktopが起動していることを確認

タスクバー（Windows）またはメニューバー（Mac）にDockerアイコンがあり、「Docker Desktop is running」と表示されていることを確認。

### 4.2 データベースとRedisを起動

```bash
docker-compose up -d postgres redis
```

**コマンドの意味**:
- `docker-compose up`: docker-compose.ymlに定義されたサービスを起動
- `-d`: バックグラウンドで実行（デタッチモード）
- `postgres redis`: これらのサービスのみ起動

### 4.3 起動確認

```bash
docker-compose ps
```

以下のように表示されればOK:
```
NAME                    STATUS
ai-interviewer-db       Up (healthy)
ai-interviewer-redis    Up (healthy)
```

### 4.4 ログの確認（問題がある場合）

```bash
# すべてのログを表示
docker-compose logs

# 特定のサービスのログを表示
docker-compose logs postgres
docker-compose logs redis
```

---

## 5. バックエンドのセットアップ

### 5.1 バックエンドディレクトリに移動

```bash
cd apps/backend
```

### 5.2 仮想環境の作成

```bash
# Windowsの場合
python -m venv .venv
.venv\Scripts\activate

# Mac/Linuxの場合
python -m venv .venv
source .venv/bin/activate
```

**仮想環境が有効になると**、ターミナルのプロンプトに `(.venv)` と表示されます。

### 5.3 依存関係のインストール

```bash
# 開発用依存関係を含めてインストール
pip install -e ".[dev]"
```

### 5.4 データベースマイグレーション

```bash
# マイグレーションを実行
alembic upgrade head
```

**マイグレーションとは？**: データベースのテーブル構造を作成・更新する処理です。

### 5.5 バックエンドサーバーの起動

```bash
uvicorn grc_backend.main:app --reload --port 8000
```

**コマンドの意味**:
- `uvicorn`: Python製の高速Webサーバー
- `grc_backend.main:app`: 起動するアプリケーション
- `--reload`: ファイル変更時に自動再起動
- `--port 8000`: ポート8000で起動

### 5.6 動作確認

ブラウザで以下にアクセス:
- API: http://localhost:8000/api/v1/health
- APIドキュメント: http://localhost:8000/api/docs

---

## 6. フロントエンドのセットアップ

**新しいターミナルを開いて**、以下を実行してください。

### 6.1 プロジェクトルートに戻る

```bash
cd /path/to/ai-interviewer
```

### 6.2 依存関係のインストール

```bash
pnpm install
```

### 6.3 フロントエンドサーバーの起動

```bash
cd apps/web
pnpm dev
```

### 6.4 動作確認

ブラウザで http://localhost:3000 にアクセス

---

## 7. 動作確認

### 7.1 全サービスの状態確認

| サービス | URL | 状態確認 |
|---------|-----|---------|
| PostgreSQL | localhost:5432 | `docker-compose ps` で確認 |
| Redis | localhost:6379 | `docker-compose ps` で確認 |
| Backend API | http://localhost:8000/api/v1/health | ブラウザでアクセス |
| API Docs | http://localhost:8000/api/docs | ブラウザでアクセス |
| Frontend | http://localhost:3000 | ブラウザでアクセス |

### 7.2 簡単なAPIテスト

```bash
# ヘルスチェック
curl http://localhost:8000/api/v1/health

# 期待される応答
{"status":"healthy","timestamp":"2026-02-08T..."}
```

---

## 8. トラブルシューティング

### 問題: Dockerが起動しない

**原因**: Docker Desktopが実行されていない

**解決策**:
1. Docker Desktopを起動
2. 起動完了を待つ（1-2分）
3. 再度コマンドを実行

### 問題: ポートが既に使用されている

**原因**: 他のアプリケーションが同じポートを使用中

**解決策**:
```bash
# 使用中のポートを確認（Windows）
netstat -ano | findstr :8000

# 使用中のポートを確認（Mac/Linux）
lsof -i :8000

# プロセスを終了するか、別のポートを使用
uvicorn grc_backend.main:app --reload --port 8001
```

### 問題: pip install でエラー

**原因**: 仮想環境がアクティブでない

**解決策**:
```bash
# Windowsの場合
.venv\Scripts\activate

# Mac/Linuxの場合
source .venv/bin/activate

# 再度インストール
pip install -e ".[dev]"
```

### 問題: データベース接続エラー

**原因**: PostgreSQLが起動していない

**解決策**:
```bash
# Dockerサービスを再起動
docker-compose down
docker-compose up -d postgres redis

# ログを確認
docker-compose logs postgres
```

### 問題: AIプロバイダーエラー

**原因**: APIキーが設定されていない、または無効

**解決策**:
1. `.env` ファイルを確認
2. APIキーが正しく設定されているか確認
3. APIキーの有効期限を確認

---

## 9. セキュリティ設定

本番環境にデプロイする前に、以下のセキュリティ設定を必ず行ってください。

> **詳細**: [セキュリティ仕様書](../specifications/SECURITY.md)を参照

### 9.1 SECRET_KEYの生成

```bash
# Pythonで安全なシークレットキーを生成
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

生成された値を `.env` の `SECRET_KEY` に設定します。

### 9.2 CORS設定

`.env` に許可するオリジンを設定:

```env
CORS_ORIGINS=["http://localhost:3000","https://your-domain.com"]
```

### 9.3 セキュリティヘッダーの確認

本番環境では以下のヘッダーが自動的に設定されます:

| ヘッダー | 説明 |
| -------- | ---- |
| X-Content-Type-Options | MIMEタイプスニッフィング防止 |
| X-Frame-Options | クリックジャッキング防止 |
| X-XSS-Protection | XSS攻撃防止 |
| Strict-Transport-Security | HTTPS強制（本番のみ） |

### 9.4 APIキーの管理

```bash
# APIキーは絶対にコードにハードコードしない
# .envファイルは.gitignoreに含まれていることを確認
cat .gitignore | grep .env
```

---

## 次のステップ

セットアップが完了したら、以下のドキュメントを参照してください：

### 開発ガイド

- [開発ガイド](./DEVELOPMENT.md) - コーディング規約、テスト方法
- [デプロイガイド](./DEPLOYMENT.md) - 本番環境へのデプロイ方法
- [アーキテクチャ](../architecture/README.md) - システム構成の詳細

### エンタープライズ仕様書（学習用）

実装の詳細を学びたい方は、以下の仕様書を参照してください：

| 仕様書 | 内容 |
| ------ | ---- |
| [ログ管理仕様書](../specifications/LOGGING.md) | 構造化ログ、相関ID、センシティブデータマスキング |
| [エラー処理仕様書](../specifications/ERROR_HANDLING.md) | エラー階層、リトライ戦略、サーキットブレーカー |
| [セキュリティ仕様書](../specifications/SECURITY.md) | JWT認証、RBAC、OWASP対策 |
| [インフラ仕様書](../specifications/INFRASTRUCTURE.md) | Docker、CI/CD、Terraform |
| [AIプロバイダー仕様書](../specifications/AI_PROVIDERS.md) | マルチクラウドAI、音声サービス |

---

## サポート

問題が解決しない場合は、以下の情報を含めてIssueを作成してください：

1. 実行したコマンド
2. エラーメッセージ（全文）
3. OS（Windows/Mac/Linux）
4. Docker/Node.js/Pythonのバージョン
