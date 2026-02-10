# AI Interview Tool - 開発ガイド

このガイドでは、プロジェクトの開発方法、コーディング規約、テスト方法を説明します。

## 目次

1. [プロジェクト構成](#1-プロジェクト構成)
2. [開発ワークフロー](#2-開発ワークフロー)
3. [コーディング規約](#3-コーディング規約)
4. [テスト](#4-テスト)
5. [Git運用](#5-git運用)
6. [デバッグ](#6-デバッグ)
7. [CI/CD パイプライン](#7-cicd-パイプライン)

---

## 1. プロジェクト構成

```
ai-interviewer/
├── apps/                      # アプリケーション
│   ├── backend/               # FastAPI バックエンド (Python)
│   │   ├── src/grc_backend/   # ソースコード
│   │   ├── tests/             # テストコード
│   │   ├── migrations/        # DBマイグレーション
│   │   └── pyproject.toml     # Python依存関係
│   ├── web/                   # Next.js フロントエンド
│   │   ├── src/
│   │   │   ├── app/           # App Router ページ
│   │   │   ├── components/    # Reactコンポーネント
│   │   │   ├── hooks/         # Reactフック
│   │   │   ├── lib/           # ユーティリティ
│   │   │   └── locales/       # 多言語リソース
│   │   └── package.json       # Node.js依存関係
│   └── mobile/                # React Native モバイルアプリ
│
├── packages/                  # 共通パッケージ
│   └── @grc/
│       ├── core/              # ドメインモデル・リポジトリ
│       ├── ai/                # AIプロバイダー抽象化
│       ├── infrastructure/    # ストレージ・キュー抽象化
│       └── ui/                # 共通UIコンポーネント
│
├── infrastructure/            # インフラ設定
│   └── terraform/             # マルチクラウドIaC
│
├── docs/                      # ドキュメント
│
├── .github/workflows/         # CI/CD パイプライン
│
├── docker-compose.yml         # 開発環境
└── docker-compose.prod.yml    # 本番環境
```

---

## 2. 開発ワークフロー

### 2.1 日常の開発フロー

```bash
# 1. 最新のmainブランチを取得
git checkout main
git pull origin main

# 2. 機能ブランチを作成
git checkout -b feature/機能名

# 3. Dockerサービスを起動
docker-compose up -d postgres redis

# 4. バックエンドを起動
cd apps/backend
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uvicorn grc_backend.main:app --reload

# 5. フロントエンドを起動（別ターミナル）
cd apps/web
pnpm dev

# 6. コーディング...

# 7. テストを実行
cd apps/backend && pytest tests/
cd apps/web && pnpm test

# 8. コミット＆プッシュ
git add .
git commit -m "feat: 機能の説明"
git push origin feature/機能名

# 9. Pull Requestを作成
```

### 2.2 Docker を使った開発

すべてのサービスをDockerで起動する場合：

```bash
# 開発環境を一括起動
docker-compose up -d

# ログを確認
docker-compose logs -f backend

# 再ビルド（コード変更後）
docker-compose up -d --build backend

# 停止
docker-compose down
```

### 2.3 Ollama (ローカルLLM) を使った開発

ローカルのLLMを使って開発・テストする場合：

```bash
# Ollama付きで起動
docker compose --profile local-llm up -d

# モデルをダウンロード
docker exec ai-interviewer-ollama ollama pull gemma3:1b

# .envの設定
AI_PROVIDER=local
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:1b

# 接続テスト
curl http://localhost:11434/api/tags
```

---

## 3. コーディング規約

### 3.1 Python (Backend)

#### フォーマッター・リンター

```bash
# Ruffでリント＆フォーマット
ruff check apps/backend/src --fix
ruff format apps/backend/src

# 型チェック
mypy apps/backend/src
```

#### 命名規則

```python
# クラス: PascalCase
class InterviewService:
    pass

# 関数・変数: snake_case
def create_interview(interview_data: InterviewCreate) -> Interview:
    interview_id = generate_uuid()
    return Interview(id=interview_id)

# 定数: UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

# プライベート: _ プレフィックス
def _validate_input(data: dict) -> bool:
    pass
```

#### docstring形式

```python
async def create_interview(
    project_id: str,
    template_id: str,
    interviewer_id: str,
) -> Interview:
    """インタビューを作成する。

    Args:
        project_id: 案件ID
        template_id: テンプレートID
        interviewer_id: インタビュアーのユーザーID

    Returns:
        作成されたインタビューオブジェクト

    Raises:
        NotFoundError: プロジェクトまたはテンプレートが見つからない場合
        ValidationError: 入力データが無効な場合
    """
    pass
```

### 3.2 TypeScript (Frontend)

#### フォーマッター・リンター

```bash
# ESLintでリント
pnpm lint

# Prettierでフォーマット
pnpm format

# 型チェック
pnpm type-check
```

#### 命名規則

```typescript
// コンポーネント: PascalCase
export function InterviewCard({ interview }: InterviewCardProps) {
  return <div>...</div>;
}

// フック: camelCase with use prefix
function useInterview(id: string) {
  return useQuery(['interview', id], () => fetchInterview(id));
}

// 型・インターフェース: PascalCase
interface InterviewCardProps {
  interview: Interview;
  onSelect?: (id: string) => void;
}

// 定数: UPPER_SNAKE_CASE
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;
```

### 3.3 コミットメッセージ

[Conventional Commits](https://www.conventionalcommits.org/) 形式を使用：

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**type の種類**:
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント変更
- `style`: コードスタイル変更（動作に影響なし）
- `refactor`: リファクタリング
- `test`: テスト追加・修正
- `chore`: ビルド・ツール変更

**例**:
```
feat(interview): インタビュー一時停止機能を追加

- WebSocket経由で一時停止/再開を制御
- UIに一時停止ボタンを追加
- 一時停止中の状態をRedisに保存

Closes #123
```

---

## 4. テスト

### 4.1 バックエンドテスト (pytest)

```bash
cd apps/backend

# すべてのテストを実行
pytest tests/ -v

# 特定のファイルをテスト
pytest tests/test_interviews.py -v

# カバレッジ付きで実行
pytest tests/ --cov=src/grc_backend --cov-report=html

# 失敗したテストのみ再実行
pytest tests/ --lf
```

#### テストの書き方

```python
# tests/test_interviews.py
import pytest
from httpx import AsyncClient
from grc_backend.main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_create_interview(client: AsyncClient, auth_headers: dict):
    """インタビュー作成のテスト"""
    response = await client.post(
        "/api/v1/interviews",
        json={
            "project_id": "test-project-id",
            "template_id": "test-template-id",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["status"] == "scheduled"
```

### 4.2 フロントエンドテスト

```bash
cd apps/web

# ユニットテストを実行
pnpm test

# ウォッチモードで実行
pnpm test:watch

# カバレッジ付きで実行
pnpm test --coverage

# E2Eテスト（Playwright）
pnpm test:e2e
```

#### テストの書き方

```typescript
// components/__tests__/InterviewCard.test.tsx
import { render, screen } from '@testing-library/react';
import { InterviewCard } from '../InterviewCard';

describe('InterviewCard', () => {
  const mockInterview = {
    id: '1',
    title: 'テストインタビュー',
    status: 'scheduled',
    scheduledAt: '2026-02-08T10:00:00Z',
  };

  it('インタビュータイトルを表示する', () => {
    render(<InterviewCard interview={mockInterview} />);

    expect(screen.getByText('テストインタビュー')).toBeInTheDocument();
  });

  it('ステータスバッジを表示する', () => {
    render(<InterviewCard interview={mockInterview} />);

    expect(screen.getByText('予定')).toBeInTheDocument();
  });
});
```

### 4.3 パッケージテスト

```bash
# AIパッケージ
cd packages/@grc/ai
pytest tests/ -v

# Coreパッケージ
cd packages/@grc/core
pytest tests/ -v
```

### 4.4 Models API テスト

```bash
# モデル一覧の取得
curl http://localhost:8000/api/v1/models

# 推奨モデルの取得
curl http://localhost:8000/api/v1/models/recommended

# プロバイダー情報
curl http://localhost:8000/api/v1/models/providers

# 接続テスト
curl -X POST http://localhost:8000/api/v1/models/test-connection \
  -H "Content-Type: application/json" \
  -d '{"provider": "local"}'
```

---

## 5. Git運用

### 5.1 ブランチ戦略

```
main
├── feature/interview-pause     # 機能開発
├── feature/report-export       # 機能開発
└── fix/login-error             # バグ修正
```

- `main`: 本番環境に対応（直接プッシュは禁止、PRを使用）
- `feature/*`: 機能開発ブランチ
- `fix/*`: バグ修正ブランチ

### 5.2 Pull Requestの作成

1. **タイトル**: 変更内容を簡潔に（日本語OK）
2. **説明**: 以下のテンプレートを使用

```markdown
## 概要
<!-- 何を変更したか -->

## 変更内容
- [ ] 機能A
- [ ] 機能B

## テスト方法
1. ステップ1
2. ステップ2

## スクリーンショット
<!-- UIの変更がある場合 -->

## 関連Issue
Closes #123
```

### 5.3 コードレビュー

**レビュアーへ**:
- 動作確認を行う
- コーディング規約に従っているか確認
- テストが十分か確認
- セキュリティ上の問題がないか確認

**レビュイーへ**:
- レビューコメントには丁寧に返信
- 修正したらコメントで報告
- 大きな変更は事前に相談

---

## 6. デバッグ

### 6.1 バックエンドのデバッグ

#### ログの確認

```python
from grc_backend.core.logging import get_logger

logger = get_logger(__name__)

def some_function():
    logger.debug("デバッグ情報", data={"key": "value"})
    logger.info("処理開始")
    logger.warning("警告")
    logger.error("エラー発生", exc_info=True)
```

#### VS Codeでのデバッグ

`.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Backend Debug",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["grc_backend.main:app", "--reload", "--port", "8000"],
      "cwd": "${workspaceFolder}/apps/backend",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/apps/backend/src:${workspaceFolder}/packages/@grc/core/src:${workspaceFolder}/packages/@grc/ai/src"
      }
    }
  ]
}
```

### 6.2 フロントエンドのデバッグ

#### ブラウザDevTools

1. F12でDevToolsを開く
2. Consoleタブでエラーを確認
3. Networkタブでリクエストを確認
4. React DevToolsでコンポーネントを確認

#### ログの出力

```typescript
// 開発環境でのみ出力
if (process.env.NODE_ENV === 'development') {
  console.log('Debug:', data);
}
```

### 6.3 データベースの確認

```bash
# psqlで接続
docker exec -it ai-interviewer-db psql -U grc_user -d ai_interviewer

# テーブル一覧
\dt

# テーブルの中身を確認
SELECT * FROM interviews LIMIT 10;

# 終了
\q
```

### 6.4 Redisの確認

```bash
# redis-cliで接続
docker exec -it ai-interviewer-redis redis-cli

# キー一覧
KEYS *

# 値を確認
GET session:xxxxx

# 終了
EXIT
```

### 6.5 デモデータの管理

開発時にデモデータを使用して動作確認を行えます。

```bash
# デモデータの投入
python -m grc_backend.demo seed

# デモデータのリセット（削除→再投入）
python -m grc_backend.demo reset

# デモデータの状態確認
python -m grc_backend.demo status

# API経由でも操作可能（development環境のみ）
curl -X POST http://localhost:8000/api/v1/demo/seed
curl -X POST http://localhost:8000/api/v1/demo/reset
curl http://localhost:8000/api/v1/demo/status
```

Docker環境では `SEED_DEMO=true` で起動時に自動投入されます。

---

## 7. CI/CD パイプライン

### 7.1 CI/CDとは？

- **CI (Continuous Integration)**: コードをプッシュするたびに自動でテスト・品質チェックを実行
- **CD (Continuous Deployment)**: テスト通過後に自動でデプロイ

### 7.2 GitHub Actionsの仕組み

- `.github/workflows/` フォルダにYAMLファイルで定義
- プッシュやPRをトリガーに自動実行
- 各「ジョブ」は独立した仮想マシンで実行

### 7.3 ci.yml の各ジョブ

| ジョブ名 | 実行内容 | 必須/任意 |
| ------- | ------- | -------- |
| backend-lint | Ruff(リンター) + MyPy(型チェック) | 必須 |
| backend-test | pytest + カバレッジ計測 | 必須 |
| frontend-lint | ESLint + TypeScript型チェック | 必須 |
| frontend-test | Jest ユニットテスト | 必須 |
| frontend-build | Next.js 本番ビルド | 必須 |
| integration-test-ollama | Ollama連携テスト | 任意 |
| e2e-test | Playwright E2Eテスト | 任意 |
| security-scan | Trivy脆弱性 + Gitleaksシークレット検出 | 任意 |
| docker-build | Dockerイメージビルドテスト | 必須 |
| terraform-validate | Terraform(Azure/AWS/GCP)検証 | 必須 |

### 7.4 ローカルでCIと同等のチェックを実行

```bash
# 1. Python リント & フォーマット
cd apps/backend
ruff check src/ --fix && ruff format src/

# 2. Python テスト
pytest tests/ -v --tb=short

# 3. TypeScript リント
cd apps/web
pnpm lint

# 4. フロントエンドテスト
pnpm test

# 5. ビルド確認
pnpm build

# 6. Dockerビルドテスト
cd ../..
docker build -t test-backend -f apps/backend/Dockerfile --target production .
docker build -t test-web -f apps/web/Dockerfile --target production .
```

### 7.5 PRからデプロイまでのフロー

```text
feature/xxx ブランチ
    ↓ git push
GitHub PR 作成
    ↓ 自動実行
CI パイプライン (ci.yml)
    ├── リント & 型チェック
    ├── テスト実行
    ├── セキュリティスキャン
    ├── Dockerビルド
    └── Terraform検証
    ↓ 全ジョブ成功
レビュー & マージ (→ main)
    ↓ 自動実行
CD パイプライン (deploy.yml)
    ├── Dockerイメージビルド
    ├── GHCR にプッシュ
    └── クラウドにデプロイ (Azure/AWS/GCP)
```

---

## よく使うコマンド一覧

```bash
# 開発サーバー起動
docker-compose up -d              # Docker全体
cd apps/backend && uvicorn grc_backend.main:app --reload  # バックエンド
cd apps/web && pnpm dev           # フロントエンド

# テスト
cd apps/backend && pytest tests/ -v
cd apps/web && pnpm test

# リント＆フォーマット
ruff check --fix && ruff format   # Python
pnpm lint && pnpm format          # TypeScript

# データベース操作
cd apps/backend && alembic upgrade head    # マイグレーション適用
cd apps/backend && alembic revision -m "説明"  # マイグレーション作成

# Docker操作
docker-compose logs -f            # ログ確認
docker-compose down               # 停止
docker-compose up -d --build      # 再ビルド
```
