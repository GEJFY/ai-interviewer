# インフラストラクチャ仕様書

## 目次

1. [はじめに](#1-はじめに)
2. [Docker](#2-docker)
3. [Docker Compose](#3-docker-compose)
4. [CI/CD パイプライン](#4-cicd-パイプライン)
5. [Terraform](#5-terraform)
6. [マルチクラウド対応](#6-マルチクラウド対応)
7. [監視とアラート](#7-監視とアラート)
8. [バックアップと復旧](#8-バックアップと復旧)
9. [スケーリング](#9-スケーリング)
10. [運用手順](#10-運用手順)

---

## 1. はじめに

### 1.1 このドキュメントの目的

本ドキュメントでは、AI Interview Toolのインフラストラクチャ設計と実装について詳細に解説します。Docker、CI/CD、Terraformを使用したエンタープライズレベルのインフラ構築方法を学習できます。

### 1.2 学習ゴール

1. マルチステージDockerビルドを設計・実装できる
2. GitHub Actions CI/CDパイプラインを構築できる
3. Terraformでマルチクラウドインフラを管理できる
4. 本番環境の監視・アラートを設定できる

### 1.3 インフラストラクチャの全体像

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         インフラストラクチャ概要                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        開発環境 (Local)                              │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │   │
│  │  │   Docker    │  │   Docker    │  │   Docker    │                  │   │
│  │  │  Compose    │  │  Compose    │  │  Compose    │                  │   │
│  │  │ (Backend)   │  │   (Web)     │  │  (DB/Redis) │                  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    │ git push                               │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      CI/CD (GitHub Actions)                          │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐             │   │
│  │  │   Lint   │→ │   Test   │→ │   Build  │→ │  Deploy  │             │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                    ┌───────────────┼───────────────┐                       │
│                    ▼               ▼               ▼                       │
│  ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐  │
│  │    Azure (本番)      │ │    AWS (本番)       │ │    GCP (本番)       │  │
│  │  ┌───────────────┐  │ │  ┌───────────────┐  │ │  ┌───────────────┐  │  │
│  │  │  App Service  │  │ │  │  ECS Fargate  │  │ │  │  Cloud Run    │  │  │
│  │  │  PostgreSQL   │  │ │  │  RDS          │  │ │  │  Cloud SQL    │  │  │
│  │  │  Redis Cache  │  │ │  │  ElastiCache  │  │ │  │  Memorystore  │  │  │
│  │  │  Key Vault    │  │ │  │  Secrets Mgr  │  │ │  │  Secret Mgr   │  │  │
│  │  └───────────────┘  │ │  └───────────────┘  │ │  └───────────────┘  │  │
│  └─────────────────────┘ └─────────────────────┘ └─────────────────────┘  │
│                                                                             │
│  管理: Terraform (Infrastructure as Code)                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Docker

### 2.1 Dockerとは

Dockerは、アプリケーションをコンテナとしてパッケージ化し、どこでも同じ環境で実行できるようにする技術です。

```
┌─────────────────────────────────────────────────────────────────┐
│                    従来 vs Docker                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  従来の環境依存問題                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ 開発者A環境  │  │ 開発者B環境  │  │ 本番環境     │          │
│  │ Python 3.11 │  │ Python 3.10 │  │ Python 3.9  │          │
│  │ lib v1.2.3  │  │ lib v1.1.0  │  │ lib v1.0.0  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│        ↓               ↓               ↓                       │
│    動作する         動作しない       動作しない                 │
│                                                                 │
│  Docker使用後                                                   │
│  ┌──────────────────────────────────────────────────────┐       │
│  │              Docker イメージ                          │       │
│  │  Python 3.12 + 全ての依存関係 + アプリケーション      │       │
│  └──────────────────────────────────────────────────────┘       │
│        ↓               ↓               ↓                       │
│    どこでも同じ動作を保証                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 マルチステージビルド

マルチステージビルドは、ビルド環境と実行環境を分離することで、最終イメージを小さく・安全に保つテクニックです。

```dockerfile
# apps/backend/Dockerfile

# =============================================================================
# Stage 1: ビルドステージ
# =============================================================================
# 大きなビルドツールを含むイメージ
# 最終イメージには含まれない
FROM python:3.12-slim as builder

# 環境変数設定
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ビルドに必要なシステム依存関係をインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 依存関係ファイルをコピー
COPY apps/backend/pyproject.toml apps/backend/
COPY packages/@grc/core/pyproject.toml packages/@grc/core/
COPY packages/@grc/ai/pyproject.toml packages/@grc/ai/

# 仮想環境を作成し、依存関係をインストール
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# pip とビルドツールを更新
RUN pip install --upgrade pip setuptools wheel

# 依存関係をインストール（キャッシュ効率化のため先に実行）
RUN pip install -e apps/backend -e packages/@grc/core -e packages/@grc/ai

# =============================================================================
# Stage 2: 開発ステージ
# =============================================================================
# ホットリロード対応の開発用イメージ
FROM python:3.12-slim as development

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ランタイム依存関係のみインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ビルドステージから仮想環境をコピー
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# ソースコードをコピー
COPY packages/@grc /app/packages/@grc
COPY apps/backend /app/apps/backend

WORKDIR /app/apps/backend

# 開発用ポート
EXPOSE 8000

# uvicorn でホットリロード有効化
CMD ["uvicorn", "grc_backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# =============================================================================
# Stage 3: 本番ステージ
# =============================================================================
# 最小限のランタイムのみを含む本番用イメージ
FROM python:3.12-slim as production

# セキュリティ: 非rootユーザーで実行
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app/packages/@grc/core/src:/app/packages/@grc/ai/src:/app/apps/backend/src"

# ランタイム依存関係のみ（ビルドツールは含まない）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# ビルドステージから仮想環境をコピー
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# ソースコードをコピー（rootユーザーで）
COPY packages/@grc /app/packages/@grc
COPY apps/backend /app/apps/backend

# 所有権を変更
RUN chown -R appuser:appgroup /app

# 非rootユーザーに切り替え
USER appuser

WORKDIR /app/apps/backend

# 本番用ポート
EXPOSE 8000

# ヘルスチェック設定
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# 本番用コマンド（ワーカー数を調整可能）
CMD ["uvicorn", "grc_backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 2.3 Dockerfile のベストプラクティス

```dockerfile
# ============================================
# 1. 軽量ベースイメージを使用
# ============================================
# ❌ フルイメージ（約 1GB）
FROM python:3.12

# ✅ slimイメージ（約 150MB）
FROM python:3.12-slim

# ✅✅ alpineイメージ（約 50MB）※互換性注意
FROM python:3.12-alpine


# ============================================
# 2. レイヤーキャッシュを活用
# ============================================
# ❌ 全ファイルを先にコピー（変更のたびに全て再ビルド）
COPY . .
RUN pip install -r requirements.txt

# ✅ 依存関係ファイルを先にコピー（キャッシュ効率化）
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .


# ============================================
# 3. 不要なファイルを含めない
# ============================================
# .dockerignore ファイルを作成
# .git
# .venv
# __pycache__
# *.pyc
# .env
# .env.*
# tests/
# docs/
# *.md


# ============================================
# 4. 単一責任のRUN命令
# ============================================
# ❌ 複数のRUN（レイヤーが増える）
RUN apt-get update
RUN apt-get install -y curl
RUN apt-get clean

# ✅ 単一のRUN（レイヤーを最小化）
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# ============================================
# 5. 非rootユーザーで実行
# ============================================
RUN useradd --create-home appuser
USER appuser


# ============================================
# 6. ヘルスチェックを設定
# ============================================
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

---

## 3. Docker Compose

### 3.1 開発環境構成

```yaml
# docker-compose.yml - 開発環境

version: "3.8"

# ============================================
# サービス定義
# ============================================
services:
  # ------------------------------------------
  # PostgreSQL データベース
  # ------------------------------------------
  postgres:
    image: postgres:16-alpine
    container_name: ai-interviewer-db
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-grc_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-grc_password}
      POSTGRES_DB: ${POSTGRES_DB:-ai_interviewer}
    ports:
      - "5432:5432"
    volumes:
      # 名前付きボリュームでデータを永続化
      - postgres_data:/var/lib/postgresql/data
      # 初期化スクリプト
      - ./infrastructure/docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-grc_user}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - backend-network

  # ------------------------------------------
  # Redis キャッシュ
  # ------------------------------------------
  redis:
    image: redis:7-alpine
    container_name: ai-interviewer-redis
    command: redis-server --appendonly yes
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - backend-network

  # ------------------------------------------
  # バックエンドAPI
  # ------------------------------------------
  backend:
    build:
      context: .
      dockerfile: apps/backend/Dockerfile
      target: development  # 開発ステージを使用
    container_name: ai-interviewer-backend
    environment:
      - ENVIRONMENT=development
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER:-grc_user}:${POSTGRES_PASSWORD:-grc_password}@postgres:5432/${POSTGRES_DB:-ai_interviewer}
      - REDIS_URL=redis://redis:6379/0
      - LOG_LEVEL=DEBUG
      - LOG_JSON_FORMAT=false
    ports:
      - "8000:8000"
    volumes:
      # ソースコードをマウント（ホットリロード用）
      - ./apps/backend/src:/app/apps/backend/src:ro
      - ./packages/@grc:/app/packages/@grc:ro
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - backend-network
      - frontend-network

  # ------------------------------------------
  # フロントエンド
  # ------------------------------------------
  web:
    build:
      context: .
      dockerfile: apps/web/Dockerfile
      target: development
    container_name: ai-interviewer-web
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_WS_URL=ws://localhost:8000
    ports:
      - "3000:3000"
    volumes:
      - ./apps/web/src:/app/apps/web/src:ro
    depends_on:
      - backend
    networks:
      - frontend-network

# ============================================
# ボリューム定義
# ============================================
volumes:
  postgres_data:
    name: ai-interviewer-postgres-data
  redis_data:
    name: ai-interviewer-redis-data

# ============================================
# ネットワーク定義
# ============================================
networks:
  backend-network:
    name: ai-interviewer-backend
  frontend-network:
    name: ai-interviewer-frontend
```

### 3.2 本番環境構成

```yaml
# docker-compose.prod.yml - 本番環境

version: "3.8"

services:
  # ------------------------------------------
  # リバースプロキシ（Traefik）
  # ------------------------------------------
  traefik:
    image: traefik:v3.0
    container_name: ai-interviewer-traefik
    command:
      # API ダッシュボード
      - "--api.dashboard=true"
      # Docker プロバイダー
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      # エントリーポイント
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      # Let's Encrypt 自動証明書
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
      - "--certificatesresolvers.letsencrypt.acme.email=${ACME_EMAIL}"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      # HTTP → HTTPS リダイレクト
      - "--entrypoints.web.http.redirections.entryPoint.to=websecure"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - traefik_certs:/letsencrypt
    networks:
      - frontend-network
    deploy:
      resources:
        limits:
          cpus: "0.5"
          memory: 256M

  # ------------------------------------------
  # バックエンドAPI（本番）
  # ------------------------------------------
  backend:
    image: ${REGISTRY}/ai-interviewer-backend:${VERSION:-latest}
    deploy:
      replicas: 3  # 複数インスタンス
      resources:
        limits:
          cpus: "2"
          memory: 2G
        reservations:
          cpus: "0.5"
          memory: 512M
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      update_config:
        parallelism: 1
        delay: 10s
        order: start-first  # ダウンタイムなしデプロイ
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
      - LOG_LEVEL=INFO
      - LOG_JSON_FORMAT=true
    labels:
      # Traefik 設定
      - "traefik.enable=true"
      - "traefik.http.routers.backend.rule=Host(`api.${DOMAIN}`)"
      - "traefik.http.routers.backend.tls.certresolver=letsencrypt"
      - "traefik.http.services.backend.loadbalancer.server.port=8000"
      # ヘルスチェック
      - "traefik.http.services.backend.loadbalancer.healthcheck.path=/api/v1/health"
      - "traefik.http.services.backend.loadbalancer.healthcheck.interval=10s"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - backend-network
      - frontend-network

  # ------------------------------------------
  # フロントエンド（本番）
  # ------------------------------------------
  web:
    image: ${REGISTRY}/ai-interviewer-web:${VERSION:-latest}
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: "1"
          memory: 1G
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.web.rule=Host(`${DOMAIN}`)"
      - "traefik.http.routers.web.tls.certresolver=letsencrypt"
      - "traefik.http.services.web.loadbalancer.server.port=3000"
    networks:
      - frontend-network

volumes:
  traefik_certs:

networks:
  backend-network:
  frontend-network:
```

### 3.3 Docker Compose コマンド

```bash
# ============================================
# 開発環境
# ============================================

# 全サービス起動
docker-compose up -d

# 特定のサービスのみ起動
docker-compose up -d postgres redis

# ログ確認（フォロー）
docker-compose logs -f backend

# サービス再ビルド
docker-compose up -d --build backend

# 全サービス停止
docker-compose down

# ボリュームも含めて削除
docker-compose down -v

# ============================================
# 本番環境
# ============================================

# 本番設定で起動
docker-compose -f docker-compose.prod.yml up -d

# スケールアウト
docker-compose -f docker-compose.prod.yml up -d --scale backend=5

# ローリングアップデート
docker-compose -f docker-compose.prod.yml up -d --no-deps backend

# ============================================
# デバッグ
# ============================================

# コンテナに入る
docker-compose exec backend bash

# サービスの状態確認
docker-compose ps

# リソース使用量確認
docker stats
```

---

## 4. CI/CD パイプライン

### 4.1 GitHub Actions 概要

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CI/CD パイプライン                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Trigger: git push / pull_request                                           │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                          CI Pipeline                                │    │
│  │                                                                      │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │    │
│  │  │   Lint   │─▶│   Test   │─▶│ Security │─▶│  Build   │            │    │
│  │  │          │  │          │  │   Scan   │  │          │            │    │
│  │  │ - ruff   │  │ - pytest │  │ - trivy  │  │ - docker │            │    │
│  │  │ - eslint │  │ - vitest │  │ - gitleak│  │ - push   │            │    │
│  │  │ - mypy   │  │ - e2e    │  │          │  │          │            │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │    │
│  │       │              │              │              │                │    │
│  │       └──────────────┴──────────────┴──────────────┘                │    │
│  │                              │                                       │    │
│  │                     全て成功した場合のみ                             │    │
│  │                              ▼                                       │    │
│  └──────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│                    main ブランチへのマージ時                                │
│                              ▼                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                          CD Pipeline                                │    │
│  │                                                                      │    │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │    │
│  │  │  Deploy to      │  │  Deploy to      │  │  Deploy to      │     │    │
│  │  │  Staging        │─▶│  Production     │─▶│  Verify         │     │    │
│  │  │                 │  │  (承認後)       │  │                 │     │    │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘     │    │
│  │                                                                      │    │
│  └──────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 CI ワークフロー詳細

```yaml
# .github/workflows/ci.yml

name: CI Pipeline

# ============================================
# トリガー設定
# ============================================
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

# ============================================
# 環境変数
# ============================================
env:
  PYTHON_VERSION: "3.12"
  NODE_VERSION: "20"
  REGISTRY: ghcr.io/${{ github.repository }}

# ============================================
# ジョブ定義
# ============================================
jobs:
  # ------------------------------------------
  # Python リント & 型チェック
  # ------------------------------------------
  lint-python:
    name: Lint Python
    runs-on: ubuntu-latest

    steps:
      # リポジトリをチェックアウト
      - name: Checkout code
        uses: actions/checkout@v4

      # Python セットアップ
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      # 依存関係キャッシュ
      - name: Cache pip packages
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/pyproject.toml') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      # リンターインストール & 実行
      - name: Install linters
        run: pip install ruff mypy

      - name: Run Ruff (lint)
        run: ruff check apps/backend/src packages/@grc

      - name: Run Ruff (format check)
        run: ruff format --check apps/backend/src packages/@grc

      - name: Run MyPy (type check)
        run: mypy apps/backend/src --ignore-missing-imports

  # ------------------------------------------
  # TypeScript リント & 型チェック
  # ------------------------------------------
  lint-typescript:
    name: Lint TypeScript
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}

      - name: Install pnpm
        uses: pnpm/action-setup@v3
        with:
          version: 9

      # pnpm キャッシュ
      - name: Get pnpm store directory
        shell: bash
        run: echo "STORE_PATH=$(pnpm store path --silent)" >> $GITHUB_ENV

      - name: Cache pnpm
        uses: actions/cache@v4
        with:
          path: ${{ env.STORE_PATH }}
          key: ${{ runner.os }}-pnpm-${{ hashFiles('**/pnpm-lock.yaml') }}

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Run ESLint
        run: pnpm lint

      - name: Run TypeScript type check
        run: pnpm type-check

  # ------------------------------------------
  # バックエンドテスト
  # ------------------------------------------
  test-backend:
    name: Test Backend
    runs-on: ubuntu-latest
    needs: lint-python

    # テスト用サービスコンテナ
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Cache pip packages
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-test-${{ hashFiles('**/pyproject.toml') }}

      - name: Install dependencies
        run: |
          pip install -e packages/@grc/core -e packages/@grc/ai
          pip install -e "apps/backend[dev]"

      - name: Run tests with coverage
        env:
          DATABASE_URL: postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0
          SECRET_KEY: test-secret-key
        run: |
          cd apps/backend
          pytest tests/ -v --cov=src/grc_backend --cov-report=xml

      - name: Upload coverage report
        uses: codecov/codecov-action@v4
        with:
          file: apps/backend/coverage.xml
          flags: backend

  # ------------------------------------------
  # フロントエンドテスト
  # ------------------------------------------
  test-frontend:
    name: Test Frontend
    runs-on: ubuntu-latest
    needs: lint-typescript

    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}

      - uses: pnpm/action-setup@v3
        with:
          version: 9

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Run unit tests
        run: pnpm --filter web test --coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: apps/web/coverage/lcov.info
          flags: frontend

  # ------------------------------------------
  # セキュリティスキャン
  # ------------------------------------------
  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      # Gitleaks でシークレット検出
      - name: Run Gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      # 依存関係の脆弱性スキャン
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: "fs"
          scan-ref: "."
          severity: "CRITICAL,HIGH"
          exit-code: "1"

  # ------------------------------------------
  # Docker イメージビルド
  # ------------------------------------------
  build-images:
    name: Build Docker Images
    runs-on: ubuntu-latest
    needs: [test-backend, test-frontend, security-scan]

    steps:
      - uses: actions/checkout@v4

      # Docker Buildx セットアップ（マルチプラットフォーム対応）
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      # コンテナレジストリへのログイン
      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      # イメージタグの生成
      - name: Generate image tags
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}
          tags: |
            type=ref,event=branch
            type=sha,prefix=
            type=raw,value=latest,enable=${{ github.ref == 'refs/heads/main' }}

      # バックエンドイメージのビルド & プッシュ
      - name: Build and push backend
        uses: docker/build-push-action@v5
        with:
          context: .
          file: apps/backend/Dockerfile
          target: production
          push: true
          tags: ${{ env.REGISTRY }}/backend:${{ steps.meta.outputs.version }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      # フロントエンドイメージのビルド & プッシュ
      - name: Build and push frontend
        uses: docker/build-push-action@v5
        with:
          context: .
          file: apps/web/Dockerfile
          target: production
          push: true
          tags: ${{ env.REGISTRY }}/web:${{ steps.meta.outputs.version }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ------------------------------------------
  # Terraform 検証
  # ------------------------------------------
  terraform-validate:
    name: Terraform Validate
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.9.0

      - name: Terraform Init
        run: terraform init -backend=false
        working-directory: infrastructure/terraform

      - name: Terraform Validate
        run: terraform validate
        working-directory: infrastructure/terraform

      - name: Terraform Format Check
        run: terraform fmt -check -recursive
        working-directory: infrastructure/terraform
```

### 4.3 CD ワークフロー

```yaml
# .github/workflows/deploy.yml

name: Deploy Pipeline

on:
  workflow_run:
    workflows: ["CI Pipeline"]
    types: [completed]
    branches: [main]

env:
  REGISTRY: ghcr.io/${{ github.repository }}

jobs:
  # ------------------------------------------
  # ステージング環境へのデプロイ
  # ------------------------------------------
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    environment: staging

    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Azure (Staging)
        if: ${{ vars.CLOUD_PROVIDER == 'azure' }}
        uses: azure/webapps-deploy@v2
        with:
          app-name: ${{ vars.AZURE_WEBAPP_NAME }}-staging
          images: ${{ env.REGISTRY }}/backend:${{ github.sha }}

      - name: Smoke test
        run: |
          sleep 30
          curl -f https://${{ vars.STAGING_URL }}/api/v1/health

  # ------------------------------------------
  # 本番環境へのデプロイ
  # ------------------------------------------
  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: deploy-staging
    environment: production  # 手動承認が必要

    steps:
      - uses: actions/checkout@v4

      # Azure へのデプロイ
      - name: Deploy to Azure
        if: ${{ vars.CLOUD_PROVIDER == 'azure' }}
        uses: azure/webapps-deploy@v2
        with:
          app-name: ${{ vars.AZURE_WEBAPP_NAME }}
          slot-name: staging
          images: ${{ env.REGISTRY }}/backend:${{ github.sha }}

      # スロットスワップ（ダウンタイムなしデプロイ）
      - name: Swap deployment slots
        if: ${{ vars.CLOUD_PROVIDER == 'azure' }}
        run: |
          az webapp deployment slot swap \
            --resource-group ${{ vars.RESOURCE_GROUP }} \
            --name ${{ vars.AZURE_WEBAPP_NAME }} \
            --slot staging \
            --target-slot production

      # AWS ECS へのデプロイ
      - name: Deploy to AWS ECS
        if: ${{ vars.CLOUD_PROVIDER == 'aws' }}
        run: |
          aws ecs update-service \
            --cluster ${{ vars.ECS_CLUSTER }} \
            --service ${{ vars.ECS_SERVICE }} \
            --force-new-deployment

      # GCP Cloud Run へのデプロイ
      - name: Deploy to GCP Cloud Run
        if: ${{ vars.CLOUD_PROVIDER == 'gcp' }}
        run: |
          gcloud run deploy ${{ vars.CLOUD_RUN_SERVICE }} \
            --image ${{ env.REGISTRY }}/backend:${{ github.sha }} \
            --region ${{ vars.GCP_REGION }} \
            --platform managed

  # ------------------------------------------
  # デプロイ検証
  # ------------------------------------------
  verify-deployment:
    name: Verify Deployment
    runs-on: ubuntu-latest
    needs: deploy-production

    steps:
      - name: Health check
        run: |
          for i in {1..10}; do
            if curl -sf https://${{ vars.PRODUCTION_URL }}/api/v1/health; then
              echo "Health check passed"
              exit 0
            fi
            echo "Attempt $i failed, retrying..."
            sleep 10
          done
          echo "Health check failed"
          exit 1

      - name: Notify success
        if: success()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "✅ Deployment successful: ${{ github.sha }}"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}

      - name: Notify failure
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "❌ Deployment failed: ${{ github.sha }}"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

---

## 5. Terraform

### 5.1 Terraform とは

Terraform は、インフラストラクチャをコード（IaC: Infrastructure as Code）として管理するツールです。

```
┌─────────────────────────────────────────────────────────────────┐
│                    Terraform のワークフロー                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. terraform init                                              │
│     ┌───────────────┐                                           │
│     │ プロバイダー   │ Azure/AWS/GCP プロバイダーを               │
│     │ ダウンロード   │ 初期化                                     │
│     └───────────────┘                                           │
│            ▼                                                    │
│  2. terraform plan                                              │
│     ┌───────────────┐                                           │
│     │ 実行計画作成   │ 現状と設定を比較し、                       │
│     │               │ 変更内容を表示                             │
│     └───────────────┘                                           │
│            ▼                                                    │
│  3. terraform apply                                             │
│     ┌───────────────┐                                           │
│     │ 変更適用      │ 計画に基づいてリソースを                   │
│     │               │ 作成/更新/削除                             │
│     └───────────────┘                                           │
│            ▼                                                    │
│  4. terraform destroy                                           │
│     ┌───────────────┐                                           │
│     │ リソース削除   │ 全リソースを削除                          │
│     └───────────────┘                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 ディレクトリ構造

```
infrastructure/terraform/
├── main.tf                 # メインエントリポイント
├── variables.tf            # 変数定義
├── outputs.tf              # 出力定義
├── versions.tf             # プロバイダーバージョン
│
├── modules/                # 再利用可能なモジュール
│   ├── azure/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── aws/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── gcp/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
│
└── environments/           # 環境別設定
    ├── dev/
    │   └── terraform.tfvars
    ├── staging/
    │   └── terraform.tfvars
    └── prod/
        └── terraform.tfvars
```

### 5.3 メイン設定ファイル

```hcl
# infrastructure/terraform/main.tf

# ============================================
# Terraform 設定
# ============================================
terraform {
  required_version = ">= 1.9.0"

  # リモートバックエンド（状態ファイルの保存先）
  backend "azurerm" {
    resource_group_name  = "terraform-state-rg"
    storage_account_name = "tfstateai"
    container_name       = "tfstate"
    key                  = "ai-interviewer.tfstate"
  }

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# ============================================
# 変数
# ============================================
variable "cloud_provider" {
  description = "使用するクラウドプロバイダー (azure/aws/gcp)"
  type        = string
  default     = "azure"
}

variable "environment" {
  description = "環境 (dev/staging/prod)"
  type        = string
}

variable "resource_prefix" {
  description = "リソース名のプレフィックス"
  type        = string
  default     = "ai-interviewer"
}

variable "location" {
  description = "デプロイ先リージョン"
  type        = string
  default     = "japaneast"
}

variable "alert_email" {
  description = "アラート通知先メールアドレス"
  type        = string
}

variable "tags" {
  description = "リソースタグ"
  type        = map(string)
  default     = {}
}

# ============================================
# ローカル変数
# ============================================
locals {
  # 共通タグ
  common_tags = merge(
    var.tags,
    {
      Environment = var.environment
      ManagedBy   = "terraform"
      Project     = "ai-interviewer"
    }
  )

  # リソース名
  name_prefix = "${var.resource_prefix}-${var.environment}"
}

# ============================================
# クラウドプロバイダー別モジュール呼び出し
# ============================================

# Azure
module "azure" {
  source = "./modules/azure"
  count  = var.cloud_provider == "azure" ? 1 : 0

  environment     = var.environment
  location        = var.location
  resource_prefix = local.name_prefix
  alert_email     = var.alert_email
  tags            = local.common_tags
}

# AWS
module "aws" {
  source = "./modules/aws"
  count  = var.cloud_provider == "aws" ? 1 : 0

  environment     = var.environment
  region          = var.location
  resource_prefix = local.name_prefix
  alert_email     = var.alert_email
  tags            = local.common_tags
}

# GCP
module "gcp" {
  source = "./modules/gcp"
  count  = var.cloud_provider == "gcp" ? 1 : 0

  environment     = var.environment
  region          = var.location
  resource_prefix = local.name_prefix
  alert_email     = var.alert_email
}

# ============================================
# 出力
# ============================================
output "api_endpoint" {
  description = "API エンドポイント URL"
  value = var.cloud_provider == "azure" ? (
    length(module.azure) > 0 ? module.azure[0].api_endpoint : null
  ) : var.cloud_provider == "aws" ? (
    length(module.aws) > 0 ? module.aws[0].api_endpoint : null
  ) : (
    length(module.gcp) > 0 ? module.gcp[0].api_endpoint : null
  )
}
```

### 5.4 Azure モジュール

```hcl
# infrastructure/terraform/modules/azure/main.tf

# ============================================
# 変数定義
# ============================================
variable "environment" {
  type = string
}

variable "location" {
  type    = string
  default = "japaneast"
}

variable "resource_prefix" {
  type = string
}

variable "alert_email" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}

# ============================================
# プロバイダー設定
# ============================================
provider "azurerm" {
  features {}
}

# ============================================
# リソースグループ
# ============================================
resource "azurerm_resource_group" "main" {
  name     = "${var.resource_prefix}-rg"
  location = var.location
  tags     = var.tags
}

# ============================================
# 仮想ネットワーク
# ============================================
resource "azurerm_virtual_network" "main" {
  name                = "${var.resource_prefix}-vnet"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  address_space       = ["10.0.0.0/16"]
  tags                = var.tags
}

# サブネット
resource "azurerm_subnet" "app" {
  name                 = "app-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.1.0/24"]

  delegation {
    name = "app-service-delegation"
    service_delegation {
      name = "Microsoft.Web/serverFarms"
    }
  }
}

resource "azurerm_subnet" "db" {
  name                 = "db-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.2.0/24"]

  delegation {
    name = "postgres-delegation"
    service_delegation {
      name = "Microsoft.DBforPostgreSQL/flexibleServers"
    }
  }
}

# ============================================
# PostgreSQL Flexible Server
# ============================================
resource "azurerm_postgresql_flexible_server" "main" {
  name                   = "${var.resource_prefix}-postgres"
  resource_group_name    = azurerm_resource_group.main.name
  location               = azurerm_resource_group.main.location
  version                = "16"
  delegated_subnet_id    = azurerm_subnet.db.id
  private_dns_zone_id    = azurerm_private_dns_zone.postgres.id
  administrator_login    = "adminuser"
  administrator_password = random_password.postgres.result
  zone                   = "1"

  storage_mb = 32768  # 32GB

  sku_name = var.environment == "prod" ? "GP_Standard_D4s_v3" : "B_Standard_B2s"

  tags = var.tags

  depends_on = [azurerm_private_dns_zone_virtual_network_link.postgres]
}

resource "random_password" "postgres" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# PostgreSQL プライベートDNSゾーン
resource "azurerm_private_dns_zone" "postgres" {
  name                = "${var.resource_prefix}.postgres.database.azure.com"
  resource_group_name = azurerm_resource_group.main.name
}

resource "azurerm_private_dns_zone_virtual_network_link" "postgres" {
  name                  = "postgres-vnet-link"
  private_dns_zone_name = azurerm_private_dns_zone.postgres.name
  virtual_network_id    = azurerm_virtual_network.main.id
  resource_group_name   = azurerm_resource_group.main.name
}

# ============================================
# Redis Cache
# ============================================
resource "azurerm_redis_cache" "main" {
  name                = "${var.resource_prefix}-redis"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  capacity            = var.environment == "prod" ? 2 : 0
  family              = var.environment == "prod" ? "C" : "C"
  sku_name            = var.environment == "prod" ? "Standard" : "Basic"

  redis_configuration {
    maxmemory_policy = "volatile-lru"
  }

  tags = var.tags
}

# ============================================
# App Service Plan
# ============================================
resource "azurerm_service_plan" "main" {
  name                = "${var.resource_prefix}-plan"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = var.environment == "prod" ? "P2v3" : "B2"

  tags = var.tags
}

# ============================================
# App Service (Backend API)
# ============================================
resource "azurerm_linux_web_app" "backend" {
  name                = "${var.resource_prefix}-api"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  service_plan_id     = azurerm_service_plan.main.id

  site_config {
    always_on = var.environment == "prod"

    application_stack {
      docker_image_name        = "ai-interviewer-backend:latest"
      docker_registry_url      = "https://ghcr.io"
      docker_registry_username = var.docker_username
      docker_registry_password = var.docker_password
    }

    health_check_path = "/api/v1/health"
  }

  app_settings = {
    ENVIRONMENT                = var.environment
    DATABASE_URL               = "postgresql+asyncpg://${azurerm_postgresql_flexible_server.main.administrator_login}:${random_password.postgres.result}@${azurerm_postgresql_flexible_server.main.fqdn}:5432/ai_interviewer"
    REDIS_URL                  = "rediss://:${azurerm_redis_cache.main.primary_access_key}@${azurerm_redis_cache.main.hostname}:6380/0"
    SECRET_KEY                 = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.secret_key.id})"
    DOCKER_REGISTRY_SERVER_URL = "https://ghcr.io"
  }

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

# ============================================
# Key Vault
# ============================================
resource "azurerm_key_vault" "main" {
  name                = "${var.resource_prefix}-kv"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  soft_delete_retention_days = 7

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    secret_permissions = ["Get", "List", "Set", "Delete", "Purge"]
  }

  tags = var.tags
}

data "azurerm_client_config" "current" {}

resource "azurerm_key_vault_secret" "secret_key" {
  name         = "secret-key"
  value        = random_password.secret_key.result
  key_vault_id = azurerm_key_vault.main.id
}

resource "random_password" "secret_key" {
  length  = 64
  special = false
}

# ============================================
# 監視・アラート
# ============================================
resource "azurerm_application_insights" "main" {
  name                = "${var.resource_prefix}-insights"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  application_type    = "web"

  tags = var.tags
}

resource "azurerm_monitor_action_group" "main" {
  name                = "${var.resource_prefix}-alerts"
  resource_group_name = azurerm_resource_group.main.name
  short_name          = "aiinterview"

  email_receiver {
    name          = "admin"
    email_address = var.alert_email
  }
}

# API ヘルスアラート
resource "azurerm_monitor_metric_alert" "api_health" {
  name                = "${var.resource_prefix}-api-health"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_linux_web_app.backend.id]
  description         = "API が応答しない場合にアラート"

  criteria {
    metric_namespace = "Microsoft.Web/sites"
    metric_name      = "HealthCheckStatus"
    aggregation      = "Average"
    operator         = "LessThan"
    threshold        = 100
  }

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }
}

# 応答時間アラート
resource "azurerm_monitor_metric_alert" "response_time" {
  name                = "${var.resource_prefix}-response-time"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_linux_web_app.backend.id]
  description         = "応答時間が5秒を超えた場合にアラート"

  criteria {
    metric_namespace = "Microsoft.Web/sites"
    metric_name      = "HttpResponseTime"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 5
  }

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }
}

