# エンタープライズエラー処理仕様書

## 目次

1. [はじめに](#1-はじめに)
2. [エラー処理の基本原則](#2-エラー処理の基本原則)
3. [エラー階層設計](#3-エラー階層設計)
4. [エラーコード体系](#4-エラーコード体系)
5. [実装詳細](#5-実装詳細)
6. [リトライ戦略](#6-リトライ戦略)
7. [サーキットブレーカー](#7-サーキットブレーカー)
8. [API エラーレスポンス](#8-api-エラーレスポンス)
9. [フロントエンドでのエラー処理](#9-フロントエンドでのエラー処理)
10. [グローバルエラーハンドリング](#10-グローバルエラーハンドリング)
11. [テスト方法](#11-テスト方法)
12. [ベストプラクティス](#12-ベストプラクティス)

---

## 1. はじめに

### 1.1 このドキュメントの目的

エンタープライズシステムでは、エラーが発生した際に適切に処理し、ユーザーに分かりやすいフィードバックを返すことが重要です。このドキュメントでは、堅牢なエラー処理システムの設計と実装について詳しく解説します。

### 1.2 学習ゴール

1. エラー階層の設計原則を理解できる
2. リトライ可能なエラーとそうでないエラーを区別できる
3. サーキットブレーカーパターンを実装できる
4. 統一されたAPIエラーレスポンスを設計できる

### 1.3 なぜエラー処理が重要か

```
┌─────────────────────────────────────────────────────────────────┐
│              エラー処理が不適切な場合の影響                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. ユーザー体験の低下                                           │
│     - 「不明なエラー」という意味不明なメッセージ                 │
│     - どうすればいいか分からない                                 │
│                                                                 │
│  2. デバッグの困難さ                                             │
│     - スタックトレースがない                                     │
│     - エラーの原因が特定できない                                 │
│                                                                 │
│  3. セキュリティリスク                                           │
│     - 内部エラーの詳細がユーザーに露出                           │
│     - 攻撃者に情報を与える                                       │
│                                                                 │
│  4. システム安定性の低下                                         │
│     - 連鎖的な障害（カスケード障害）                             │
│     - リソースの枯渇                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. エラー処理の基本原則

### 2.1 Fail Fast（早期失敗）

```python
# ❌ 悪い例: 失敗を遅らせる
def process_interview(interview_id: str):
    interview = get_interview(interview_id)
    # interview が None でも処理を続ける
    template = get_template(interview.template_id)  # ここでAttributeError
    ...

# ✅ 良い例: 早期に失敗
def process_interview(interview_id: str):
    interview = get_interview(interview_id)
    if not interview:
        raise NotFoundError(
            message="Interview not found",
            resource_type="interview",
            resource_id=interview_id
        )

    template = get_template(interview.template_id)
    ...
```

**原則**: 問題を早期に検出し、明確なエラーを発生させる。曖昧な状態で処理を続けない。

### 2.2 Fail Gracefully（優雅な失敗）

```python
# ❌ 悪い例: すべての例外をそのまま上げる
async def get_ai_response(messages):
    return await ai_provider.chat(messages)  # 例外がそのまま伝播

# ✅ 良い例: 適切にラップして意味のあるエラーに変換
async def get_ai_response(messages):
    try:
        return await ai_provider.chat(messages)
    except RateLimitError as e:
        raise AIProviderError(
            message="AI service rate limit exceeded",
            code=ErrorCode.AI_RATE_LIMIT,
            retry_after=e.retry_after,
            cause=e
        )
    except TimeoutError as e:
        raise AIProviderError(
            message="AI service timeout",
            code=ErrorCode.AI_TIMEOUT,
            is_retryable=True,
            cause=e
        )
```

**原則**: 低レベルの例外を意味のあるドメインエラーに変換する。

### 2.3 Never Swallow Exceptions（例外を握りつぶさない）

```python
# ❌ 悪い例: 例外を握りつぶす
try:
    result = risky_operation()
except Exception:
    pass  # 何もしない

# ❌ 悪い例: ログだけ出して握りつぶす
try:
    result = risky_operation()
except Exception as e:
    logger.error(f"Error: {e}")
    # 処理が続行されるが、呼び出し元はエラーを知らない

# ✅ 良い例: 適切に処理してから再送出
try:
    result = risky_operation()
except Exception as e:
    logger.error("Operation failed", exc_info=True)
    # クリーンアップ処理
    cleanup_resources()
    raise  # 再送出
```

**原則**: 例外を完全に処理できない場合は、必ず再送出する。

### 2.4 Specific Exceptions（具体的な例外）

```python
# ❌ 悪い例: 汎用的な例外をキャッチ
try:
    result = process()
except Exception as e:
    handle_error(e)

# ✅ 良い例: 具体的な例外をキャッチ
try:
    result = process()
except ValidationError as e:
    # バリデーションエラー固有の処理
    return {"error": "Invalid input", "details": e.details}
except NotFoundError as e:
    # リソース不存在の処理
    return {"error": "Resource not found", "resource_id": e.resource_id}
except AIProviderError as e:
    # AI関連エラーの処理
    if e.is_retryable:
        return await retry_with_backoff(process)
    raise
```

**原則**: できるだけ具体的な例外をキャッチし、それぞれに適した処理を行う。

---

## 3. エラー階層設計

### 3.1 エラークラスの継承構造

```
Exception
└── AppError (アプリケーション基底エラー)
    ├── ValidationError (入力検証エラー)
    │   ├── FieldValidationError
    │   └── SchemaValidationError
    │
    ├── AuthenticationError (認証エラー)
    │   ├── InvalidCredentialsError
    │   ├── TokenExpiredError
    │   └── MFARequiredError
    │
    ├── AuthorizationError (認可エラー)
    │   ├── PermissionDeniedError
    │   └── ResourceAccessDeniedError
    │
    ├── NotFoundError (リソース不存在)
    │   ├── UserNotFoundError
    │   ├── InterviewNotFoundError
    │   └── ProjectNotFoundError
    │
    ├── ConflictError (競合エラー)
    │   ├── DuplicateResourceError
    │   └── ConcurrentModificationError
    │
    ├── ExternalServiceError (外部サービスエラー)
    │   ├── AIProviderError
    │   ├── SpeechServiceError
    │   ├── StorageServiceError
    │   └── DatabaseError
    │
    └── InternalError (内部エラー)
        └── ConfigurationError
```

### 3.2 各エラー種類の特性

| エラー種類 | HTTPステータス | リトライ可能 | ユーザーへの表示 |
|-----------|---------------|-------------|----------------|
| ValidationError | 400 | ❌ | 具体的なフィールドエラー |
| AuthenticationError | 401 | ❌ | 再ログインを促す |
| AuthorizationError | 403 | ❌ | 権限不足を通知 |
| NotFoundError | 404 | ❌ | リソースが見つからない |
| ConflictError | 409 | ❌ | 操作の競合を通知 |
| RateLimitError | 429 | ✅ | 待機を促す |
| ExternalServiceError | 502/503 | ✅ | 一時的な問題を通知 |
| InternalError | 500 | ❌ | 一般的なエラーメッセージ |

---

## 4. エラーコード体系

### 4.1 エラーコードの設計

エラーコードは、問題を一意に識別するための文字列です。

```python
class ErrorCode(str, Enum):
    """システム全体で使用するエラーコード

    命名規則: {カテゴリ}_{詳細}
    例: AUTH_INVALID_CREDENTIALS, AI_RATE_LIMIT
    """

    # === 認証関連 (AUTH_) ===
    AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_TOKEN_INVALID = "AUTH_TOKEN_INVALID"
    AUTH_MFA_REQUIRED = "AUTH_MFA_REQUIRED"
    AUTH_SESSION_EXPIRED = "AUTH_SESSION_EXPIRED"

    # === 認可関連 (AUTHZ_) ===
    AUTHZ_PERMISSION_DENIED = "AUTHZ_PERMISSION_DENIED"
    AUTHZ_RESOURCE_ACCESS_DENIED = "AUTHZ_RESOURCE_ACCESS_DENIED"
    AUTHZ_ORGANIZATION_MISMATCH = "AUTHZ_ORGANIZATION_MISMATCH"

    # === バリデーション関連 (VALIDATION_) ===
    VALIDATION_REQUIRED_FIELD = "VALIDATION_REQUIRED_FIELD"
    VALIDATION_INVALID_FORMAT = "VALIDATION_INVALID_FORMAT"
    VALIDATION_FIELD_TOO_LONG = "VALIDATION_FIELD_TOO_LONG"
    VALIDATION_FIELD_TOO_SHORT = "VALIDATION_FIELD_TOO_SHORT"
    VALIDATION_INVALID_ENUM = "VALIDATION_INVALID_ENUM"

    # === リソース関連 (RESOURCE_) ===
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    RESOURCE_LOCKED = "RESOURCE_LOCKED"

    # === AI関連 (AI_) ===
    AI_PROVIDER_ERROR = "AI_PROVIDER_ERROR"
    AI_RATE_LIMIT = "AI_RATE_LIMIT"
    AI_TIMEOUT = "AI_TIMEOUT"
    AI_CONTENT_FILTERED = "AI_CONTENT_FILTERED"
    AI_MODEL_UNAVAILABLE = "AI_MODEL_UNAVAILABLE"

    # === 音声関連 (SPEECH_) ===
    SPEECH_RECOGNITION_FAILED = "SPEECH_RECOGNITION_FAILED"
    SPEECH_SYNTHESIS_FAILED = "SPEECH_SYNTHESIS_FAILED"
    SPEECH_UNSUPPORTED_LANGUAGE = "SPEECH_UNSUPPORTED_LANGUAGE"

    # === インタビュー関連 (INTERVIEW_) ===
    INTERVIEW_ALREADY_STARTED = "INTERVIEW_ALREADY_STARTED"
    INTERVIEW_ALREADY_COMPLETED = "INTERVIEW_ALREADY_COMPLETED"
    INTERVIEW_NOT_STARTED = "INTERVIEW_NOT_STARTED"
    INTERVIEW_SESSION_EXPIRED = "INTERVIEW_SESSION_EXPIRED"

    # === システム関連 (SYSTEM_) ===
    SYSTEM_INTERNAL_ERROR = "SYSTEM_INTERNAL_ERROR"
    SYSTEM_SERVICE_UNAVAILABLE = "SYSTEM_SERVICE_UNAVAILABLE"
    SYSTEM_RATE_LIMIT = "SYSTEM_RATE_LIMIT"
    SYSTEM_MAINTENANCE = "SYSTEM_MAINTENANCE"
```

### 4.2 エラーコードのドキュメント化

```python
# エラーコードの詳細情報を定義
ERROR_CODE_METADATA = {
    ErrorCode.AUTH_INVALID_CREDENTIALS: {
        "message_ja": "メールアドレスまたはパスワードが正しくありません",
        "message_en": "Invalid email or password",
        "http_status": 401,
        "is_retryable": False,
        "user_action": "認証情報を確認して再試行してください",
    },
    ErrorCode.AI_RATE_LIMIT: {
        "message_ja": "AIサービスのレート制限に達しました",
        "message_en": "AI service rate limit exceeded",
        "http_status": 429,
        "is_retryable": True,
        "user_action": "しばらく待ってから再試行してください",
    },
    # ... 他のエラーコード
}
```

---

## 5. 実装詳細

### 5.1 基底エラークラス

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass
class ErrorDetail:
    """エラーの詳細情報を表現するデータクラス

    主に複数のバリデーションエラーを格納するために使用します。

    Attributes:
        field: エラーが発生したフィールド名
        message: エラーメッセージ
        code: エラーコード
        value: エラーを引き起こした値（オプション）
    """
    field: str
    message: str
    code: str
    value: Any = None


@dataclass
class AppError(Exception):
    """アプリケーション基底エラークラス

    全てのカスタムエラーはこのクラスを継承します。

    設計思想:
    - 一貫したエラー構造
    - HTTPステータスコードとの紐付け
    - リトライ可能性の判定
    - 原因となった例外の保持

    Attributes:
        message: ユーザー向けエラーメッセージ
        code: エラーコード（ErrorCode enum）
        status_code: HTTPステータスコード
        details: エラー詳細のリスト
        cause: 原因となった例外
        retry_after: リトライまでの待機秒数
        is_retryable: リトライ可能かどうか
    """
    message: str
    code: ErrorCode = ErrorCode.SYSTEM_INTERNAL_ERROR
    status_code: int = 500
    details: list[ErrorDetail] = field(default_factory=list)
    cause: Exception | None = None
    retry_after: int | None = None
    is_retryable: bool = False

    def __str__(self) -> str:
        """エラーの文字列表現"""
        return f"[{self.code}] {self.message}"

    def to_dict(self) -> dict:
        """APIレスポンス用の辞書形式に変換

        Returns:
            エラー情報を含む辞書
        """
        result = {
            "error": {
                "code": self.code.value,
                "message": self.message,
            }
        }

        if self.details:
            result["error"]["details"] = [
                {
                    "field": d.field,
                    "message": d.message,
                    "code": d.code,
                }
                for d in self.details
            ]

        if self.retry_after:
            result["error"]["retry_after"] = self.retry_after

        return result

    def with_cause(self, cause: Exception) -> "AppError":
        """原因となった例外を設定

        メソッドチェーン可能なビルダーパターン。

        Args:
            cause: 原因となった例外

        Returns:
            自身への参照
        """
        self.cause = cause
        return self
```

### 5.2 具体的なエラークラス

```python
@dataclass
class ValidationError(AppError):
    """入力値バリデーションエラー

    ユーザーからの入力が不正な場合に使用します。
    複数のフィールドエラーを同時に返すことができます。

    使用例:
        errors = []
        if not data.email:
            errors.append(ErrorDetail(
                field="email",
                message="メールアドレスは必須です",
                code="required"
            ))
        if len(data.name) > 100:
            errors.append(ErrorDetail(
                field="name",
                message="名前は100文字以内で入力してください",
                code="too_long",
                value=len(data.name)
            ))
        if errors:
            raise ValidationError(details=errors)
    """
    message: str = "入力値が不正です"
    code: ErrorCode = ErrorCode.VALIDATION_REQUIRED_FIELD
    status_code: int = 400

    def add_field_error(
        self,
        field: str,
        message: str,
        code: str = "invalid",
        value: Any = None
    ) -> "ValidationError":
        """フィールドエラーを追加

        Args:
            field: フィールド名
            message: エラーメッセージ
            code: エラーコード
            value: エラー値

        Returns:
            自身への参照（メソッドチェーン用）
        """
        self.details.append(ErrorDetail(
            field=field,
            message=message,
            code=code,
            value=value
        ))
        return self


@dataclass
class NotFoundError(AppError):
    """リソースが見つからないエラー

    データベースに存在しないリソースへのアクセス時に使用。

    使用例:
        interview = await repo.get(interview_id)
        if not interview:
            raise NotFoundError(
                resource_type="interview",
                resource_id=interview_id
            )
    """
    message: str = "リソースが見つかりません"
    code: ErrorCode = ErrorCode.RESOURCE_NOT_FOUND
    status_code: int = 404
    resource_type: str = ""
    resource_id: str = ""

    def __post_init__(self):
        if self.resource_type and self.resource_id:
            self.message = f"{self.resource_type}（ID: {self.resource_id}）が見つかりません"


@dataclass
class AuthenticationError(AppError):
    """認証エラー

    ログイン失敗、トークン無効/期限切れなどで使用。

    使用例:
        if not verify_password(password, user.hashed_password):
            raise AuthenticationError(
                code=ErrorCode.AUTH_INVALID_CREDENTIALS
            )
    """
    message: str = "認証に失敗しました"
    code: ErrorCode = ErrorCode.AUTH_INVALID_CREDENTIALS
    status_code: int = 401


@dataclass
class AuthorizationError(AppError):
    """認可エラー

    アクセス権限がない場合に使用。

    使用例:
        if not user.has_permission("interview:create"):
            raise AuthorizationError(
                code=ErrorCode.AUTHZ_PERMISSION_DENIED,
                required_permission="interview:create"
            )
    """
    message: str = "アクセス権限がありません"
    code: ErrorCode = ErrorCode.AUTHZ_PERMISSION_DENIED
    status_code: int = 403
    required_permission: str = ""


@dataclass
class ConflictError(AppError):
    """競合エラー

    リソースの重複、同時更新の競合などで使用。

    使用例:
        existing = await repo.get_by_email(email)
        if existing:
            raise ConflictError(
                code=ErrorCode.RESOURCE_ALREADY_EXISTS,
                conflicting_field="email"
            )
    """
    message: str = "リソースが競合しています"
    code: ErrorCode = ErrorCode.RESOURCE_CONFLICT
    status_code: int = 409
    conflicting_field: str = ""


@dataclass
class ExternalServiceError(AppError):
    """外部サービスエラー

    AI、音声認識、ストレージなど外部サービスのエラー。
    多くの場合リトライ可能です。
    """
    message: str = "外部サービスでエラーが発生しました"
    code: ErrorCode = ErrorCode.SYSTEM_SERVICE_UNAVAILABLE
    status_code: int = 502
    service_name: str = ""
    is_retryable: bool = True


@dataclass
class AIProviderError(ExternalServiceError):
    """AIプロバイダーエラー

    LLMサービス（Azure OpenAI、Bedrock等）のエラー。

    使用例:
        try:
            response = await ai.chat(messages)
        except RateLimitError as e:
            raise AIProviderError(
                code=ErrorCode.AI_RATE_LIMIT,
                retry_after=e.retry_after
            )
    """
    message: str = "AIサービスでエラーが発生しました"
    code: ErrorCode = ErrorCode.AI_PROVIDER_ERROR
    service_name: str = "ai_provider"
    model: str = ""
    provider: str = ""


@dataclass
class RateLimitError(AppError):
    """レート制限エラー

    APIのレート制限に達した場合に使用。
    retry_afterで再試行までの待機時間を通知。
    """
    message: str = "リクエスト数の上限に達しました"
    code: ErrorCode = ErrorCode.SYSTEM_RATE_LIMIT
    status_code: int = 429
    is_retryable: bool = True
    limit: int = 0
    remaining: int = 0
    reset_at: datetime | None = None
```

---

## 6. リトライ戦略

### 6.1 リトライの基本概念

```
┌─────────────────────────────────────────────────────────────────┐
│                    リトライ戦略の選択                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐                                            │
│  │ エラー発生      │                                            │
│  └────────┬────────┘                                            │
│           ▼                                                     │
│  ┌─────────────────┐     ❌                                     │
│  │ リトライ可能？  │────────────▶ エラーを返す                  │
│  └────────┬────────┘                                            │
│           │ ✅                                                  │
│           ▼                                                     │
│  ┌─────────────────┐     ❌                                     │
│  │ 最大回数内？    │────────────▶ エラーを返す                  │
│  └────────┬────────┘                                            │
│           │ ✅                                                  │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ バックオフ待機  │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐     ❌                                     │
│  │ 再試行          │────────────▶ 次のリトライへ               │
│  └────────┬────────┘                                            │
│           │ ✅                                                  │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ 成功を返す      │                                            │
│  └─────────────────┘                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 バックオフアルゴリズム

```python
import asyncio
import random
from dataclasses import dataclass
from typing import Callable, TypeVar, Awaitable

T = TypeVar("T")


@dataclass
class RetryConfig:
    """リトライ設定

    Attributes:
        max_retries: 最大リトライ回数
        base_delay: 初回待機時間（秒）
        max_delay: 最大待機時間（秒）
        exponential_base: 指数バックオフの基数
        jitter: ジッター（ランダム遅延）の有無
    """
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


def calculate_backoff(
    attempt: int,
    config: RetryConfig,
) -> float:
    """指数バックオフ + ジッターを計算

    アルゴリズム:
    delay = min(base_delay * (exponential_base ^ attempt), max_delay)
    if jitter:
        delay = delay * random(0.5, 1.5)

    例（base_delay=1, exponential_base=2）:
    - attempt 1: 1秒 * 2^1 = 2秒
    - attempt 2: 1秒 * 2^2 = 4秒
    - attempt 3: 1秒 * 2^3 = 8秒

    ジッターを加えると、複数クライアントが同時にリトライする
    「サンダリングハード問題」を回避できます。

    Args:
        attempt: 現在の試行回数（1から始まる）
        config: リトライ設定

    Returns:
        待機時間（秒）
    """
    delay = min(
        config.base_delay * (config.exponential_base ** attempt),
        config.max_delay
    )

    if config.jitter:
        # 0.5〜1.5倍のランダムなジッターを追加
        jitter_factor = 0.5 + random.random()
        delay *= jitter_factor

    return delay


async def retry_with_backoff(
    func: Callable[[], Awaitable[T]],
    config: RetryConfig = RetryConfig(),
    retryable_exceptions: tuple = (ExternalServiceError,),
) -> T:
    """指数バックオフ付きリトライを実行

    使用例:
        result = await retry_with_backoff(
            lambda: ai_provider.chat(messages),
            config=RetryConfig(max_retries=3),
            retryable_exceptions=(AIProviderError, TimeoutError)
        )

    Args:
        func: リトライ対象の非同期関数
        config: リトライ設定
        retryable_exceptions: リトライ対象の例外タプル

    Returns:
        関数の戻り値

    Raises:
        最後のリトライでも失敗した場合、その例外を送出
    """
    last_exception = None

    for attempt in range(config.max_retries + 1):
        try:
            return await func()
        except retryable_exceptions as e:
            last_exception = e

            if attempt == config.max_retries:
                # 最大リトライ回数に達した
                logger.warning(
                    f"Max retries ({config.max_retries}) exceeded",
                    extra={
                        "attempt": attempt + 1,
                        "error": str(e),
                    }
                )
                raise

            # 待機時間を計算
            delay = calculate_backoff(attempt + 1, config)

            logger.info(
                f"Retrying after {delay:.2f}s (attempt {attempt + 1}/{config.max_retries})",
                extra={
                    "attempt": attempt + 1,
                    "delay_seconds": delay,
                    "error": str(e),
                }
            )

            await asyncio.sleep(delay)

    raise last_exception
```

### 6.3 リトライデコレータ

```python
from functools import wraps

def with_retry(
    max_retries: int = 3,
    retryable_exceptions: tuple = (ExternalServiceError,),
    base_delay: float = 1.0,
):
    """リトライ機能を追加するデコレータ

    使用例:
        @with_retry(max_retries=3, retryable_exceptions=(AIProviderError,))
        async def call_ai(messages):
            return await ai_provider.chat(messages)

    Args:
        max_retries: 最大リトライ回数
        retryable_exceptions: リトライ対象の例外
        base_delay: 初回待機時間
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            config = RetryConfig(
                max_retries=max_retries,
                base_delay=base_delay,
            )
            return await retry_with_backoff(
                lambda: func(*args, **kwargs),
                config=config,
                retryable_exceptions=retryable_exceptions,
            )
        return wrapper
    return decorator
```

---

## 7. サーキットブレーカー

### 7.1 サーキットブレーカーとは

外部サービスの障害時に、連続的なリクエストを防ぎ、システム全体の安定性を保つパターンです。

```
┌─────────────────────────────────────────────────────────────────┐
│                サーキットブレーカーの状態遷移                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                    ┌─────────────┐                              │
│         成功       │             │ 失敗閾値超過                 │
│    ┌───────────────│   CLOSED    │───────────────┐              │
│    │               │  (正常動作) │               │              │
│    │               └─────────────┘               │              │
│    │                                             ▼              │
│    │                                      ┌─────────────┐       │
│    │                                      │             │       │
│    │                                      │    OPEN     │       │
│    │                                      │(即座に失敗) │       │
│    │                                      └──────┬──────┘       │
│    │                                             │              │
│    │                           タイムアウト後    │              │
│    │                                             ▼              │
│    │                                      ┌─────────────┐       │
│    │               成功                   │             │       │
│    └──────────────────────────────────────│ HALF-OPEN   │       │
│                                           │ (試験的許可)│       │
│                               失敗        └──────┬──────┘       │
│                               ┌──────────────────┘              │
│                               ▼                                 │
│                        ┌─────────────┐                          │
│                        │    OPEN     │                          │
│                        └─────────────┘                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 実装

```python
import asyncio
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, Awaitable, TypeVar

T = TypeVar("T")


class CircuitState(Enum):
    """サーキットブレーカーの状態"""
    CLOSED = "closed"      # 正常動作中
    OPEN = "open"          # 遮断中（即座に失敗）
    HALF_OPEN = "half_open"  # 試験的に許可


@dataclass
class CircuitBreakerConfig:
    """サーキットブレーカー設定

    Attributes:
        failure_threshold: OPEN に遷移する失敗回数の閾値
        success_threshold: CLOSED に遷移する成功回数の閾値
        timeout_seconds: OPEN から HALF_OPEN に遷移するまでの秒数
        monitored_exceptions: 監視対象の例外タイプ
    """
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: float = 30.0
    monitored_exceptions: tuple = (Exception,)


@dataclass
class CircuitBreaker:
    """サーキットブレーカー実装

    外部サービスの障害を検知し、システムを保護します。

    使用例:
        breaker = CircuitBreaker(
            name="ai_provider",
            config=CircuitBreakerConfig(failure_threshold=3)
        )

        try:
            result = await breaker.call(lambda: ai.chat(messages))
        except CircuitOpenError:
            # サーキットが開いている場合のフォールバック
            return fallback_response()
    """
    name: str
    config: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: datetime | None = None
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def call(
        self,
        func: Callable[[], Awaitable[T]],
    ) -> T:
        """サーキットブレーカーを通して関数を呼び出す

        Args:
            func: 呼び出す非同期関数

        Returns:
            関数の戻り値

        Raises:
            CircuitOpenError: サーキットが開いている場合
            その他: 関数が発生させた例外
        """
        async with self._lock:
            # 状態チェック
            if self.state == CircuitState.OPEN:
                # タイムアウト経過をチェック
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    logger.info(
                        f"Circuit {self.name} transitioning to HALF_OPEN",
                        extra={"circuit_name": self.name}
                    )
                else:
                    raise CircuitOpenError(
                        message=f"Circuit {self.name} is OPEN",
                        circuit_name=self.name,
                        retry_after=self._time_until_retry()
                    )

        # 関数を実行
        try:
            result = await func()
            await self._on_success()
            return result
        except self.config.monitored_exceptions as e:
            await self._on_failure()
            raise

    async def _on_success(self) -> None:
        """成功時の処理"""
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    logger.info(
                        f"Circuit {self.name} CLOSED (recovered)",
                        extra={"circuit_name": self.name}
                    )
            elif self.state == CircuitState.CLOSED:
                self.failure_count = 0  # 成功でカウンターをリセット

    async def _on_failure(self) -> None:
        """失敗時の処理"""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            if self.state == CircuitState.HALF_OPEN:
                # HALF_OPEN で失敗 → OPEN に戻る
                self.state = CircuitState.OPEN
                logger.warning(
                    f"Circuit {self.name} back to OPEN",
                    extra={
                        "circuit_name": self.name,
                        "failure_count": self.failure_count,
                    }
                )
            elif (
                self.state == CircuitState.CLOSED
                and self.failure_count >= self.config.failure_threshold
            ):
                # 閾値超過 → OPEN に遷移
                self.state = CircuitState.OPEN
                logger.warning(
                    f"Circuit {self.name} OPEN (failures: {self.failure_count})",
                    extra={
                        "circuit_name": self.name,
                        "failure_count": self.failure_count,
                    }
                )

    def _should_attempt_reset(self) -> bool:
        """HALF_OPEN への遷移をすべきか判定"""
        if not self.last_failure_time:
            return True
        elapsed = datetime.now() - self.last_failure_time
        return elapsed.total_seconds() >= self.config.timeout_seconds

    def _time_until_retry(self) -> float:
        """次のリトライまでの秒数"""
        if not self.last_failure_time:
            return 0
        elapsed = datetime.now() - self.last_failure_time
        remaining = self.config.timeout_seconds - elapsed.total_seconds()
        return max(0, remaining)


@dataclass
class CircuitOpenError(AppError):
    """サーキットが開いているエラー"""
    message: str = "サービスが一時的に利用できません"
    code: ErrorCode = ErrorCode.SYSTEM_SERVICE_UNAVAILABLE
    status_code: int = 503
    circuit_name: str = ""
    is_retryable: bool = True
```

### 7.3 サービスでの使用

```python
class AIDialogueService:
    """AI対話サービス"""

    def __init__(self):
        self.circuit_breaker = CircuitBreaker(
            name="ai_provider",
            config=CircuitBreakerConfig(
                failure_threshold=5,
                success_threshold=2,
                timeout_seconds=30,
                monitored_exceptions=(AIProviderError, TimeoutError),
            )
        )

    async def get_response(self, messages: list[Message]) -> str:
        try:
            return await self.circuit_breaker.call(
                lambda: self.ai_provider.chat(messages)
            )
        except CircuitOpenError:
            # フォールバック応答
            logger.warning("Using fallback response due to circuit open")
            return "申し訳ありません。現在サービスが混み合っています。"
```

---

## 8. API エラーレスポンス

### 8.1 エラーレスポンス形式

```json
{
  "error": {
    "code": "VALIDATION_REQUIRED_FIELD",
    "message": "入力値が不正です",
    "details": [
      {
        "field": "email",
        "message": "メールアドレスは必須です",
        "code": "required"
      },
      {
        "field": "name",
        "message": "名前は100文字以内で入力してください",
        "code": "too_long"
      }
    ],
    "request_id": "req-abc123",
    "timestamp": "2026-02-08T10:30:45.123Z"
  }
}
```

### 8.2 FastAPI での実装

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

app = FastAPI()


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """アプリケーションエラーのハンドラー

    AppError を継承した全てのエラーを統一形式でレスポンス。
    """
    # ログ出力
    logger.error(
        f"AppError: {exc.code}",
        extra={
            "error_code": exc.code.value,
            "message": exc.message,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=exc.cause,
    )

    response_data = exc.to_dict()
    response_data["error"]["request_id"] = correlation_id_ctx.get()
    response_data["error"]["timestamp"] = datetime.now(timezone.utc).isoformat()

    response = JSONResponse(
        status_code=exc.status_code,
        content=response_data,
    )

    # Retry-After ヘッダー（レート制限時）
    if exc.retry_after:
        response.headers["Retry-After"] = str(exc.retry_after)

    return response


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Pydantic バリデーションエラーのハンドラー

    FastAPI/Pydantic のバリデーションエラーを統一形式に変換。
    """
    details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        details.append(ErrorDetail(
            field=field,
            message=error["msg"],
            code=error["type"],
        ))

    app_error = ValidationError(details=details)
    return await app_error_handler(request, app_error)


@app.exception_handler(Exception)
async def unhandled_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """未処理例外のハンドラー

    予期しない例外をキャッチし、内部情報を隠蔽。
    """
    # 詳細はログに出力（本番環境では Sentry 等に送信）
    logger.critical(
        "Unhandled exception",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
        },
        exc_info=True,
    )

    # ユーザーには一般的なメッセージのみ返す
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "SYSTEM_INTERNAL_ERROR",
                "message": "予期しないエラーが発生しました。しばらくしてから再試行してください。",
                "request_id": correlation_id_ctx.get(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        },
    )
```

---

## 9. フロントエンドでのエラー処理

### 9.1 エラー型定義（TypeScript）

```typescript
// types/error.ts

/**
 * APIエラーレスポンスの型定義
 */
export interface APIErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Array<{
      field: string;
      message: string;
      code: string;
    }>;
    request_id?: string;
    timestamp?: string;
    retry_after?: number;
  };
}

/**
 * エラーコードの列挙
 * バックエンドと同期を保つこと
 */
export enum ErrorCode {
  // 認証
  AUTH_INVALID_CREDENTIALS = 'AUTH_INVALID_CREDENTIALS',
  AUTH_TOKEN_EXPIRED = 'AUTH_TOKEN_EXPIRED',

  // バリデーション
  VALIDATION_REQUIRED_FIELD = 'VALIDATION_REQUIRED_FIELD',
  VALIDATION_INVALID_FORMAT = 'VALIDATION_INVALID_FORMAT',

  // リソース
  RESOURCE_NOT_FOUND = 'RESOURCE_NOT_FOUND',

  // システム
  SYSTEM_RATE_LIMIT = 'SYSTEM_RATE_LIMIT',
  SYSTEM_SERVICE_UNAVAILABLE = 'SYSTEM_SERVICE_UNAVAILABLE',
}

/**
 * ユーザー向けエラーメッセージ
 */
export const ERROR_MESSAGES: Record<ErrorCode, string> = {
  [ErrorCode.AUTH_INVALID_CREDENTIALS]:
    'メールアドレスまたはパスワードが正しくありません',
  [ErrorCode.AUTH_TOKEN_EXPIRED]:
    'セッションの有効期限が切れました。再度ログインしてください',
  [ErrorCode.VALIDATION_REQUIRED_FIELD]:
    '必須項目を入力してください',
  [ErrorCode.VALIDATION_INVALID_FORMAT]:
    '入力形式が正しくありません',
  [ErrorCode.RESOURCE_NOT_FOUND]:
    'リソースが見つかりませんでした',
  [ErrorCode.SYSTEM_RATE_LIMIT]:
    'リクエストが多すぎます。しばらくお待ちください',
  [ErrorCode.SYSTEM_SERVICE_UNAVAILABLE]:
    'サービスが一時的に利用できません',
};
```

### 9.2 エラーハンドリングフック

```typescript
// hooks/useApiError.ts

import { useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { APIErrorResponse, ErrorCode, ERROR_MESSAGES } from '@/types/error';

/**
 * APIエラーを処理するカスタムフック
 *
 * 使用例:
 * const { handleError } = useApiError();
 *
 * try {
 *   await api.createInterview(data);
 * } catch (error) {
 *   handleError(error);
 * }
 */
export function useApiError() {
  const router = useRouter();

  const handleError = useCallback((error: unknown) => {
    // APIエラーレスポンスの場合
    if (isAPIError(error)) {
      const { code, message, retry_after } = error.error;

      switch (code) {
        case ErrorCode.AUTH_TOKEN_EXPIRED:
        case ErrorCode.AUTH_INVALID_CREDENTIALS:
          // 認証エラー: ログインページにリダイレクト
          toast.error(ERROR_MESSAGES[code as ErrorCode] || message);
          router.push('/login');
          break;

        case ErrorCode.SYSTEM_RATE_LIMIT:
          // レート制限: 待機時間を表示
          toast.error(
            `${message}${retry_after ? ` (${retry_after}秒後に再試行可能)` : ''}`
          );
          break;

        case ErrorCode.VALIDATION_REQUIRED_FIELD:
        case ErrorCode.VALIDATION_INVALID_FORMAT:
          // バリデーションエラー: 詳細を表示
          if (error.error.details) {
            error.error.details.forEach((detail) => {
              toast.error(`${detail.field}: ${detail.message}`);
            });
          } else {
            toast.error(message);
          }
          break;

        default:
          // その他のエラー
          toast.error(
            ERROR_MESSAGES[code as ErrorCode] || message || 'エラーが発生しました'
          );
      }
    } else if (error instanceof Error) {
      // ネットワークエラー等
      toast.error('通信エラーが発生しました。ネットワーク接続を確認してください');
    } else {
      toast.error('予期しないエラーが発生しました');
    }
  }, [router]);

  return { handleError };
}

/**
 * APIエラーレスポンスかどうかを判定
 */
function isAPIError(error: unknown): error is APIErrorResponse {
  return (
    typeof error === 'object' &&
    error !== null &&
    'error' in error &&
    typeof (error as APIErrorResponse).error === 'object'
  );
}
```

### 9.3 フォームでのエラー表示

```typescript
// components/InterviewForm.tsx

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useApiError } from '@/hooks/useApiError';

const schema = z.object({
  title: z.string().min(1, '必須項目です').max(100, '100文字以内で入力してください'),
  templateId: z.string().uuid('テンプレートを選択してください'),
  language: z.enum(['ja', 'en', 'zh']),
});

type FormData = z.infer<typeof schema>;

export function InterviewForm() {
  const { handleError } = useApiError();

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    try {
      await api.createInterview(data);
    } catch (error) {
      // バリデーションエラーの場合、フィールドにエラーを設定
      if (isAPIError(error) && error.error.details) {
        error.error.details.forEach((detail) => {
          setError(detail.field as keyof FormData, {
            type: 'server',
            message: detail.message,
          });
        });
      } else {
        handleError(error);
      }
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div>
        <label>タイトル</label>
        <input {...register('title')} />
        {errors.title && (
          <span className="text-red-500">{errors.title.message}</span>
        )}
      </div>
      {/* ... その他のフィールド */}
    </form>
  );
}
```

---

## 10. グローバルエラーハンドリング

### 10.1 エラーバウンダリ（React）

```typescript
// components/ErrorBoundary.tsx

import React from 'react';
import { Button } from '@/components/ui/button';

interface Props {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

/**
 * エラーバウンダリコンポーネント
 *
 * 子コンポーネントで発生したエラーをキャッチし、
 * フォールバックUIを表示します。
 *
 * 使用例:
 * <ErrorBoundary>
 *   <InterviewPage />
 * </ErrorBoundary>
 */
export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // エラーログをサーバーに送信
    console.error('ErrorBoundary caught:', error, errorInfo);

    // 本番環境では Sentry 等に送信
    // Sentry.captureException(error, { extra: errorInfo });
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex flex-col items-center justify-center min-h-screen">
          <h1 className="text-2xl font-bold mb-4">エラーが発生しました</h1>
          <p className="text-gray-600 mb-6">
            申し訳ありません。予期しないエラーが発生しました。
          </p>
          <div className="flex gap-4">
            <Button onClick={this.handleRetry}>
              再試行
            </Button>
            <Button variant="outline" onClick={() => window.location.href = '/'}>
              ホームに戻る
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### 10.2 Next.js エラーページ

```typescript
// app/error.tsx
'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // エラーをログサービスに送信
    console.error('Page error:', error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <h1 className="text-2xl font-bold mb-4">問題が発生しました</h1>
      <p className="text-gray-600 mb-6">
        ページの読み込み中にエラーが発生しました。
      </p>
      <Button onClick={reset}>再試行</Button>
    </div>
  );
}
```

---

## 11. テスト方法

### 11.1 エラークラスのユニットテスト

```python
# tests/test_errors.py

import pytest
from grc_backend.core.errors import (
    AppError,
    ValidationError,
    NotFoundError,
    ErrorCode,
    ErrorDetail,
)


class TestAppError:
    """AppError基底クラスのテスト"""

    def test_error_creation(self):
        """エラー生成のテスト"""
        error = AppError(
            message="Test error",
            code=ErrorCode.SYSTEM_INTERNAL_ERROR,
            status_code=500,
        )

        assert error.message == "Test error"
        assert error.code == ErrorCode.SYSTEM_INTERNAL_ERROR
        assert error.status_code == 500

    def test_to_dict(self):
        """辞書変換のテスト"""
        error = AppError(
            message="Test error",
            code=ErrorCode.SYSTEM_INTERNAL_ERROR,
        )

        result = error.to_dict()

        assert result["error"]["code"] == "SYSTEM_INTERNAL_ERROR"
        assert result["error"]["message"] == "Test error"


class TestValidationError:
    """ValidationErrorのテスト"""

    def test_with_details(self):
        """詳細情報付きエラーのテスト"""
        error = ValidationError()
        error.add_field_error(
            field="email",
            message="Invalid email format",
            code="invalid_format"
        )

        assert len(error.details) == 1
        assert error.details[0].field == "email"

    def test_to_dict_with_details(self):
        """詳細情報を含む辞書変換のテスト"""
        error = ValidationError(
            details=[
                ErrorDetail(
                    field="email",
                    message="Required",
                    code="required"
                )
            ]
        )

        result = error.to_dict()

        assert len(result["error"]["details"]) == 1
        assert result["error"]["details"][0]["field"] == "email"


class TestNotFoundError:
    """NotFoundErrorのテスト"""

    def test_message_generation(self):
        """メッセージ自動生成のテスト"""
        error = NotFoundError(
            resource_type="interview",
            resource_id="int-123"
        )

        assert "interview" in error.message
        assert "int-123" in error.message
```

### 11.2 APIエラーハンドリングのテスト

```python
# tests/test_api_errors.py

import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
class TestAPIErrorHandling:
    """APIエラーハンドリングの統合テスト"""

    async def test_validation_error_response(self, client: AsyncClient):
        """バリデーションエラーのレスポンス形式テスト"""
        response = await client.post(
            "/api/v1/interviews",
            json={}  # 必須フィールドなし
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "VALIDATION_REQUIRED_FIELD"
        assert "details" in data["error"]

    async def test_not_found_error_response(self, client: AsyncClient):
        """NotFoundエラーのレスポンス形式テスト"""
        response = await client.get("/api/v1/interviews/non-existent-id")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"

    async def test_rate_limit_response(self, client: AsyncClient):
        """レート制限のレスポンス形式テスト"""
        # レート制限を発動させる
        for _ in range(101):
            await client.get("/api/v1/health")

        response = await client.get("/api/v1/health")

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "Retry-After" in response.headers
```

---

## 12. ベストプラクティス

### 12.1 エラー処理チェックリスト

```markdown
## エラー処理実装チェックリスト

### 設計
- [ ] エラー階層が適切に設計されている
- [ ] エラーコードが一意で意味がある
- [ ] HTTPステータスコードが正しく対応している

### 実装
- [ ] 具体的な例外をキャッチしている
- [ ] 例外を握りつぶしていない
- [ ] 原因となった例外を保持している

### セキュリティ
- [ ] 内部エラーの詳細が外部に露出しない
- [ ] スタックトレースが本番で表示されない
- [ ] エラーメッセージに機密情報がない

### ログ
- [ ] エラー時に適切なログが出力される
- [ ] 相関IDで追跡可能
- [ ] スタックトレースがログに含まれる

### ユーザー体験
- [ ] ユーザーに分かりやすいメッセージを表示
- [ ] リトライ可能な場合は案内している
- [ ] フォームエラーは該当フィールドに表示
```

### 12.2 Do's and Don'ts

#### ✅ Do's

```python
# 1. 具体的な例外を使用
raise ValidationError(
    code=ErrorCode.VALIDATION_REQUIRED_FIELD,
    details=[
        ErrorDetail(field="email", message="Required", code="required")
    ]
)

# 2. 原因となった例外を保持
try:
    result = await external_service.call()
except ServiceError as e:
    raise ExternalServiceError(
        message="External service failed",
        service_name="payment",
    ).with_cause(e)

# 3. リトライ可能性を明示
raise AIProviderError(
    message="Rate limit exceeded",
    is_retryable=True,
    retry_after=60,
)

# 4. ログにコンテキストを含める
logger.error(
    "Operation failed",
    extra={
        "operation": "create_interview",
        "user_id": user_id,
        "error_code": error.code.value,
    },
    exc_info=True,
)
```

#### ❌ Don'ts

```python
# 1. 汎用的な例外
raise Exception("Something went wrong")  # ❌

# 2. 例外の握りつぶし
try:
    risky_operation()
except Exception:
    pass  # ❌

# 3. 内部情報の露出
raise HTTPException(
    status_code=500,
    detail=f"Database error: {str(e)}"  # ❌ 内部情報が露出
)

# 4. 曖昧なエラーメッセージ
raise AppError(message="Error")  # ❌ 何が起きたか分からない
```

---

## 付録

### A. 関連ドキュメント

- [ログ管理仕様書](./LOGGING.md)
- [セキュリティ仕様書](./SECURITY.md)
- [API仕様書](../api/README.md)

### B. 参考資料

- [Microsoft REST API Guidelines - Error Handling](https://github.com/microsoft/api-guidelines)
- [Google Cloud API Design Guide - Errors](https://cloud.google.com/apis/design/errors)
- [Circuit Breaker Pattern - Martin Fowler](https://martinfowler.com/bliki/CircuitBreaker.html)
