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
7. [Ollama (ローカルLLM) のセットアップ](#7-ollama-ローカルllm-のセットアップ)
8. [動作確認](#8-動作確認)
9. [トラブルシューティング](#9-トラブルシューティング)
10. [セキュリティ設定](#10-セキュリティ設定)
11. [Docker 入門](#11-docker-入門)
12. [Git 入門](#12-git-入門)

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
AI_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key

# または AWS Bedrock を使う場合
# AI_PROVIDER=aws
# AWS_ACCESS_KEY_ID=your-access-key
# AWS_SECRET_ACCESS_KEY=your-secret-key
# AWS_REGION=ap-northeast-1

# または GCP Vertex AI を使う場合
# AI_PROVIDER=gcp
# GCP_PROJECT_ID=your-project-id
# GOOGLE_APPLICATION_CREDENTIALS=./credentials/gcp-credentials.json

# または ローカルLLM (Ollama) を使う場合
# AI_PROVIDER=local
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_MODEL=gemma3:1b

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

```bash
# Ollamaも使う場合（クラウドAPIキー不要で開発可能）
docker compose --profile local-llm up -d postgres redis ollama
```

> **ヒント**: クラウドのAPIキー（Azure OpenAI等）を持っていない場合でも、Ollamaを使えばローカル環境だけでAI機能の開発・テストが可能です。詳しくは [7. Ollama (ローカルLLM) のセットアップ](#7-ollama-ローカルllm-のセットアップ) を参照してください。

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

## 7. Ollama (ローカルLLM) のセットアップ

**Ollamaとは？**: ローカル環境でLLM（大規模言語モデル）を実行するためのツールです。クラウドのAPIキーが不要なので、無料で手軽にAI機能の開発・テストを始められます。

> **こんな方におすすめ**: Azure OpenAI / AWS Bedrock / GCP Vertex AI のAPIキーをまだ持っていない場合、まずOllamaでローカルLLMを使って開発を始めることができます。

### 7.1 Ollamaのインストール

1. [https://ollama.com/](https://ollama.com/) からインストーラーをダウンロード
2. インストーラーを実行
3. インストール完了後、確認:

```bash
ollama --version
# 出力例: ollama version 0.5.x
```

### 7.2 モデルのダウンロード

```bash
# 軽量モデル gemma3:1b をダウンロード（約1GB）
ollama pull gemma3:1b
```

> **補足**: `gemma3:1b` は軽量なモデルなので、スペックが低いPCでも動作します。より高性能なモデルを使いたい場合は `ollama pull gemma3:4b` や `ollama pull llama3.2` なども利用できます。

### 7.3 Docker経由で起動する場合

Ollamaをローカルにインストールせず、Docker経由で起動することもできます。

```bash
# Ollamaプロファイル付きでサービスを起動
docker compose --profile local-llm up -d postgres redis ollama
```

起動後、モデルをダウンロードします:

```bash
# Dockerコンテナ内でモデルをダウンロード
docker exec -it ai-interviewer-ollama ollama pull gemma3:1b
```

### 7.4 環境変数の設定

`.env` ファイルを以下のように編集します:

```env
# AIプロバイダーをローカルに変更
AI_PROVIDER=local

# Ollama設定
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:1b
```

> **Docker経由の場合**: `OLLAMA_BASE_URL` はそのまま `http://localhost:11434` でOKです（ポートマッピングにより、ホストからアクセスできます）。

### 7.5 動作確認

```bash
# OllamaのAPIが応答するか確認
curl http://localhost:11434/api/tags

# 期待される応答例（ダウンロード済みモデルの一覧が表示される）
# {"models":[{"name":"gemma3:1b","model":"gemma3:1b",...}]}
```

---

## 8. 動作確認

### 8.1 ポート番号の対応表

起動方法によってポート番号が異なります。注意してください。

| 起動方法 | Backend | Frontend |
| --------- | --------- | ---------- |
| 直接起動（uvicorn / pnpm dev） | `http://localhost:8000` | `http://localhost:3000` |
| Docker（docker-compose up） | `http://localhost:8001` | `http://localhost:3001` |

> **なぜポートが違うの？**: Docker経由で起動した場合、`docker-compose.yml` のポートマッピング設定により、ホスト側のポートが `8001`（Backend）と `3001`（Frontend）になります。直接起動の場合は、アプリケーションがそのまま `8000` / `3000` で待ち受けます。

### 8.2 全サービスの状態確認

| サービス | URL | 状態確認 |
|---------|-----|---------|
| PostgreSQL | localhost:5432 | `docker-compose ps` で確認 |
| Redis | localhost:6379 | `docker-compose ps` で確認 |
| Backend API | http://localhost:8000/api/v1/health | ブラウザでアクセス |
| API Docs | http://localhost:8000/api/docs | ブラウザでアクセス |
| Frontend | http://localhost:3000 | ブラウザでアクセス |

### 8.3 簡単なAPIテスト

```bash
# ヘルスチェック
curl http://localhost:8000/api/v1/health

# 期待される応答
{"status":"healthy","timestamp":"2026-02-08T..."}
```

### 8.4 テストの実行

セットアップが正しく完了したことを確認するために、テストを実行しましょう。

```bash
# バックエンドテスト
cd apps/backend
pytest tests/ -v --tb=short

# フロントエンドテスト
cd apps/web
pnpm test

# AIパッケージテスト
cd packages/@grc/ai
pytest tests/ -v

# Coreパッケージテスト
cd packages/@grc/core
pytest tests/ -v
```

> **注意**: Pythonのテストを実行する前に、仮想環境が有効化されていることを確認してください（プロンプトに `(.venv)` が表示されているか）。

---

## 9. トラブルシューティング

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

## 10. セキュリティ設定

本番環境にデプロイする前に、以下のセキュリティ設定を必ず行ってください。

> **詳細**: [セキュリティ仕様書](../specifications/SECURITY.md)を参照

### 10.1 SECRET_KEYの生成

```bash
# Pythonで安全なシークレットキーを生成
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

生成された値を `.env` の `SECRET_KEY` に設定します。

### 10.2 CORS設定

`.env` に許可するオリジンを設定:

```env
CORS_ORIGINS=["http://localhost:3000","https://your-domain.com"]
```

### 10.3 セキュリティヘッダーの確認

本番環境では以下のヘッダーが自動的に設定されます:

| ヘッダー | 説明 |
| -------- | ---- |
| X-Content-Type-Options | MIMEタイプスニッフィング防止 |
| X-Frame-Options | クリックジャッキング防止 |
| X-XSS-Protection | XSS攻撃防止 |
| Strict-Transport-Security | HTTPS強制（本番のみ） |

### 10.4 APIキーの管理

```bash
# APIキーは絶対にコードにハードコードしない
# .envファイルは.gitignoreに含まれていることを確認
cat .gitignore | grep .env
```

---

## 11. Docker 入門

このセクションでは、Docker初心者向けにDockerの基本概念とよく使うコマンドを解説します。

### 11.1 Dockerとは？

Dockerは、アプリケーションを**「コンテナ」という隔離された環境で実行する技術**です。

従来の開発では「自分のPCでは動くのに、他の人の環境では動かない」という問題がよく発生していました。Dockerを使うと、アプリの実行に必要な環境（OS設定、ライブラリ、ツール等）をすべてパッケージ化するため、**誰のPCでも同じ環境を再現**できます。

### 11.2 基本用語

| 用語 | 説明 | たとえ |
| ------ | ------ | -------- |
| **イメージ** | アプリの設計図。必要なソフトウェアや設定が含まれた読み取り専用のテンプレート | 料理のレシピ |
| **コンテナ** | イメージから作られた実行環境。実際にアプリが動作する場所 | レシピから作った料理 |
| **ボリューム** | コンテナが削除されてもデータを保持するための永続化領域 | 冷蔵庫（料理を保存） |
| **ネットワーク** | コンテナ同士が通信するための仮想ネットワーク | キッチン内の配膳経路 |

### 11.3 docker-compose.yml の読み方

本プロジェクトの `docker-compose.yml` には複数のサービスが定義されています。主要な設定項目を解説します。

```yaml
services:           # サービス定義（起動するコンテナの一覧）
  postgres:         # サービス名
    image: pgvector/pgvector:pg16   # 使用するイメージ
    ports:
      - "5432:5432"   # ポートマッピング（ホスト:コンテナ）
    volumes:
      - postgres_data:/var/lib/postgresql/data   # データの永続化
    healthcheck:       # ヘルスチェック（サービスが正常か定期確認）
      test: ["CMD-SHELL", "pg_isready"]
      interval: 10s
    depends_on:        # 起動順序（このサービスより先に起動するもの）
      redis:
        condition: service_healthy
    profiles:          # オプション起動（--profile指定時のみ起動）
      - local-llm
```

**各設定項目の意味**:

| 設定項目 | 説明 | 例 |
| --------- | ------ | ----- |
| `services` | 起動するサービス（コンテナ）の定義 | postgres, redis, backend |
| `image` | 使用するDockerイメージ | `redis:7-alpine` |
| `ports` | ポートマッピング（`ホスト:コンテナ` 形式） | `"8001:8000"` = ホストの8001番ポートをコンテナの8000番に接続 |
| `volumes` | データの保存先（コンテナ削除後もデータ保持） | `postgres_data:/var/lib/postgresql/data` |
| `healthcheck` | サービスの正常性チェック設定 | `pg_isready` コマンドで定期確認 |
| `depends_on` | 他のサービスへの依存関係（起動順序） | backendはpostgresとredisの後に起動 |
| `profiles` | オプションのプロファイル（`--profile` 指定時のみ起動） | ollamaサービスは `--profile local-llm` 時のみ起動 |

### 11.4 よく使うDockerコマンド

| コマンド | 説明 |
| --------- | ------ |
| `docker compose up -d` | バックグラウンドで起動 |
| `docker compose down` | 停止・コンテナ削除 |
| `docker compose ps` | 実行中のコンテナ一覧 |
| `docker compose logs -f [サービス名]` | ログをリアルタイム表示 |
| `docker compose up -d --build` | 再ビルドして起動 |
| `docker compose --profile local-llm up -d` | Ollamaプロファイル付き起動 |
| `docker exec -it [コンテナ名] bash` | コンテナ内に入る |
| `docker volume ls` | ボリューム一覧 |
| `docker system prune` | 未使用リソースの削除 |

> **`docker-compose` と `docker compose` の違い**: 旧バージョンでは `docker-compose`（ハイフンあり）、新バージョンでは `docker compose`（スペース区切り）です。どちらでも動作しますが、新しい `docker compose` の使用を推奨します。

---

## 12. Git 入門

このセクションでは、Git初心者向けに基本的な使い方を解説します。

### 12.1 Gitとは？

Gitは、**ソースコードの変更履歴を記録・管理するツール**です。

- いつ、誰が、どのファイルを、どう変更したかを記録
- 過去のバージョンにいつでも戻すことが可能
- 複数人で同じコードを安全に編集できる

### 12.2 基本用語

| 用語 | 説明 |
| ------ | ------ |
| **リポジトリ（Repository）** | プロジェクトの保管庫。コードと変更履歴がすべて含まれる |
| **コミット（Commit）** | 変更のスナップショット（記録ポイント）。「セーブポイント」のようなもの |
| **ブランチ（Branch）** | 変更の分岐。メインのコードに影響を与えずに新機能を開発できる |
| **マージ（Merge）** | 分岐したブランチを統合して、変更を取り込むこと |
| **プルリクエスト（Pull Request / PR）** | 変更のレビュー依頼。他のメンバーにコードを確認してもらう仕組み |
| **ステージング（Staging）** | コミットする前の準備段階。どの変更をコミットに含めるか選択する |

### 12.3 初期設定

Gitを初めて使う場合、ユーザー名とメールアドレスを設定します:

```bash
git config --global user.name "あなたの名前"
git config --global user.email "あなたのメール"
```

設定を確認するには:

```bash
git config --global --list
```

### 12.4 基本的な作業フロー

| ステップ | コマンド | 説明 |
| --------- | --------- | ------ |
| 1 | `git clone URL` | リポジトリをダウンロード |
| 2 | `git checkout -b feature/新機能` | 新しいブランチを作成 |
| 3 | （コーディング） | ファイルを編集 |
| 4 | `git status` | 変更されたファイルを確認 |
| 5 | `git add ファイル名` | 変更をステージング |
| 6 | `git commit -m "feat: 説明"` | 変更を記録 |
| 7 | `git push origin ブランチ名` | リモートにアップロード |
| 8 | （GitHub上でPR作成） | レビュー依頼 |

### 12.5 よく使うGitコマンド

| コマンド | 説明 |
| --------- | ------ |
| `git status` | 現在の状態を表示 |
| `git log --oneline` | コミット履歴を1行表示 |
| `git diff` | 変更内容を表示 |
| `git stash` | 変更を一時退避 |
| `git stash pop` | 退避した変更を復元 |
| `git pull origin main` | 最新の変更を取得 |
| `git branch -a` | すべてのブランチを表示 |

### 12.6 コンフリクト（衝突）の解消

複数人が同じファイルの同じ箇所を編集した場合、**コンフリクト（衝突）** が発生します。

コンフリクトが発生すると、ファイル内に以下のようなマーカーが挿入されます:

```text
<<<<<<< HEAD
あなたの変更
=======
他の人の変更
>>>>>>> feature/other
```

**解消手順**:

1. 残したい方を選ぶ（または両方を組み合わせる）
2. `<<<<<<<`, `=======`, `>>>>>>>` マーカーを削除
3. `git add` → `git commit` で解消を記録

> **ヒント**: VS Codeにはコンフリクト解消を支援するUI機能があります。マーカーの上に「Accept Current Change」「Accept Incoming Change」「Accept Both Changes」のボタンが表示されるので、クリックで選択できます。

---

## 次のステップ

セットアップが完了したら、以下のドキュメントを参照してください：

### 開発ガイド

- [開発ガイド](./DEVELOPMENT.md) - コーディング規約、テスト方法
- [デプロイガイド](./DEPLOYMENT.md) - 本番環境へのデプロイ方法
- [インフラ仕様書](../specifications/INFRASTRUCTURE.md) - システム構成の詳細

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