# ============================================
# 出力
# ============================================
output "api_endpoint" {
  value = "https://${azurerm_linux_web_app.backend.default_hostname}"
}

output "key_vault_uri" {
  value = azurerm_key_vault.main.vault_uri
}
```

### 5.5 Terraform コマンド

```bash
# ============================================
# 基本操作
# ============================================

# 初期化（プロバイダーのダウンロード）
cd infrastructure/terraform
terraform init

# 設定の検証
terraform validate

# フォーマット
terraform fmt -recursive

# 実行計画の確認
terraform plan -var-file=environments/dev/terraform.tfvars

# 変更の適用
terraform apply -var-file=environments/dev/terraform.tfvars

# リソースの削除（注意！）
terraform destroy -var-file=environments/dev/terraform.tfvars

# ============================================
# 本番環境
# ============================================

# 本番環境のプラン
terraform plan -var-file=environments/prod/terraform.tfvars -out=prod.tfplan

# プランのレビュー後に適用
terraform apply prod.tfplan

# ============================================
# 状態管理
# ============================================

# 状態の確認
terraform state list

# 特定リソースの状態
terraform state show azurerm_linux_web_app.backend

# リソースのインポート（既存リソースを管理下に）
terraform import azurerm_resource_group.main /subscriptions/.../resourceGroups/my-rg
```

---

## 6. マルチクラウド対応

### 6.1 プロバイダー別の対応表

| 機能 | Azure | AWS | GCP |
|------|-------|-----|-----|
| コンテナ実行 | App Service | ECS Fargate | Cloud Run |
| データベース | PostgreSQL Flexible Server | RDS | Cloud SQL |
| キャッシュ | Redis Cache | ElastiCache | Memorystore |
| シークレット | Key Vault | Secrets Manager | Secret Manager |
| ストレージ | Blob Storage | S3 | Cloud Storage |
| 監視 | Azure Monitor | CloudWatch | Cloud Monitoring |

### 6.2 環境変数による切り替え

```bash
# environments/prod/terraform.tfvars

