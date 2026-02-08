# エンタープライズログ管理仕様書

## 目次

1. [はじめに](#1-はじめに)
2. [ログ管理の基本概念](#2-ログ管理の基本概念)
3. [構造化ログの設計](#3-構造化ログの設計)
4. [実装詳細](#4-実装詳細)
5. [ログレベルと使い分け](#5-ログレベルと使い分け)
6. [相関IDによるリクエスト追跡](#6-相関idによるリクエスト追跡)
7. [センシティブデータのマスキング](#7-センシティブデータのマスキング)
8. [パフォーマンスログ](#8-パフォーマンスログ)
9. [監査ログ](#9-監査ログ)
10. [クラウド統合](#10-クラウド統合)
11. [設定方法](#11-設定方法)
12. [ベストプラクティス](#12-ベストプラクティス)

---

## 1. はじめに

### 1.1 このドキュメントの目的

このドキュメントでは、本システムで採用しているエンタープライズレベルのログ管理について詳細に解説します。ログ管理は、本番環境での問題解決、セキュリティ監査、パフォーマンス分析において不可欠な要素です。

### 1.2 対象読者

- システムエンジニア（初心者〜中級者）
- DevOpsエンジニア
- セキュリティ担当者
- プロジェクトマネージャー

### 1.3 学習ゴール

このドキュメントを読み終えると、以下ができるようになります：

1. 構造化ログの設計原則を理解できる
2. 相関IDを使った分散トレーシングを実装できる
3. センシティブデータの適切なマスキングができる
4. クラウドログサービスとの統合ができる

---

## 2. ログ管理の基本概念

### 2.1 なぜログが重要なのか

```
┌─────────────────────────────────────────────────────────────────┐
│                    ログの3つの主要目的                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 問題診断（トラブルシューティング）                           │
│     - エラーの原因特定                                           │
│     - パフォーマンス低下の分析                                   │
│     - 障害発生時の根本原因分析（RCA）                            │
│                                                                 │
│  2. セキュリティ監査                                             │
│     - 不正アクセスの検知                                         │
│     - ユーザー行動の追跡                                         │
│     - コンプライアンス要件への対応                               │
│                                                                 │
│  3. ビジネスインサイト                                           │
│     - 利用状況の把握                                             │
│     - 機能の使用頻度分析                                         │
│     - ユーザー体験の改善                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 従来のログ vs 構造化ログ

#### 従来のログ（非構造化）

```
2026-02-08 10:30:45 ERROR - User login failed for user@example.com from IP 192.168.1.1
```

**問題点**：
- 機械処理が困難
- フィールドの抽出に正規表現が必要
- フォーマットが統一されていない

#### 構造化ログ（JSON形式）

```json
{
  "timestamp": "2026-02-08T10:30:45.123456Z",
  "level": "ERROR",
  "logger": "grc_backend.api.routes.auth",
  "message": "User login failed",
  "correlation_id": "abc123-def456-ghi789",
  "user_email": "u***@example.com",
  "client_ip": "192.168.1.1",
  "error_code": "AUTH_INVALID_CREDENTIALS",
  "duration_ms": 150
}
```

**利点**：
- 機械処理が容易（クラウドログサービスで自動パース）
- フィールドによる検索・フィルタリングが可能
- 統計分析やアラート設定が容易

---

## 3. 構造化ログの設計

### 3.1 ログスキーマ

本システムのログは、以下の標準フィールドを持ちます：

```python
# ログエントリの基本構造
{
    # === 必須フィールド ===
    "timestamp": str,       # ISO 8601形式のタイムスタンプ
    "level": str,           # ログレベル (DEBUG/INFO/WARNING/ERROR/CRITICAL)
    "logger": str,          # ロガー名（モジュールパス）
    "message": str,         # ログメッセージ

    # === リクエスト追跡 ===
    "correlation_id": str,  # リクエスト相関ID（分散トレーシング用）
    "request_id": str,      # 個別リクエストID

    # === コンテキスト情報 ===
    "service": str,         # サービス名
    "environment": str,     # 環境 (development/staging/production)
    "version": str,         # アプリケーションバージョン

    # === オプションフィールド ===
    "user_id": str,         # ユーザーID（認証済みの場合）
    "client_ip": str,       # クライアントIPアドレス
    "user_agent": str,      # ユーザーエージェント
    "duration_ms": float,   # 処理時間（ミリ秒）
    "error_code": str,      # エラーコード
    "stack_trace": str,     # スタックトレース（エラー時）
    "extra": dict,          # 追加のカスタムデータ
}
```

### 3.2 フィールド命名規則

| カテゴリ | プレフィックス | 例 |
|---------|---------------|-----|
| ユーザー関連 | `user_` | `user_id`, `user_email` |
| リクエスト関連 | `request_` | `request_id`, `request_path` |
| レスポンス関連 | `response_` | `response_status`, `response_size` |
| エラー関連 | `error_` | `error_code`, `error_message` |
| パフォーマンス関連 | `duration_` / `latency_` | `duration_ms`, `latency_p99` |
| AI関連 | `ai_` | `ai_provider`, `ai_model`, `ai_tokens` |

---

## 4. 実装詳細

### 4.1 ファイル構成

```
apps/backend/src/grc_backend/core/
├── __init__.py          # モジュールエクスポート
├── logging.py           # ログ管理の中核実装 ← このファイルを解説
├── errors.py            # エラー処理（別ドキュメント）
└── security.py          # セキュリティ（別ドキュメント）
```

### 4.2 主要クラス解説

#### 4.2.1 LogConfig（設定クラス）

```python
class LogConfig(BaseSettings):
    """ログ設定を環境変数から読み込むクラス

    Pydanticの BaseSettings を継承することで、環境変数との自動バインディングが可能。

    設計意図:
    - 設定の一元管理
    - 環境ごとの切り替えが容易
    - 型安全性の確保
    """

    # ログレベル: 環境変数 LOG_LEVEL で設定
    # 開発環境: DEBUG, 本番環境: INFO を推奨
    level: str = "INFO"

    # JSON形式出力: 本番環境では True にする
    # クラウドログサービスがJSONを自動パースするため
    json_format: bool = True

    # 相関ID生成: 分散トレーシングに必要
    include_correlation_id: bool = True

    # センシティブデータマスキング: 本番では必須
    mask_sensitive_data: bool = True

    # パフォーマンスログ: 遅延分析用
    log_performance: bool = True

    # 監査ログ: コンプライアンス要件
    audit_log_enabled: bool = True

    class Config:
        env_prefix = "LOG_"  # 環境変数のプレフィックス
        # 例: LOG_LEVEL=DEBUG, LOG_JSON_FORMAT=true
```

**学習ポイント**: Pydantic の `BaseSettings` を使うと、環境変数を型安全に読み込めます。`env_prefix` を設定すると、`LOG_` で始まる環境変数を自動的にマッピングします。

#### 4.2.2 SensitiveDataFilter（マスキングフィルタ）

```python
class SensitiveDataFilter(logging.Filter):
    """センシティブデータをマスキングするログフィルタ

    ログに含まれる可能性のある機密情報を自動的に検出し、
    マスキング処理を行います。

    対象:
    - パスワード
    - APIキー
    - クレジットカード番号
    - 個人情報（メール、電話番号）
    """

    # マスキング対象のパターン定義
    SENSITIVE_PATTERNS = [
        # パスワード: "password": "secret123" → "password": "***MASKED***"
        (r'"password"\s*:\s*"[^"]*"', '"password": "***MASKED***"'),

        # APIキー: 様々な形式に対応
        (r'"api_key"\s*:\s*"[^"]*"', '"api_key": "***MASKED***"'),
        (r'"api[-_]?key"\s*:\s*"[^"]*"', '"api_key": "***MASKED***"'),

        # トークン: JWT、アクセストークンなど
        (r'"token"\s*:\s*"[^"]*"', '"token": "***MASKED***"'),
        (r'"access_token"\s*:\s*"[^"]*"', '"access_token": "***MASKED***"'),
        (r'"refresh_token"\s*:\s*"[^"]*"', '"refresh_token": "***MASKED***"'),

        # シークレット
        (r'"secret"\s*:\s*"[^"]*"', '"secret": "***MASKED***"'),
        (r'"client_secret"\s*:\s*"[^"]*"', '"client_secret": "***MASKED***"'),

        # クレジットカード: 16桁の数字を検出
        (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '****-****-****-****'),

        # メールアドレス: ローカルパートを部分マスク
        (r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
         lambda m: f"{m.group(1)[0]}***@{m.group(2)}"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """ログレコードをフィルタリング

        Args:
            record: ログレコード

        Returns:
            True: ログを出力する
            False: ログを抑制する（このフィルタでは常にTrue）
        """
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = self._mask_sensitive_data(record.msg)
        return True

    def _mask_sensitive_data(self, message: str) -> str:
        """センシティブデータをマスキング"""
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            if callable(replacement):
                message = re.sub(pattern, replacement, message)
            else:
                message = re.sub(pattern, replacement, message)
        return message
```

**学習ポイント**: `logging.Filter` を継承してカスタムフィルタを作成できます。`filter()` メソッドで `True` を返すとログが出力され、`False` を返すと抑制されます。

#### 4.2.3 JSONFormatter（JSON形式フォーマッタ）

```python
class JSONFormatter(logging.Formatter):
    """ログをJSON形式で出力するフォーマッタ

    クラウドログサービス（CloudWatch, Azure Monitor, GCP Logging）は
    JSON形式のログを自動的にパースし、各フィールドで検索可能にします。

    出力例:
    {
        "timestamp": "2026-02-08T10:30:45.123456Z",
        "level": "INFO",
        "logger": "grc_backend.api.routes.interviews",
        "message": "Interview started",
        "correlation_id": "abc123",
        "interview_id": "int-456",
        "user_id": "user-789"
    }
    """

    def format(self, record: logging.LogRecord) -> str:
        """ログレコードをJSON文字列に変換

        処理フロー:
        1. 基本フィールドの構築
        2. 例外情報の追加（あれば）
        3. カスタムフィールドのマージ
        4. JSON文字列へのシリアライズ
        """
        # 基本ログ構造
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),

            # ファイル位置情報（デバッグ用）
            "file": record.filename,
            "line": record.lineno,
            "function": record.funcName,
        }

        # 相関ID（リクエスト追跡用）
        if hasattr(record, 'correlation_id'):
            log_data["correlation_id"] = record.correlation_id

        # 例外情報
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
            }

        # カスタムフィールド（extraで渡されたもの）
        # 例: logger.info("message", extra={"user_id": "123"})
        standard_attrs = {
            'name', 'msg', 'args', 'created', 'filename', 'funcName',
            'levelname', 'levelno', 'lineno', 'module', 'msecs',
            'pathname', 'process', 'processName', 'relativeCreated',
            'stack_info', 'exc_info', 'exc_text', 'thread', 'threadName',
            'correlation_id', 'message', 'asctime'
        }

        for key, value in record.__dict__.items():
            if key not in standard_attrs:
                log_data[key] = value

        return json.dumps(log_data, ensure_ascii=False, default=str)
```

**学習ポイント**: `logging.Formatter` を継承してカスタムフォーマッタを作成します。`format()` メソッドで出力形式を完全にカスタマイズできます。

#### 4.2.4 StructuredLogger（拡張ロガー）

```python
class StructuredLogger(logging.Logger):
    """構造化ログ出力に特化したロガークラス

    標準のLoggerを拡張し、以下の専用メソッドを追加:
    - audit(): 監査ログ
    - performance(): パフォーマンスログ
    - security(): セキュリティイベントログ
    """

    def audit(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id: str | None = None,
        details: dict | None = None,
        **kwargs,
    ) -> None:
        """監査ログを出力

        コンプライアンス要件で必要な操作履歴を記録します。

        Args:
            action: 実行されたアクション (create, read, update, delete)
            resource_type: リソースの種類 (interview, project, report)
            resource_id: リソースのID
            user_id: 操作を行ったユーザーのID
            details: 追加の詳細情報

        使用例:
            logger.audit(
                action="create",
                resource_type="interview",
                resource_id="int-123",
                user_id="user-456",
                details={"template_id": "tmpl-789"}
            )
        """
        log_data = {
            "log_type": "audit",
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "user_id": user_id,
            "details": details or {},
            **kwargs,
        }
        self.info(f"AUDIT: {action} {resource_type}/{resource_id}", extra=log_data)

    def performance(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True,
        metadata: dict | None = None,
        **kwargs,
    ) -> None:
        """パフォーマンスログを出力

        処理時間を記録し、パフォーマンス分析に活用します。

        Args:
            operation: 操作名 (api_call, db_query, ai_inference)
            duration_ms: 処理時間（ミリ秒）
            success: 成功/失敗
            metadata: 追加メタデータ

        使用例:
            start = time.time()
            result = await ai_provider.chat(messages)
            duration_ms = (time.time() - start) * 1000

            logger.performance(
                operation="ai_inference",
                duration_ms=duration_ms,
                metadata={"model": "gpt-4", "tokens": 150}
            )
        """
        log_data = {
            "log_type": "performance",
            "operation": operation,
            "duration_ms": duration_ms,
            "success": success,
            "metadata": metadata or {},
            **kwargs,
        }

        # 処理時間に応じてログレベルを変更
        level = logging.INFO
        if duration_ms > 5000:  # 5秒以上
            level = logging.WARNING
        elif duration_ms > 10000:  # 10秒以上
            level = logging.ERROR

        self.log(level, f"PERF: {operation} took {duration_ms:.2f}ms", extra=log_data)

    def security(
        self,
        event: str,
        severity: str = "info",
        client_ip: str | None = None,
        user_id: str | None = None,
        details: dict | None = None,
        **kwargs,
    ) -> None:
        """セキュリティイベントログを出力

        セキュリティ関連のイベントを記録します。

        Args:
            event: イベント名 (login_failed, rate_limit_exceeded, etc.)
            severity: 重要度 (info, warning, critical)
            client_ip: クライアントIPアドレス
            user_id: 関連するユーザーID
            details: 追加詳細

        使用例:
            logger.security(
                event="login_failed",
                severity="warning",
                client_ip="192.168.1.1",
                details={"attempts": 3}
            )
        """
        log_data = {
            "log_type": "security",
            "security_event": event,
            "severity": severity,
            "client_ip": client_ip,
            "user_id": user_id,
            "details": details or {},
            **kwargs,
        }

        level_map = {
            "info": logging.INFO,
            "warning": logging.WARNING,
            "critical": logging.CRITICAL,
        }
        level = level_map.get(severity, logging.INFO)

        self.log(level, f"SECURITY: {event}", extra=log_data)
```

**学習ポイント**: `logging.Logger` を継承してカスタムメソッドを追加できます。`logging.setLoggerClass()` で登録すると、`logging.getLogger()` でカスタムロガーが返されます。

---

## 5. ログレベルと使い分け

### 5.1 ログレベルの定義

```
┌─────────────────────────────────────────────────────────────────┐
│                    ログレベルピラミッド                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                          CRITICAL                               │
│                         ▲ 重大 ▲                               │
│                        ／         ＼                            │
│                       ／  ERROR    ＼                           │
│                      ▲    エラー    ▲                          │
│                     ／               ＼                         │
│                    ／    WARNING      ＼                        │
│                   ▲       警告        ▲                        │
│                  ／                     ＼                      │
│                 ／        INFO           ＼                     │
│                ▲         情報            ▲                     │
│               ／                           ＼                   │
│              ／          DEBUG              ＼                  │
│             ▲           詳細               ▲                   │
│            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                  │
│                                                                 │
│  上位レベルを設定すると、それ以上のレベルのみ出力される          │
│  例: INFO を設定 → INFO, WARNING, ERROR, CRITICAL が出力        │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 各レベルの使用指針

| レベル | 用途 | 例 |
|--------|------|-----|
| **DEBUG** | 開発・デバッグ用の詳細情報 | 変数値、SQL、API呼び出し詳細 |
| **INFO** | 正常な処理の記録 | リクエスト受信、処理完了 |
| **WARNING** | 問題の可能性があるが継続可能 | 非推奨API使用、リトライ発生 |
| **ERROR** | エラー発生、処理失敗 | 例外発生、外部サービス障害 |
| **CRITICAL** | システム停止レベルの重大問題 | DB接続不可、設定エラー |

### 5.3 実践的な使用例

```python
# DEBUG: 開発時のみ必要な詳細情報
logger.debug(
    "AI provider request",
    extra={
        "provider": "azure_openai",
        "model": "gpt-4",
        "messages_count": len(messages),
        "temperature": 0.7,
    }
)

# INFO: 通常の処理フロー
logger.info(
    "Interview started",
    extra={
        "interview_id": interview_id,
        "template_id": template_id,
        "language": "ja",
    }
)

# WARNING: 注意が必要だが処理は継続
logger.warning(
    "Rate limit approaching",
    extra={
        "current_requests": 90,
        "limit": 100,
        "window_seconds": 60,
    }
)

# ERROR: エラーが発生したが回復可能
logger.error(
    "External API call failed",
    extra={
        "service": "speech_recognition",
        "error_code": "TIMEOUT",
        "retry_count": 3,
    },
    exc_info=True,  # スタックトレースを含める
)

# CRITICAL: システムレベルの重大問題
logger.critical(
    "Database connection pool exhausted",
    extra={
        "active_connections": 100,
        "max_connections": 100,
        "waiting_requests": 50,
    }
)
```

---

## 6. 相関IDによるリクエスト追跡

### 6.1 相関IDとは

相関ID（Correlation ID）は、1つのリクエストに対する全ての処理を追跡するための一意識別子です。

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         リクエストフロー                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  クライアント ─────▶ API Gateway ─────▶ Backend ─────▶ AI Provider          │
│       │                  │                │               │                 │
│       │    X-Correlation-ID: abc123       │               │                 │
│       │ ◀────────────────────────────────────────────────────────────────▶ │
│                                                                             │
│  すべてのサービスで同じ correlation_id: "abc123" を使用                      │
│  → 分散システムでも一連のリクエストを追跡可能                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 実装方法

#### ミドルウェアでの相関ID設定

```python
from contextvars import ContextVar
import uuid

# コンテキスト変数: スレッドセーフに相関IDを保持
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")

class CorrelationIdMiddleware:
    """相関IDを管理するミドルウェア

    処理フロー:
    1. リクエストヘッダーから相関IDを取得（既存の場合）
    2. なければ新規生成
    3. コンテキスト変数に設定
    4. レスポンスヘッダーにも付与
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            # ヘッダーから既存の相関IDを取得
            headers = dict(scope.get("headers", []))
            correlation_id = headers.get(
                b"x-correlation-id",
                str(uuid.uuid4()).encode()
            ).decode()

            # コンテキストに設定
            token = correlation_id_ctx.set(correlation_id)

            # レスポンスに相関IDを追加
            async def send_with_correlation_id(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    headers.append((b"x-correlation-id", correlation_id.encode()))
                    message["headers"] = headers
                await send(message)

            try:
                await self.app(scope, receive, send_with_correlation_id)
            finally:
                correlation_id_ctx.reset(token)
        else:
            await self.app(scope, receive, send)
```

#### ロガーでの相関ID自動付与

```python
class CorrelationIdFilter(logging.Filter):
    """すべてのログに相関IDを自動付与するフィルタ"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = correlation_id_ctx.get() or "no-correlation-id"
        return True
```

### 6.3 使用方法

```python
# 相関IDは自動的にログに含まれる
logger.info("Processing interview", extra={"interview_id": "int-123"})

# 出力例:
# {
#     "timestamp": "2026-02-08T10:30:45.123Z",
#     "level": "INFO",
#     "message": "Processing interview",
#     "correlation_id": "abc123-def456-ghi789",  ← 自動付与
#     "interview_id": "int-123"
# }
```

---

## 7. センシティブデータのマスキング

### 7.1 マスキングが必要なデータ

| カテゴリ | データ種類 | マスキング例 |
|---------|-----------|-------------|
| 認証情報 | パスワード | `***MASKED***` |
| | APIキー | `***MASKED***` |
| | トークン | `***MASKED***` |
| 個人情報 | メールアドレス | `u***@example.com` |
| | 電話番号 | `***-****-1234` |
| | クレジットカード | `****-****-****-1234` |
| 機密情報 | 社内ID | 部分マスク |

### 7.2 マスキングのタイミング

```
┌─────────────────────────────────────────────────────────────────┐
│               マスキングはログ出力時に行う                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ❌ 悪い例: データ処理時にマスク                                │
│                                                                 │
│      user.email = mask(user.email)  # 元データが失われる        │
│      save_to_db(user)                                           │
│      logger.info(f"User: {user}")                               │
│                                                                 │
│   ✅ 良い例: ログ出力時にのみマスク                              │
│                                                                 │
│      save_to_db(user)  # 元データは保持                         │
│      logger.info("User saved", extra={"email": user.email})     │
│      # ↑ SensitiveDataFilter がログ出力時にマスキング           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.3 カスタムマスキングルールの追加

```python
class CustomSensitiveDataFilter(SensitiveDataFilter):
    """プロジェクト固有のマスキングルールを追加"""

    # 親クラスのパターンに追加
    ADDITIONAL_PATTERNS = [
        # 社員番号: EMP-123456 → EMP-***
        (r'EMP-\d{6}', 'EMP-******'),

        # 内部プロジェクトID
        (r'PRJ-[A-Z0-9]{8}', 'PRJ-********'),

        # カスタム機密フィールド
        (r'"salary"\s*:\s*\d+', '"salary": ***MASKED***'),
    ]

    def __init__(self):
        super().__init__()
        self.SENSITIVE_PATTERNS.extend(self.ADDITIONAL_PATTERNS)
```

---

## 8. パフォーマンスログ

### 8.1 計測対象

| カテゴリ | 計測項目 | 警告閾値 |
|---------|---------|---------|
| API | レスポンス時間 | > 3秒 |
| データベース | クエリ実行時間 | > 1秒 |
| AI推論 | TTFT (Time to First Token) | > 2秒 |
| | 総処理時間 | > 30秒 |
| 外部API | 応答時間 | > 5秒 |

### 8.2 実装パターン

#### デコレータを使った計測

```python
from functools import wraps
import time

def log_performance(operation: str):
    """パフォーマンス計測デコレータ

    使用例:
        @log_performance("db_query")
        async def get_user(user_id: str):
            return await db.users.get(user_id)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            success = True
            error = None

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error = str(e)
                raise
            finally:
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.performance(
                    operation=operation,
                    duration_ms=duration_ms,
                    success=success,
                    metadata={
                        "function": func.__name__,
                        "error": error,
                    }
                )
        return wrapper
    return decorator
```

#### コンテキストマネージャを使った計測

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def measure_performance(operation: str, **metadata):
    """パフォーマンス計測コンテキストマネージャ

    使用例:
        async with measure_performance("ai_inference", model="gpt-4"):
            response = await ai.chat(messages)
    """
    start_time = time.perf_counter()
    success = True
    error = None

    try:
        yield
    except Exception as e:
        success = False
        error = str(e)
        raise
    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.performance(
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            metadata={**metadata, "error": error},
        )
```

### 8.3 レイテンシクラス

AI推論の応答時間を分類するためのレイテンシクラス：

```python
class LatencyClass(str, Enum):
    """AI応答のレイテンシ分類

    リアルタイム対話では ULTRA_FAST または FAST を使用するモデルを選択
    """
    ULTRA_FAST = "ultra_fast"  # TTFT < 200ms （音声対話に最適）
    FAST = "fast"              # TTFT 200-500ms （チャットに適切）
    STANDARD = "standard"      # TTFT 500ms-1s （バッチ処理向け）
    SLOW = "slow"              # TTFT > 1s （非同期処理向け）

# モデル別のレイテンシクラス定義
MODEL_LATENCY_CLASSES = {
    "gpt-5-nano": LatencyClass.ULTRA_FAST,
    "gpt-5.2": LatencyClass.FAST,
    "claude-opus-4.5": LatencyClass.STANDARD,
}
```

---

## 9. 監査ログ

### 9.1 監査ログの目的

監査ログは、コンプライアンス要件（SOC2、ISO27001など）を満たすために必要な操作履歴です。

### 9.2 記録すべき操作

| カテゴリ | 操作 | 必須フィールド |
|---------|------|---------------|
| 認証 | ログイン/ログアウト | user_id, client_ip, success |
| データアクセス | 閲覧/ダウンロード | user_id, resource_type, resource_id |
| データ変更 | 作成/更新/削除 | user_id, resource_type, before/after |
| 権限変更 | ロール変更 | admin_id, target_user_id, changes |
| 設定変更 | システム設定変更 | admin_id, setting_key, before/after |

### 9.3 実装例

```python
# インタビュー作成時の監査ログ
async def create_interview(
    request: InterviewCreate,
    current_user: User,
):
    interview = await interview_repo.create(request)

    # 監査ログを記録
    logger.audit(
        action="create",
        resource_type="interview",
        resource_id=str(interview.id),
        user_id=str(current_user.id),
        details={
            "project_id": str(request.project_id),
            "template_id": str(request.template_id),
            "language": request.language,
        }
    )

    return interview

# データベースへの監査ログ永続化
class AuditLogService:
    """監査ログをデータベースに永続化するサービス"""

    async def log(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id: str,
        details: dict,
        client_ip: str | None = None,
    ):
        audit_log = AuditLog(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            action=action,
            resource_type=resource_type,
            resource_id=uuid.UUID(resource_id),
            details=details,
            ip_address=client_ip,
            created_at=datetime.now(timezone.utc),
        )
        await self.repo.create(audit_log)
```

---

## 10. クラウド統合

### 10.1 サポートするクラウドログサービス

| クラウド | サービス名 | 特徴 |
|---------|-----------|------|
| Azure | Azure Monitor / Log Analytics | Kusto Query Language (KQL) |
| AWS | CloudWatch Logs | Insights クエリ |
| GCP | Cloud Logging | BigQuery連携 |

### 10.2 Azure Monitor 統合

```python
# OpenTelemetry を使用した Azure Monitor 連携
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter

def setup_azure_monitor():
    """Azure Monitor との連携を設定"""

    # 接続文字列から Exporter を作成
    exporter = AzureMonitorTraceExporter(
        connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    )

    # TracerProvider を設定
    provider = TracerProvider()
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
```

### 10.3 AWS CloudWatch 統合

```python
import watchtower
import logging

def setup_cloudwatch():
    """AWS CloudWatch Logs との連携を設定"""

    # CloudWatch ハンドラーを追加
    cloudwatch_handler = watchtower.CloudWatchLogHandler(
        log_group="/ecs/ai-interviewer",
        stream_name="backend-{strftime:%Y-%m-%d}",
        use_queues=True,  # 非同期送信
    )
    cloudwatch_handler.setFormatter(JSONFormatter())

    logging.getLogger().addHandler(cloudwatch_handler)
```

### 10.4 GCP Cloud Logging 統合

```python
from google.cloud import logging as gcp_logging

def setup_gcp_logging():
    """GCP Cloud Logging との連携を設定"""

    client = gcp_logging.Client()

    # Python ロガーと Cloud Logging を連携
    client.setup_logging()

    # 構造化ログのためのハンドラー設定
    handler = client.get_default_handler()
    handler.setFormatter(JSONFormatter())
```

---

## 11. 設定方法

### 11.1 環境変数

```bash
# .env ファイル

# === ログ基本設定 ===
LOG_LEVEL=INFO                    # DEBUG / INFO / WARNING / ERROR / CRITICAL
LOG_JSON_FORMAT=true              # true: JSON形式, false: テキスト形式

# === 機能フラグ ===
LOG_INCLUDE_CORRELATION_ID=true   # 相関IDを含める
LOG_MASK_SENSITIVE_DATA=true      # センシティブデータをマスク
LOG_PERFORMANCE=true              # パフォーマンスログを出力
LOG_AUDIT_ENABLED=true            # 監査ログを有効化

# === クラウド連携 ===
# Azure
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=xxx;IngestionEndpoint=https://xxx

# AWS
AWS_CLOUDWATCH_LOG_GROUP=/ecs/ai-interviewer

# GCP
GOOGLE_CLOUD_PROJECT=your-project-id
```

### 11.2 環境別推奨設定

```yaml
# 開発環境
development:
  LOG_LEVEL: DEBUG
  LOG_JSON_FORMAT: false       # 人間が読みやすいテキスト形式
  LOG_MASK_SENSITIVE_DATA: false  # 開発時はマスクなし
  LOG_PERFORMANCE: true

# ステージング環境
staging:
  LOG_LEVEL: INFO
  LOG_JSON_FORMAT: true
  LOG_MASK_SENSITIVE_DATA: true
  LOG_PERFORMANCE: true

# 本番環境
production:
  LOG_LEVEL: INFO              # WARNING でも可（ログ量削減）
  LOG_JSON_FORMAT: true
  LOG_MASK_SENSITIVE_DATA: true
  LOG_PERFORMANCE: true
  LOG_AUDIT_ENABLED: true
```

---

## 12. ベストプラクティス

### 12.1 ログ設計のDo's and Don'ts

#### ✅ Do's（推奨）

```python
# 1. 構造化データを使用
logger.info("User logged in", extra={
    "user_id": user.id,
    "login_method": "oauth",
    "client_ip": request.client.host,
})

# 2. 適切なログレベルを選択
logger.debug("Received request payload", extra={"payload": sanitized_payload})
logger.info("Processing started", extra={"task_id": task_id})
logger.warning("Deprecated API called", extra={"endpoint": "/api/v1/old"})
logger.error("External service failed", extra={"service": "payment"}, exc_info=True)

# 3. コンテキスト情報を含める
logger.info("Interview completed", extra={
    "interview_id": interview.id,
    "duration_seconds": interview.duration,
    "questions_count": len(interview.questions),
    "language": interview.language,
})

# 4. 例外時はスタックトレースを含める
try:
    result = await risky_operation()
except Exception as e:
    logger.error("Operation failed", exc_info=True, extra={"operation": "risky"})
    raise
```

#### ❌ Don'ts（非推奨）

```python
# 1. 非構造化メッセージ
logger.info(f"User {user.id} logged in from {ip}")  # ❌ パースしにくい

# 2. センシティブデータの直接出力
logger.info(f"Login with password: {password}")  # ❌ 絶対禁止

# 3. 過剰なログ（ループ内）
for item in large_list:
    logger.debug(f"Processing item: {item}")  # ❌ ログ爆発

# 4. 意味のないメッセージ
logger.info("here")  # ❌ 何の情報もない
logger.info("done")  # ❌ 何が done なのか不明

# 5. ログレベルの誤用
logger.error("User not found")  # ❌ 正常なケースならWARNINGかINFO
```

### 12.2 チェックリスト

```markdown
## ログ実装チェックリスト

### 基本設定
- [ ] 環境変数で設定可能になっている
- [ ] 開発/本番で異なる設定が適用される
- [ ] JSON形式での出力に対応している

### セキュリティ
- [ ] パスワード/トークンがマスクされている
- [ ] 個人情報（PII）が適切に処理されている
- [ ] 機密ビジネスデータが保護されている

### 追跡性
- [ ] 相関IDが全リクエストに付与されている
- [ ] エラー時にスタックトレースが含まれている
- [ ] 監査ログが必要な操作に記録されている

### パフォーマンス
- [ ] 重要な処理の所要時間が記録されている
- [ ] 閾値超過時に適切なログレベルで出力される
- [ ] 非同期ログ出力でパフォーマンスに影響しない

### 運用
- [ ] クラウドログサービスとの連携が設定されている
- [ ] ログローテーションが設定されている
- [ ] アラート設定が適切に行われている
```

---

## 付録

### A. よく使うログクエリ（Azure Log Analytics）

```kusto
// エラーログの検索
traces
| where severityLevel >= 3
| where timestamp > ago(1h)
| project timestamp, message, customDimensions
| order by timestamp desc

// 特定の相関IDで追跡
traces
| where customDimensions.correlation_id == "abc123"
| order by timestamp asc

// パフォーマンス分析
traces
| where customDimensions.log_type == "performance"
| summarize
    avg_duration = avg(todouble(customDimensions.duration_ms)),
    p95_duration = percentile(todouble(customDimensions.duration_ms), 95)
    by operation = tostring(customDimensions.operation)
```

### B. 関連ドキュメント

- [エラー処理仕様書](./ERROR_HANDLING.md)
- [セキュリティ仕様書](./SECURITY.md)
- [インフラストラクチャ仕様書](./INFRASTRUCTURE.md)