# クラウドプロバイダー選択
cloud_provider = "azure"  # または "aws" / "gcp"

# 共通設定
environment     = "prod"
resource_prefix = "ai-interviewer"
alert_email     = "admin@example.com"

# Azure固有設定
location = "japaneast"

# または AWS固有設定
# region = "ap-northeast-1"

# または GCP固有設定
# project_id = "my-gcp-project"
# region = "asia-northeast1"
```

---

## 7. 監視とアラート

### 7.1 監視項目

| カテゴリ | メトリクス | 警告閾値 | 重大閾値 |
|---------|-----------|---------|---------|
| 可用性 | ヘルスチェック | 95%以下 | 90%以下 |
| パフォーマンス | 応答時間 | 3秒超 | 5秒超 |
| パフォーマンス | エラーレート | 1%超 | 5%超 |
| リソース | CPU使用率 | 70%超 | 90%超 |
| リソース | メモリ使用率 | 70%超 | 90%超 |
| データベース | 接続数 | 80%超 | 95%超 |
| データベース | クエリ遅延 | 1秒超 | 5秒超 |

### 7.2 アラート設定例

```hcl
# Azure Monitor アラート

# CPU使用率アラート
resource "azurerm_monitor_metric_alert" "cpu_high" {
  name                = "${var.resource_prefix}-cpu-high"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_service_plan.main.id]
  description         = "CPU使用率が70%を超えた場合"
  severity            = 2  # Warning

  criteria {
    metric_namespace = "Microsoft.Web/serverfarms"
    metric_name      = "CpuPercentage"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 70
  }

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }
}

# メモリ使用率アラート
resource "azurerm_monitor_metric_alert" "memory_high" {
  name                = "${var.resource_prefix}-memory-high"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_service_plan.main.id]
  description         = "メモリ使用率が70%を超えた場合"
  severity            = 2

  criteria {
    metric_namespace = "Microsoft.Web/serverfarms"
    metric_name      = "MemoryPercentage"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 70
  }

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }
}

# エラーレートアラート
resource "azurerm_monitor_metric_alert" "error_rate" {
  name                = "${var.resource_prefix}-error-rate"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_linux_web_app.backend.id]
  description         = "5xxエラーが発生した場合"
  severity            = 1  # Critical

  criteria {
    metric_namespace = "Microsoft.Web/sites"
    metric_name      = "Http5xx"
    aggregation      = "Total"
    operator         = "GreaterThan"
    threshold        = 10
  }

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }
}
```

---

## 8. バックアップと復旧

### 8.1 バックアップ戦略

```
┌─────────────────────────────────────────────────────────────────┐
│                    バックアップ戦略                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  データベース                                                   │
│  ├── 自動バックアップ: 毎日                                     │
│  ├── 保持期間: 35日（本番）、7日（開発）                         │
│  ├── ポイントインタイムリカバリ: 有効                           │
│  └── 地理冗長: 本番のみ有効                                     │
│                                                                 │
│  ストレージ（音声ファイル等）                                   │
│  ├── バージョニング: 有効                                       │
│  ├── ソフトデリート: 30日                                       │
│  └── 地理冗長: 本番のみ有効                                     │
│                                                                 │
│  設定・シークレット                                             │
│  ├── Terraform 状態: リモートバックエンド                       │
│  └── Key Vault: ソフトデリート有効                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 復旧手順

```bash
# ============================================
# データベース復旧
# ============================================

# Azure PostgreSQL のポイントインタイムリストア
az postgres flexible-server restore \
  --resource-group my-rg \
  --name my-postgres-restored \
  --source-server my-postgres \
  --restore-time "2026-02-08T10:00:00Z"

# ============================================
# インフラ復旧
# ============================================

# Terraform 状態から再構築
terraform apply -var-file=environments/prod/terraform.tfvars
```

---

## 9. スケーリング

### 9.1 水平スケーリング

```hcl
# Azure App Service 自動スケール
resource "azurerm_monitor_autoscale_setting" "main" {
  name                = "${var.resource_prefix}-autoscale"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  target_resource_id  = azurerm_service_plan.main.id

  profile {
    name = "default"

    capacity {
      default = 2
      minimum = 1
      maximum = 10
    }

    # スケールアウト: CPU 70%超で1インスタンス追加
    rule {
      metric_trigger {
        metric_name        = "CpuPercentage"
        metric_resource_id = azurerm_service_plan.main.id
        time_grain         = "PT1M"
        statistic          = "Average"
        time_window        = "PT5M"
        time_aggregation   = "Average"
        operator           = "GreaterThan"
        threshold          = 70
      }

      scale_action {
        direction = "Increase"
        type      = "ChangeCount"
        value     = "1"
        cooldown  = "PT5M"
      }
    }

    # スケールイン: CPU 30%未満で1インスタンス削減
    rule {
      metric_trigger {
        metric_name        = "CpuPercentage"
        metric_resource_id = azurerm_service_plan.main.id
        time_grain         = "PT1M"
        statistic          = "Average"
        time_window        = "PT5M"
        time_aggregation   = "Average"
        operator           = "LessThan"
        threshold          = 30
      }

      scale_action {
        direction = "Decrease"
        type      = "ChangeCount"
        value     = "1"
        cooldown  = "PT5M"
      }
    }
  }
}
```

---

## 10. 運用手順

### 10.1 日次運用チェックリスト

```markdown
## 日次運用チェックリスト

### モニタリング確認
- [ ] ダッシュボードでエラーレートを確認
- [ ] 応答時間の異常がないか確認
- [ ] リソース使用率を確認

### ログ確認
- [ ] エラーログの確認
- [ ] セキュリティアラートの確認

### バックアップ確認
- [ ] 自動バックアップの成功を確認
```

### 10.2 障害対応フロー

```
┌─────────────────────────────────────────────────────────────────┐
│                    障害対応フロー                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 検知                                                        │
│     └─▶ アラート受信 / ユーザー報告                             │
│                                                                 │
│  2. 初期対応（15分以内）                                        │
│     ├─▶ 影響範囲の確認                                          │
│     ├─▶ 関係者への連絡                                          │
│     └─▶ 一時対応（スケールアウト、ロールバック等）              │
│                                                                 │
│  3. 原因調査                                                    │
│     ├─▶ ログの確認                                              │
│     ├─▶ メトリクスの確認                                        │
│     └─▶ 直近の変更の確認                                        │
│                                                                 │
│  4. 恒久対応                                                    │
│     ├─▶ 修正の実施                                              │
│     ├─▶ テスト                                                  │
│     └─▶ デプロイ                                                │
│                                                                 │
│  5. 事後対応                                                    │
│     ├─▶ 障害報告書の作成                                        │
│     └─▶ 再発防止策の検討                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 付録

### A. よく使うコマンド

```bash
# Docker
docker-compose up -d            # 開発環境起動
docker-compose logs -f backend  # ログ確認
docker-compose down             # 停止

# Terraform
terraform plan                  # プラン確認
terraform apply                 # 適用
terraform destroy               # 削除

# GitHub Actions
gh workflow run ci.yml          # ワークフロー手動実行
gh run list                     # 実行一覧
gh run view                     # 実行詳細
```

### B. 関連ドキュメント

- [ログ管理仕様書](./LOGGING.md)
- [エラー処理仕様書](./ERROR_HANDLING.md)
- [セキュリティ仕様書](./SECURITY.md)
- [セットアップガイド](../guides/SETUP.md)
- [デプロイガイド](../guides/DEPLOYMENT.md)
