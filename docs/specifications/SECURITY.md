# エンタープライズセキュリティ仕様書

## 目次

1. [はじめに](#1-はじめに)
2. [セキュリティ設計原則](#2-セキュリティ設計原則)
3. [認証システム](#3-認証システム)
4. [認可システム](#4-認可システム)
5. [APIセキュリティ](#5-apiセキュリティ)
6. [レート制限](#6-レート制限)
7. [セキュリティヘッダー](#7-セキュリティヘッダー)
8. [データ保護](#8-データ保護)
9. [シークレット管理](#9-シークレット管理)
10. [監査ログ](#10-監査ログ)
11. [脆弱性対策](#11-脆弱性対策)
12. [セキュリティテスト](#12-セキュリティテスト)
13. [インシデント対応](#13-インシデント対応)
14. [コンプライアンス](#14-コンプライアンス)

---

## 1. はじめに

### 1.1 このドキュメントの目的

本ドキュメントは、AI Interview Toolのセキュリティ設計と実装について詳細に解説します。エンタープライズ環境で求められるセキュリティ要件を満たすための具体的な実装方法を学習できます。

### 1.2 学習ゴール

1. 多層防御（Defense in Depth）の概念を理解できる
2. JWT/OAuth2.0ベースの認証システムを実装できる
3. RBAC（Role-Based Access Control）を設計・実装できる
4. OWASP Top 10脆弱性を理解し対策できる

### 1.3 セキュリティの重要性

```
┌─────────────────────────────────────────────────────────────────┐
│           セキュリティ侵害がもたらす影響                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 財務的損失                                                  │
│     - 直接的な金銭被害                                           │
│     - 復旧コスト                                                 │
│     - 法的制裁・罰金                                             │
│                                                                 │
│  2. 評判の毀損                                                   │
│     - 顧客の信頼喪失                                             │
│     - ブランドイメージの低下                                     │
│     - ビジネスパートナーの離反                                   │
│                                                                 │
│  3. 法的責任                                                     │
│     - 個人情報保護法違反                                         │
│     - GDPR/CCPA等の規制違反                                      │
│     - 訴訟リスク                                                 │
│                                                                 │
│  4. 業務停止                                                     │
│     - サービス中断                                               │
│     - データ損失                                                 │
│     - 復旧までの長期ダウンタイム                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. セキュリティ設計原則

### 2.1 多層防御（Defense in Depth）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          多層防御アーキテクチャ                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Layer 1: ネットワーク                                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ WAF / DDoS Protection / Firewall                                      │  │
│  │ - 不正トラフィックのブロック                                          │  │
│  │ - 既知の攻撃パターンの検出                                            │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                   ▼                                         │
│  Layer 2: アプリケーション境界                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ API Gateway / Rate Limiting / Security Headers                        │  │
│  │ - レート制限                                                          │  │
│  │ - 入力検証                                                            │  │
│  │ - セキュリティヘッダー                                                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                   ▼                                         │
│  Layer 3: 認証・認可                                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ JWT / OAuth2.0 / RBAC                                                 │  │
│  │ - ユーザー認証                                                        │  │
│  │ - 権限制御                                                            │  │
│  │ - セッション管理                                                      │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                   ▼                                         │
│  Layer 4: データ保護                                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Encryption / Masking / Access Control                                 │  │
│  │ - 暗号化（転送中・保存時）                                            │  │
│  │ - データマスキング                                                    │  │
│  │ - 行レベルセキュリティ                                                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 最小権限の原則

```python
# ❌ 悪い例: 全ての権限を持つロール
class AdminRole:
    permissions = ["*"]  # すべて許可

# ✅ 良い例: 必要最小限の権限
class InterviewerRole:
    permissions = [
        "interview:create",
        "interview:read:own",
        "interview:update:own",
        "transcript:read:own",
    ]

class ManagerRole:
    permissions = [
        "interview:read:all",
        "interview:read:team",
        "report:read:team",
        "report:export:team",
    ]
```

### 2.3 ゼロトラスト

```
┌─────────────────────────────────────────────────────────────────┐
│                    ゼロトラストの原則                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Never Trust, Always Verify                                  │
│     - 全てのリクエストを検証                                     │
│     - 内部ネットワークも信頼しない                               │
│                                                                 │
│  2. Least Privilege Access                                      │
│     - 必要最小限のアクセス権限                                   │
│     - Just-In-Time アクセス                                      │
│                                                                 │
│  3. Assume Breach                                               │
│     - 侵害を前提とした設計                                       │
│     - 被害の最小化                                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 認証システム

### 3.1 認証フロー

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          JWT認証フロー                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. ログイン                                                                │
│     Client ─────────────────────────────────────────▶ Server                │
│             POST /auth/login                                                │
│             { email, password }                                             │
│                                                                             │
│  2. 認証情報の検証                                                          │
│     Server: パスワードハッシュを検証                                         │
│                                                                             │
│  3. トークン発行                                                            │
│     Client ◀───────────────────────────────────────── Server                │
│             { access_token, refresh_token }                                 │
│                                                                             │
│  4. APIリクエスト                                                           │
│     Client ─────────────────────────────────────────▶ Server                │
│             Authorization: Bearer <access_token>                            │
│                                                                             │
│  5. トークン検証                                                            │
│     Server: 署名・有効期限を検証                                            │
│                                                                             │
│  6. トークンリフレッシュ（access_token期限切れ時）                          │
│     Client ─────────────────────────────────────────▶ Server                │
│             POST /auth/refresh                                              │
│             { refresh_token }                                               │
│     Client ◀───────────────────────────────────────── Server                │
│             { access_token (new) }                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 JWT実装

```python
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel


class JWTConfig(BaseSettings):
    """JWT設定

    Attributes:
        secret_key: 署名用秘密鍵（必ず環境変数で設定）
        algorithm: 署名アルゴリズム
        access_token_expire_minutes: アクセストークン有効期間
        refresh_token_expire_days: リフレッシュトークン有効期間
    """
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    class Config:
        env_prefix = "JWT_"


class TokenPayload(BaseModel):
    """JWTペイロードの構造

    Attributes:
        sub: サブジェクト（ユーザーID）
        exp: 有効期限
        iat: 発行日時
        type: トークンタイプ（access/refresh）
        roles: ユーザーロール
        organization_id: 組織ID
    """
    sub: str
    exp: datetime
    iat: datetime
    type: str = "access"
    roles: list[str] = []
    organization_id: str | None = None


class JWTService:
    """JWT管理サービス

    セキュリティのポイント:
    - 秘密鍵は環境変数から取得
    - アクセストークンは短い有効期間（30分）
    - リフレッシュトークンでアクセストークンを更新
    - トークンタイプをペイロードに含めて誤用を防止
    """

    def __init__(self, config: JWTConfig):
        self.config = config
        # パスワードハッシュ用（bcrypt使用）
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def create_access_token(
        self,
        user_id: str,
        roles: list[str],
        organization_id: str | None = None,
    ) -> str:
        """アクセストークンを生成

        Args:
            user_id: ユーザーID
            roles: ユーザーロール
            organization_id: 組織ID

        Returns:
            エンコードされたJWT文字列
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self.config.access_token_expire_minutes)

        payload = TokenPayload(
            sub=user_id,
            exp=expire,
            iat=now,
            type="access",
            roles=roles,
            organization_id=organization_id,
        )

        return jwt.encode(
            payload.model_dump(),
            self.config.secret_key,
            algorithm=self.config.algorithm,
        )

    def create_refresh_token(self, user_id: str) -> str:
        """リフレッシュトークンを生成

        リフレッシュトークンはアクセストークンより長い有効期間を持ちます。
        ロールなどの詳細情報は含めず、再認証時に最新を取得します。
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=self.config.refresh_token_expire_days)

        payload = TokenPayload(
            sub=user_id,
            exp=expire,
            iat=now,
            type="refresh",
        )

        return jwt.encode(
            payload.model_dump(),
            self.config.secret_key,
            algorithm=self.config.algorithm,
        )

    def verify_token(self, token: str, token_type: str = "access") -> TokenPayload:
        """トークンを検証

        検証項目:
        1. 署名の有効性
        2. 有効期限
        3. トークンタイプ

        Args:
            token: JWT文字列
            token_type: 期待するトークンタイプ

        Returns:
            検証済みペイロード

        Raises:
            AuthenticationError: 検証失敗時
        """
        try:
            payload = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm],
            )
            token_payload = TokenPayload(**payload)

            # トークンタイプの検証
            if token_payload.type != token_type:
                raise AuthenticationError(
                    code=ErrorCode.AUTH_TOKEN_INVALID,
                    message=f"Invalid token type: expected {token_type}",
                )

            return token_payload

        except jwt.ExpiredSignatureError:
            raise AuthenticationError(
                code=ErrorCode.AUTH_TOKEN_EXPIRED,
                message="Token has expired",
            )
        except JWTError as e:
            raise AuthenticationError(
                code=ErrorCode.AUTH_TOKEN_INVALID,
                message="Invalid token",
            ).with_cause(e)

    def hash_password(self, password: str) -> str:
        """パスワードをハッシュ化

        bcryptを使用し、自動的にソルトを生成します。
        """
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """パスワードを検証"""
        return self.pwd_context.verify(plain_password, hashed_password)
```

### 3.3 多要素認証（MFA）

```python
import pyotp
import qrcode
from io import BytesIO


class MFAService:
    """多要素認証サービス

    TOTP（Time-based One-Time Password）を使用。
    Google Authenticator等のアプリと互換性があります。
    """

    def generate_secret(self) -> str:
        """MFA用シークレットを生成

        Returns:
            Base32エンコードされたシークレット
        """
        return pyotp.random_base32()

    def get_provisioning_uri(
        self,
        secret: str,
        user_email: str,
        issuer: str = "AI Interview Tool",
    ) -> str:
        """QRコード用のURIを生成

        このURIをQRコードにすると、
        認証アプリでスキャンしてセットアップできます。
        """
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=user_email, issuer_name=issuer)

    def generate_qr_code(self, uri: str) -> bytes:
        """QRコード画像を生成

        Returns:
            PNG形式の画像バイト列
        """
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    def verify_code(self, secret: str, code: str) -> bool:
        """TOTPコードを検証

        Args:
            secret: ユーザーのMFAシークレット
            code: ユーザー入力の6桁コード

        Returns:
            検証結果

        Notes:
            valid_window=1 により、前後1期間（30秒）のコードも許容。
            これにより時刻のずれを吸収します。
        """
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)
```

### 3.4 SSO統合（Azure AD / Okta）

```python
from authlib.integrations.starlette_client import OAuth


class SSOService:
    """SSO（Single Sign-On）サービス

    Azure AD、Okta等のIdPと連携して認証を行います。
    OpenID Connect (OIDC) プロトコルを使用。
    """

    def __init__(self, config: SSOConfig):
        self.oauth = OAuth()
        self._setup_providers(config)

    def _setup_providers(self, config: SSOConfig):
        """OAuthプロバイダーを設定"""

        # Azure AD
        if config.azure_ad_client_id:
            self.oauth.register(
                name="azure",
                client_id=config.azure_ad_client_id,
                client_secret=config.azure_ad_client_secret,
                server_metadata_url=(
                    f"https://login.microsoftonline.com/{config.azure_ad_tenant_id}"
                    "/v2.0/.well-known/openid-configuration"
                ),
                client_kwargs={"scope": "openid email profile"},
            )

        # Okta
        if config.okta_domain:
            self.oauth.register(
                name="okta",
                client_id=config.okta_client_id,
                client_secret=config.okta_client_secret,
                server_metadata_url=(
                    f"https://{config.okta_domain}/.well-known/openid-configuration"
                ),
                client_kwargs={"scope": "openid email profile groups"},
            )

    async def get_authorization_url(
        self,
        provider: str,
        redirect_uri: str,
    ) -> str:
        """認証URLを取得

        ユーザーをIdPのログインページにリダイレクトするためのURLを生成。
        """
        client = self.oauth.create_client(provider)
        return await client.create_authorization_url(redirect_uri)

    async def handle_callback(
        self,
        provider: str,
        request: Request,
    ) -> dict:
        """コールバックを処理

        IdPからのリダイレクト後に呼び出され、
        認可コードをアクセストークンに交換し、ユーザー情報を取得。

        Returns:
            ユーザー情報を含む辞書
        """
        client = self.oauth.create_client(provider)
        token = await client.authorize_access_token(request)

        # ユーザー情報を取得
        userinfo = await client.userinfo(token=token)

        return {
            "provider": provider,
            "external_id": userinfo["sub"],
            "email": userinfo["email"],
            "name": userinfo.get("name"),
            "groups": userinfo.get("groups", []),
        }
```

---

## 4. 認可システム

### 4.1 RBAC（Role-Based Access Control）

```python
from enum import Enum
from dataclasses import dataclass


class Role(str, Enum):
    """システムロール

    階層構造:
    ADMIN > MANAGER > INTERVIEWER > VIEWER
    """
    ADMIN = "admin"           # 全権限
    MANAGER = "manager"       # チーム管理
    INTERVIEWER = "interviewer"  # インタビュー実施
    VIEWER = "viewer"         # 閲覧のみ


class Permission(str, Enum):
    """権限の定義

    命名規則: {リソース}:{アクション}:{スコープ}
    スコープ:
    - own: 自分が作成したリソースのみ
    - team: 所属チームのリソース
    - all: 全てのリソース
    """
    # プロジェクト
    PROJECT_CREATE = "project:create"
    PROJECT_READ_OWN = "project:read:own"
    PROJECT_READ_TEAM = "project:read:team"
    PROJECT_READ_ALL = "project:read:all"
    PROJECT_UPDATE_OWN = "project:update:own"
    PROJECT_DELETE = "project:delete"

    # インタビュー
    INTERVIEW_CREATE = "interview:create"
    INTERVIEW_READ_OWN = "interview:read:own"
    INTERVIEW_READ_TEAM = "interview:read:team"
    INTERVIEW_READ_ALL = "interview:read:all"
    INTERVIEW_UPDATE_OWN = "interview:update:own"
    INTERVIEW_DELETE = "interview:delete"

    # レポート
    REPORT_CREATE = "report:create"
    REPORT_READ_TEAM = "report:read:team"
    REPORT_EXPORT = "report:export"
    REPORT_APPROVE = "report:approve"

    # 管理
    USER_MANAGE = "user:manage"
    SETTINGS_MANAGE = "settings:manage"
    AUDIT_VIEW = "audit:view"


# ロールと権限のマッピング
ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.ADMIN: set(Permission),  # 全権限

    Role.MANAGER: {
        Permission.PROJECT_CREATE,
        Permission.PROJECT_READ_TEAM,
        Permission.PROJECT_UPDATE_OWN,
        Permission.INTERVIEW_CREATE,
        Permission.INTERVIEW_READ_TEAM,
        Permission.INTERVIEW_UPDATE_OWN,
        Permission.REPORT_CREATE,
        Permission.REPORT_READ_TEAM,
        Permission.REPORT_EXPORT,
        Permission.REPORT_APPROVE,
    },

    Role.INTERVIEWER: {
        Permission.PROJECT_READ_OWN,
        Permission.INTERVIEW_CREATE,
        Permission.INTERVIEW_READ_OWN,
        Permission.INTERVIEW_UPDATE_OWN,
        Permission.REPORT_CREATE,
    },

    Role.VIEWER: {
        Permission.PROJECT_READ_OWN,
        Permission.INTERVIEW_READ_OWN,
    },
}


@dataclass
class AuthorizationContext:
    """認可コンテキスト

    リクエストのユーザー情報と対象リソースの情報を保持。
    """
    user_id: str
    roles: list[Role]
    organization_id: str
    resource_owner_id: str | None = None
    resource_organization_id: str | None = None


class AuthorizationService:
    """認可サービス

    権限チェックのロジックを一元管理します。
    """

    def has_permission(
        self,
        ctx: AuthorizationContext,
        permission: Permission,
    ) -> bool:
        """権限を持っているかチェック

        Args:
            ctx: 認可コンテキスト
            permission: 必要な権限

        Returns:
            権限がある場合True
        """
        # ロールから権限を取得
        user_permissions = set()
        for role in ctx.roles:
            user_permissions.update(ROLE_PERMISSIONS.get(role, set()))

        # 権限チェック
        if permission in user_permissions:
            return self._check_scope(ctx, permission)

        return False

    def _check_scope(
        self,
        ctx: AuthorizationContext,
        permission: Permission,
    ) -> bool:
        """スコープをチェック

        :own - 自分のリソースのみ
        :team - 同じ組織のリソース
        :all - 全てのリソース
        """
        perm_str = permission.value

        if ":all" in perm_str:
            return True

        if ":team" in perm_str:
            # 同じ組織かチェック
            return ctx.organization_id == ctx.resource_organization_id

        if ":own" in perm_str:
            # 自分のリソースかチェック
            return ctx.user_id == ctx.resource_owner_id

        return True  # スコープ指定なしの権限

    def require_permission(
        self,
        ctx: AuthorizationContext,
        permission: Permission,
    ) -> None:
        """権限を要求（なければ例外）

        使用例:
            auth_service.require_permission(ctx, Permission.INTERVIEW_CREATE)
        """
        if not self.has_permission(ctx, permission):
            raise AuthorizationError(
                code=ErrorCode.AUTHZ_PERMISSION_DENIED,
                required_permission=permission.value,
            )
```

### 4.2 FastAPI での認可デコレータ

```python
from functools import wraps
from fastapi import Depends, Request


def require_permissions(*permissions: Permission):
    """権限を要求するデコレータ

    使用例:
        @router.post("/interviews")
        @require_permissions(Permission.INTERVIEW_CREATE)
        async def create_interview(
            request: CreateInterviewRequest,
            current_user: User = Depends(get_current_user),
        ):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # current_user を kwargs から取得
            current_user = kwargs.get("current_user")
            if not current_user:
                raise AuthenticationError()

            # 認可コンテキストを構築
            ctx = AuthorizationContext(
                user_id=str(current_user.id),
                roles=[Role(r) for r in current_user.roles],
                organization_id=str(current_user.organization_id),
            )

            # 権限チェック
            auth_service = AuthorizationService()
            for permission in permissions:
                auth_service.require_permission(ctx, permission)

            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

---

## 5. APIセキュリティ

### 5.1 入力検証

```python
from pydantic import BaseModel, Field, validator
import re


class CreateInterviewRequest(BaseModel):
    """インタビュー作成リクエスト

    Pydanticによる入力検証で、不正なデータを早期に拒否します。
    """
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="インタビュータイトル",
    )

    template_id: str = Field(
        ...,
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        description="テンプレートID（UUID形式）",
    )

    interviewee_email: str = Field(
        ...,
        max_length=254,
        description="被インタビュー者のメールアドレス",
    )

    @validator("interviewee_email")
    def validate_email(cls, v):
        """メールアドレスの追加検証"""
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, v):
            raise ValueError("Invalid email format")
        return v.lower()

    @validator("title")
    def sanitize_title(cls, v):
        """タイトルのサニタイズ"""
        # HTMLタグを除去
        v = re.sub(r"<[^>]+>", "", v)
        # 連続する空白を単一に
        v = re.sub(r"\s+", " ", v)
        return v.strip()


# SQLインジェクション対策
# SQLAlchemy ORMを使用することで、自動的にパラメータ化される
async def get_interview(interview_id: str):
    # ✅ 安全: パラメータ化クエリ
    result = await session.execute(
        select(Interview).where(Interview.id == interview_id)
    )
    return result.scalar_one_or_none()

    # ❌ 危険: 文字列連結（絶対に使わない）
    # result = await session.execute(
    #     f"SELECT * FROM interviews WHERE id = '{interview_id}'"
    # )
```

### 5.2 出力エンコーディング

```python
from markupsafe import escape


def format_transcript_for_display(transcript: str) -> str:
    """文字起こしを表示用にフォーマット

    XSS対策として、HTMLエスケープを行います。
    """
    # HTMLエスケープ
    escaped = escape(transcript)

    # 改行を<br>に変換（エスケープ後に行う）
    formatted = str(escaped).replace("\n", "<br>")

    return formatted
```

---

## 6. レート制限

### 6.1 レート制限の設計

```
┌─────────────────────────────────────────────────────────────────┐
│                    レート制限の戦略                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 固定ウィンドウ (Fixed Window)                               │
│     - 単純だが、ウィンドウ境界で突発的なリクエストを許容         │
│     時間: |----60秒----|----60秒----|                           │
│     制限: [   100回    ][   100回    ]                          │
│                                                                 │
│  2. スライディングウィンドウ (Sliding Window) ← 本システムで採用 │
│     - より滑らかな制限、突発的なリクエストを抑制                 │
│     時間: ---->|----60秒----|---->                              │
│     制限:     [   過去60秒で100回   ]                           │
│                                                                 │
│  3. トークンバケット (Token Bucket)                              │
│     - バースト対応、一定レートでトークン補充                     │
│     容量: [●●●●●●●●●●] 10トークン                               │
│     補充: 1トークン/秒                                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 実装

```python
import time
from dataclasses import dataclass
from collections import defaultdict
import asyncio


@dataclass
class RateLimitConfig:
    """レート制限設定

    Attributes:
        requests_per_window: ウィンドウ内の許可リクエスト数
        window_seconds: ウィンドウサイズ（秒）
        by_ip: IPアドレスごとに制限するか
        by_user: ユーザーごとに制限するか
    """
    requests_per_window: int = 100
    window_seconds: int = 60
    by_ip: bool = True
    by_user: bool = True


class SlidingWindowRateLimiter:
    """スライディングウィンドウ方式のレート制限

    実装の仕組み:
    - 各リクエストのタイムスタンプを記録
    - 現在時刻から window_seconds 以内のリクエスト数をカウント
    - 古いリクエストは定期的にクリーンアップ
    """

    def __init__(self, config: RateLimitConfig):
        self.config = config
        # key -> [timestamp1, timestamp2, ...]
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def is_allowed(self, key: str) -> tuple[bool, dict]:
        """リクエストが許可されるかチェック

        Args:
            key: レート制限のキー（IPアドレスまたはユーザーID）

        Returns:
            (許可されるか, レート制限情報)
        """
        async with self._lock:
            now = time.time()
            window_start = now - self.config.window_seconds

            # 古いリクエストを削除
            self._requests[key] = [
                ts for ts in self._requests[key]
                if ts > window_start
            ]

            current_count = len(self._requests[key])
            remaining = self.config.requests_per_window - current_count

            rate_limit_info = {
                "limit": self.config.requests_per_window,
                "remaining": max(0, remaining - 1),
                "reset": int(window_start + self.config.window_seconds),
            }

            if current_count >= self.config.requests_per_window:
                # レート制限超過
                retry_after = int(
                    self._requests[key][0] + self.config.window_seconds - now
                )
                rate_limit_info["retry_after"] = max(1, retry_after)
                return False, rate_limit_info

            # リクエストを記録
            self._requests[key].append(now)
            return True, rate_limit_info


class RateLimitMiddleware:
    """レート制限ミドルウェア

    使用例:
        app.add_middleware(RateLimitMiddleware, config=RateLimitConfig())
    """

    def __init__(self, app, config: RateLimitConfig = RateLimitConfig()):
        self.app = app
        self.config = config
        self.limiter = SlidingWindowRateLimiter(config)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # レート制限キーを決定
        client_ip = self._get_client_ip(scope)
        key = f"ip:{client_ip}"

        # レート制限チェック
        allowed, info = await self.limiter.is_allowed(key)

        if not allowed:
            # 429 Too Many Requests を返す
            response = JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "SYSTEM_RATE_LIMIT",
                        "message": "リクエスト数の上限に達しました",
                        "retry_after": info.get("retry_after"),
                    }
                },
                headers={
                    "Retry-After": str(info.get("retry_after", 60)),
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(info["reset"]),
                },
            )
            await response(scope, receive, send)
            return

        # レート制限ヘッダーを追加してリクエストを処理
        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend([
                    (b"x-ratelimit-limit", str(info["limit"]).encode()),
                    (b"x-ratelimit-remaining", str(info["remaining"]).encode()),
                    (b"x-ratelimit-reset", str(info["reset"]).encode()),
                ])
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_headers)

    def _get_client_ip(self, scope) -> str:
        """クライアントIPを取得

        プロキシ経由の場合、X-Forwarded-For ヘッダーを確認。
        """
        headers = dict(scope.get("headers", []))

        # X-Forwarded-For ヘッダーをチェック
        forwarded = headers.get(b"x-forwarded-for")
        if forwarded:
            # 最初のIPが元のクライアント
            return forwarded.decode().split(",")[0].strip()

        # 直接接続の場合
        client = scope.get("client")
        return client[0] if client else "unknown"
```

### 6.3 エンドポイント別のレート制限

```python
# エンドポイントごとに異なる制限を設定
ENDPOINT_RATE_LIMITS = {
    # 認証関連: ブルートフォース対策で厳しく
    "/api/v1/auth/login": RateLimitConfig(
        requests_per_window=5,
        window_seconds=60,
    ),
    "/api/v1/auth/register": RateLimitConfig(
        requests_per_window=3,
        window_seconds=3600,  # 1時間
    ),

    # AI関連: コスト対策
    "/api/v1/interviews/*/chat": RateLimitConfig(
        requests_per_window=30,
        window_seconds=60,
    ),

    # 一般API: 標準
    "default": RateLimitConfig(
        requests_per_window=100,
        window_seconds=60,
    ),
}
```

---

## 7. セキュリティヘッダー

### 7.1 主要なセキュリティヘッダー

```python
class SecurityHeadersMiddleware:
    """セキュリティヘッダーを追加するミドルウェア

    各ヘッダーの目的と設定値を解説します。
    """

    # セキュリティヘッダーの定義
    SECURITY_HEADERS = {
        # XSS対策: ブラウザのXSSフィルタを有効化
        "X-XSS-Protection": "1; mode=block",

        # コンテンツタイプの強制: MIMEスニッフィング防止
        "X-Content-Type-Options": "nosniff",

        # クリックジャッキング対策: iframeでの埋め込みを制限
        "X-Frame-Options": "DENY",

        # HTTPS強制: HTTPアクセスをHTTPSにリダイレクト
        # max-age: 1年間（31536000秒）
        # includeSubDomains: サブドメインにも適用
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",

        # リファラー制御: 外部サイトへの情報漏洩防止
        "Referrer-Policy": "strict-origin-when-cross-origin",

        # パーミッションポリシー: ブラウザ機能の制限
        "Permissions-Policy": (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(self), "  # マイクは自サイトのみ許可
            "payment=(), "
            "usb=()"
        ),

        # コンテンツセキュリティポリシー（CSP）
        # 詳細は後述
    }

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_security_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))

                for name, value in self.SECURITY_HEADERS.items():
                    headers.append((name.lower().encode(), value.encode()))

                # CSPは動的に生成
                csp = self._build_csp()
                headers.append((b"content-security-policy", csp.encode()))

                message["headers"] = headers

            await send(message)

        await self.app(scope, receive, send_with_security_headers)

    def _build_csp(self) -> str:
        """Content-Security-Policy を構築

        CSPは、ブラウザが読み込み可能なリソースの出所を制限します。
        XSSやデータインジェクション攻撃の緩和に効果的です。
        """
        directives = [
            # デフォルトポリシー: 自サイトのみ許可
            "default-src 'self'",

            # スクリプト: 自サイト + インライン（nonce付き）
            "script-src 'self' 'unsafe-inline'",

            # スタイル: 自サイト + インライン
            "style-src 'self' 'unsafe-inline'",

            # 画像: 自サイト + データURL
            "img-src 'self' data: blob:",

            # フォント: 自サイト + Google Fonts
            "font-src 'self' https://fonts.gstatic.com",

            # 接続先: 自サイト + API + WebSocket
            "connect-src 'self' wss://*.example.com",

            # フレーム: 禁止
            "frame-ancestors 'none'",

            # フォーム送信先: 自サイトのみ
            "form-action 'self'",

            # ベースURL: 自サイトのみ
            "base-uri 'self'",

            # オブジェクト: 禁止（Flash等）
            "object-src 'none'",
        ]

        return "; ".join(directives)
```

### 7.2 CORS設定

```python
from fastapi.middleware.cors import CORSMiddleware


def setup_cors(app: FastAPI, config: SecurityConfig):
    """CORS（Cross-Origin Resource Sharing）を設定

    CORSは、異なるオリジン（ドメイン）からのリクエストを制御します。
    """

    app.add_middleware(
        CORSMiddleware,
        # 許可するオリジン
        # 開発: ["http://localhost:3000"]
        # 本番: ["https://app.example.com"]
        allow_origins=config.cors_origins,

        # 認証情報（Cookie等）を含むリクエストを許可
        allow_credentials=True,

        # 許可するHTTPメソッド
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],

        # 許可するリクエストヘッダー
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Correlation-ID",
            "X-Request-ID",
        ],

        # レスポンスで公開するヘッダー
        expose_headers=[
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
        ],

        # プリフライトリクエストのキャッシュ時間
        max_age=600,  # 10分
    )
```

---

## 8. データ保護

### 8.1 暗号化

```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os


class EncryptionService:
    """データ暗号化サービス

    Fernet（AES-128-CBC + HMAC-SHA256）を使用。
    センシティブなデータの保存時に暗号化します。
    """

    def __init__(self, master_key: str):
        """
        Args:
            master_key: マスターキー（環境変数から取得）
        """
        # マスターキーから暗号化キーを導出
        self.fernet = self._create_fernet(master_key)

    def _create_fernet(self, master_key: str) -> Fernet:
        """マスターキーからFernetインスタンスを生成

        PBKDF2を使用してキーを導出することで、
        マスターキーの強度に関係なく安全なキーを生成。
        """
        salt = b"ai-interview-tool-salt"  # 固定ソルト（本番では変更推奨）

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(
            kdf.derive(master_key.encode())
        )
        return Fernet(key)

    def encrypt(self, data: str) -> str:
        """データを暗号化

        Args:
            data: 暗号化する文字列

        Returns:
            暗号化されたBase64文字列
        """
        encrypted = self.fernet.encrypt(data.encode())
        return encrypted.decode()

    def decrypt(self, encrypted_data: str) -> str:
        """データを復号

        Args:
            encrypted_data: 暗号化されたBase64文字列

        Returns:
            復号された文字列
        """
        decrypted = self.fernet.decrypt(encrypted_data.encode())
        return decrypted.decode()


# 使用例
encryption = EncryptionService(os.getenv("ENCRYPTION_KEY"))

# インタビュー音声のURLを暗号化して保存
audio_url = "https://storage.example.com/audio/interview-123.mp3"
encrypted_url = encryption.encrypt(audio_url)
# 保存: "gAAAAABf..."

# 取得時に復号
decrypted_url = encryption.decrypt(encrypted_url)
# "https://storage.example.com/audio/interview-123.mp3"
```

### 8.2 データマスキング

```python
import re
from dataclasses import dataclass
from typing import Any


@dataclass
class MaskingRule:
    """マスキングルール"""
    pattern: str
    replacement: str | callable


class DataMaskingService:
    """センシティブデータのマスキングサービス

    レポートやログ出力時に個人情報をマスキングします。
    """

    MASKING_RULES = [
        # メールアドレス: user@example.com → u***@example.com
        MaskingRule(
            pattern=r"([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
            replacement=lambda m: f"{m.group(1)[0]}***@{m.group(2)}",
        ),

        # 電話番号: 090-1234-5678 → ***-****-5678
        MaskingRule(
            pattern=r"(\d{2,4})-(\d{2,4})-(\d{4})",
            replacement=r"***-****-\3",
        ),

        # クレジットカード: 1234-5678-9012-3456 → ****-****-****-3456
        MaskingRule(
            pattern=r"\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?(\d{4})",
            replacement=r"****-****-****-\1",
        ),

        # 氏名（日本語）: 山田太郎 → 山●●郎
        MaskingRule(
            pattern=r"([一-龥ぁ-んァ-ン])([一-龥ぁ-んァ-ン]+)([一-龥ぁ-んァ-ン])",
            replacement=lambda m: f"{m.group(1)}{'●' * len(m.group(2))}{m.group(3)}",
        ),
    ]

    def mask(self, data: str) -> str:
        """文字列データをマスキング"""
        result = data
        for rule in self.MASKING_RULES:
            if callable(rule.replacement):
                result = re.sub(rule.pattern, rule.replacement, result)
            else:
                result = re.sub(rule.pattern, rule.replacement, result)
        return result

    def mask_dict(self, data: dict, fields_to_mask: list[str]) -> dict:
        """辞書の特定フィールドをマスキング

        Args:
            data: 対象の辞書
            fields_to_mask: マスキングするフィールド名のリスト

        Returns:
            マスキング済みの辞書
        """
        result = data.copy()
        for field in fields_to_mask:
            if field in result and isinstance(result[field], str):
                result[field] = self.mask(result[field])
        return result
```

---

## 9. シークレット管理

### 9.1 環境変数での管理

```python
from pydantic import BaseSettings, Field, SecretStr


class SecurityConfig(BaseSettings):
    """セキュリティ設定

    SecretStr を使用することで、ログ等で誤って出力されるのを防ぎます。
    """

    # シークレットキー
    secret_key: SecretStr = Field(..., env="SECRET_KEY")

    # データベース認証情報
    database_password: SecretStr = Field(..., env="POSTGRES_PASSWORD")

    # AI プロバイダーキー
    azure_openai_api_key: SecretStr = Field(
        default=None,
        env="AZURE_OPENAI_API_KEY"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def get_secret_key(self) -> str:
        """シークレットキーを安全に取得"""
        return self.secret_key.get_secret_value()


# 使用例
config = SecurityConfig()

# ❌ 危険: シークレットがそのまま出力される可能性
# print(f"Key: {config.secret_key}")  # SecretStr('**********')

# ✅ 安全: 明示的に値を取得
secret = config.get_secret_key()
```

### 9.2 クラウドシークレット管理

```python
from abc import ABC, abstractmethod


class SecretManagerBase(ABC):
    """シークレット管理の抽象基底クラス"""

    @abstractmethod
    async def get_secret(self, name: str) -> str:
        """シークレットを取得"""
        pass

    @abstractmethod
    async def set_secret(self, name: str, value: str) -> None:
        """シークレットを設定"""
        pass


class AzureKeyVaultManager(SecretManagerBase):
    """Azure Key Vault を使用したシークレット管理

    Azure Key Vault は、シークレット、キー、証明書を
    安全に保存・管理するためのサービスです。
    """

    def __init__(self, vault_url: str):
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient

        credential = DefaultAzureCredential()
        self.client = SecretClient(vault_url=vault_url, credential=credential)

    async def get_secret(self, name: str) -> str:
        """Key Vault からシークレットを取得

        Args:
            name: シークレット名

        Returns:
            シークレット値
        """
        secret = self.client.get_secret(name)
        return secret.value

    async def set_secret(self, name: str, value: str) -> None:
        """Key Vault にシークレットを設定"""
        self.client.set_secret(name, value)


class AWSSecretsManager(SecretManagerBase):
    """AWS Secrets Manager を使用したシークレット管理"""

    def __init__(self, region: str = "ap-northeast-1"):
        import boto3
        self.client = boto3.client("secretsmanager", region_name=region)

    async def get_secret(self, name: str) -> str:
        response = self.client.get_secret_value(SecretId=name)
        return response["SecretString"]

    async def set_secret(self, name: str, value: str) -> None:
        self.client.put_secret_value(SecretId=name, SecretString=value)


class GCPSecretManager(SecretManagerBase):
    """GCP Secret Manager を使用したシークレット管理"""

    def __init__(self, project_id: str):
        from google.cloud import secretmanager
        self.client = secretmanager.SecretManagerServiceClient()
        self.project_id = project_id

    async def get_secret(self, name: str) -> str:
        secret_name = f"projects/{self.project_id}/secrets/{name}/versions/latest"
        response = self.client.access_secret_version(request={"name": secret_name})
        return response.payload.data.decode("UTF-8")

    async def set_secret(self, name: str, value: str) -> None:
        parent = f"projects/{self.project_id}/secrets/{name}"
        self.client.add_secret_version(
            request={"parent": parent, "payload": {"data": value.encode("UTF-8")}}
        )
```

---

## 10. 監査ログ

### 10.1 監査ログの設計

```python
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass


class AuditAction(str, Enum):
    """監査対象のアクション"""
    # 認証
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    MFA_ENABLE = "mfa_enable"
    MFA_DISABLE = "mfa_disable"

    # データアクセス
    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"

    # 管理操作
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"
    SETTINGS_CHANGE = "settings_change"


@dataclass
class AuditLogEntry:
    """監査ログエントリ

    Attributes:
        id: ログID
        timestamp: 発生日時
        action: アクション種別
        actor_id: 操作者のユーザーID
        actor_email: 操作者のメールアドレス
        resource_type: 対象リソースの種類
        resource_id: 対象リソースのID
        organization_id: 組織ID
        client_ip: クライアントIPアドレス
        user_agent: ユーザーエージェント
        status: 成功/失敗
        details: 追加情報（変更前後の値など）
    """
    id: str
    timestamp: datetime
    action: AuditAction
    actor_id: str
    actor_email: str
    resource_type: str
    resource_id: str | None
    organization_id: str
    client_ip: str
    user_agent: str
    status: str  # "success" | "failure"
    details: dict


class AuditLogService:
    """監査ログサービス

    全ての重要な操作を記録し、コンプライアンス要件を満たします。
    """

    def __init__(self, repository: AuditLogRepository):
        self.repo = repository

    async def log(
        self,
        action: AuditAction,
        actor: User,
        resource_type: str,
        resource_id: str | None = None,
        request: Request | None = None,
        status: str = "success",
        details: dict | None = None,
    ) -> None:
        """監査ログを記録

        Args:
            action: 実行されたアクション
            actor: 操作を行ったユーザー
            resource_type: 対象リソースの種類
            resource_id: 対象リソースのID
            request: HTTPリクエスト（IPなど取得用）
            status: 操作結果
            details: 追加情報
        """
        entry = AuditLogEntry(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            action=action,
            actor_id=str(actor.id),
            actor_email=actor.email,
            resource_type=resource_type,
            resource_id=resource_id,
            organization_id=str(actor.organization_id),
            client_ip=self._get_client_ip(request) if request else "unknown",
            user_agent=request.headers.get("user-agent", "unknown") if request else "unknown",
            status=status,
            details=details or {},
        )

        # 非同期で保存（パフォーマンス考慮）
        await self.repo.create(entry)

        # 構造化ログにも出力
        logger.audit(
            action=action.value,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=str(actor.id),
            details=details,
        )

    async def log_login(
        self,
        user: User,
        request: Request,
        success: bool,
        failure_reason: str | None = None,
    ) -> None:
        """ログインイベントを記録"""
        await self.log(
            action=AuditAction.LOGIN if success else AuditAction.LOGIN_FAILED,
            actor=user,
            resource_type="session",
            request=request,
            status="success" if success else "failure",
            details={"failure_reason": failure_reason} if failure_reason else None,
        )

    async def log_data_access(
        self,
        user: User,
        resource_type: str,
        resource_id: str,
        action: AuditAction,
        request: Request,
    ) -> None:
        """データアクセスを記録"""
        await self.log(
            action=action,
            actor=user,
            resource_type=resource_type,
            resource_id=resource_id,
            request=request,
        )

    def _get_client_ip(self, request: Request) -> str:
        """クライアントIPを取得"""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
```

---

## 11. 脆弱性対策

### 11.1 OWASP Top 10 対策

```
┌─────────────────────────────────────────────────────────────────┐
│                    OWASP Top 10 対策一覧                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  A01: Broken Access Control（アクセス制御の不備）               │
│  → RBAC実装、リソースレベルの権限チェック                       │
│                                                                 │
│  A02: Cryptographic Failures（暗号化の失敗）                    │
│  → TLS強制、保存時暗号化、安全なアルゴリズム使用                │
│                                                                 │
│  A03: Injection（インジェクション）                              │
│  → パラメータ化クエリ、入力検証、出力エスケープ                 │
│                                                                 │
│  A04: Insecure Design（安全でない設計）                         │
│  → 脅威モデリング、セキュリティレビュー                         │
│                                                                 │
│  A05: Security Misconfiguration（設定ミス）                     │
│  → セキュリティヘッダー、デフォルト無効化、IaC                  │
│                                                                 │
│  A06: Vulnerable Components（脆弱なコンポーネント）             │
│  → 依存関係スキャン、自動更新、SBOM                             │
│                                                                 │
│  A07: Authentication Failures（認証の失敗）                     │
│  → 強力なパスワードポリシー、MFA、レート制限                    │
│                                                                 │
│  A08: Data Integrity Failures（データ整合性の失敗）             │
│  → 署名検証、安全なデシリアライズ                               │
│                                                                 │
│  A09: Logging Failures（ログの失敗）                            │
│  → 構造化ログ、監査ログ、アラート                               │
│                                                                 │
│  A10: SSRF（サーバーサイドリクエストフォージェリ）               │
│  → URLバリデーション、内部ネットワークへのアクセス制限          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 11.2 依存関係のセキュリティスキャン

```yaml
# .github/workflows/security.yml
name: Security Scan

on:
  push:
    branches: [main, develop]
  schedule:
    - cron: "0 0 * * *"  # 毎日実行

jobs:
  dependency-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Python依存関係のスキャン
      - name: Run Safety check
        run: |
          pip install safety
          safety check -r apps/backend/requirements.txt

      # Node.js依存関係のスキャン
      - name: Run npm audit
        run: |
          cd apps/web
          npm audit --audit-level=high

      # Dockerイメージのスキャン
      - name: Run Trivy
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: "ai-interviewer-backend:latest"
          severity: "CRITICAL,HIGH"

      # シークレット検出
      - name: Run Gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## 12. セキュリティテスト

### 12.1 ユニットテスト

```python
# tests/test_security.py

import pytest
from grc_backend.core.security import (
    JWTService,
    RateLimiter,
    SensitiveDataFilter,
)


class TestJWTService:
    """JWT関連のセキュリティテスト"""

    def test_password_hashing(self):
        """パスワードハッシュのテスト"""
        jwt_service = JWTService(config)
        password = "SecurePassword123!"

        hashed = jwt_service.hash_password(password)

        # ハッシュは元のパスワードと異なる
        assert hashed != password
        # 正しいパスワードで検証成功
        assert jwt_service.verify_password(password, hashed)
        # 間違ったパスワードで検証失敗
        assert not jwt_service.verify_password("wrong", hashed)

    def test_token_expiration(self):
        """トークン期限切れのテスト"""
        jwt_service = JWTService(JWTConfig(
            secret_key="test",
            access_token_expire_minutes=-1,  # 既に期限切れ
        ))

        token = jwt_service.create_access_token("user-123", ["user"])

        with pytest.raises(AuthenticationError) as exc:
            jwt_service.verify_token(token)

        assert exc.value.code == ErrorCode.AUTH_TOKEN_EXPIRED

    def test_token_tampering(self):
        """トークン改ざん検出のテスト"""
        jwt_service = JWTService(config)
        token = jwt_service.create_access_token("user-123", ["user"])

        # トークンを改ざん
        tampered_token = token[:-5] + "xxxxx"

        with pytest.raises(AuthenticationError) as exc:
            jwt_service.verify_token(tampered_token)

        assert exc.value.code == ErrorCode.AUTH_TOKEN_INVALID


class TestRateLimiter:
    """レート制限のテスト"""

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self):
        """レート制限超過のテスト"""
        limiter = SlidingWindowRateLimiter(
            RateLimitConfig(requests_per_window=5, window_seconds=60)
        )

        key = "test-ip"

        # 5回は許可
        for _ in range(5):
            allowed, _ = await limiter.is_allowed(key)
            assert allowed

        # 6回目は拒否
        allowed, info = await limiter.is_allowed(key)
        assert not allowed
        assert "retry_after" in info


class TestSensitiveDataFilter:
    """センシティブデータマスキングのテスト"""

    def test_email_masking(self):
        """メールアドレスマスキングのテスト"""
        filter = SensitiveDataFilter()
        text = 'User email is "user@example.com"'

        masked = filter._mask_sensitive_data(text)

        assert "user@example.com" not in masked
        assert "u***@example.com" in masked

    def test_password_masking(self):
        """パスワードマスキングのテスト"""
        filter = SensitiveDataFilter()
        text = '{"password": "secret123"}'

        masked = filter._mask_sensitive_data(text)

        assert "secret123" not in masked
        assert "***MASKED***" in masked
```

### 12.2 ペネトレーションテスト項目

```markdown
## ペネトレーションテストチェックリスト

### 認証
- [ ] ブルートフォース攻撃への耐性
- [ ] パスワードリセットの安全性
- [ ] セッションハイジャック
- [ ] トークン漏洩時の影響範囲

### 認可
- [ ] 権限昇格の可能性
- [ ] 他ユーザーデータへのアクセス
- [ ] 管理機能への不正アクセス

### 入力検証
- [ ] SQLインジェクション
- [ ] XSS（Stored/Reflected/DOM）
- [ ] コマンドインジェクション
- [ ] パストラバーサル

### ビジネスロジック
- [ ] レート制限のバイパス
- [ ] 二重処理
- [ ] 時間ベースの攻撃

### インフラ
- [ ] SSRF
- [ ] 情報漏洩（エラーメッセージ、ヘッダー）
- [ ] 設定ミス
```

---

## 13. インシデント対応

### 13.1 インシデント対応フロー

```
┌─────────────────────────────────────────────────────────────────┐
│                  インシデント対応プロセス                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 検知 (Detection)                                            │
│     ↓                                                           │
│     - アラート受信                                               │
│     - 異常検知                                                   │
│     - ユーザー報告                                               │
│                                                                 │
│  2. 封じ込め (Containment)                                       │
│     ↓                                                           │
│     - 影響範囲の特定                                             │
│     - 被害拡大の防止                                             │
│     - 証拠の保全                                                 │
│                                                                 │
│  3. 根絶 (Eradication)                                           │
│     ↓                                                           │
│     - 原因の特定                                                 │
│     - 脆弱性の修正                                               │
│     - マルウェアの除去                                           │
│                                                                 │
│  4. 復旧 (Recovery)                                              │
│     ↓                                                           │
│     - システムの復元                                             │
│     - 監視強化                                                   │
│     - サービス再開                                               │
│                                                                 │
│  5. 事後対応 (Post-Incident)                                     │
│                                                                 │
│     - インシデントレポート作成                                   │
│     - 再発防止策の策定                                           │
│     - 関係者への報告                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 14. コンプライアンス

### 14.1 対応規制・基準

| 規制/基準 | 対象 | 主な要件 |
|----------|------|---------|
| 個人情報保護法 | 日本 | 個人情報の適正な取扱い |
| GDPR | EU | データ保護、削除権 |
| SOC 2 | 国際 | セキュリティ統制 |
| ISO 27001 | 国際 | 情報セキュリティ管理 |

### 14.2 コンプライアンスチェックリスト

```markdown
## セキュリティコンプライアンスチェックリスト

### データ保護
- [ ] 個人情報の暗号化（保存時・転送時）
- [ ] アクセス制御の実装
- [ ] データ保持期間の設定
- [ ] データ削除機能の実装

### 監査
- [ ] 全操作の監査ログ
- [ ] ログの改ざん防止
- [ ] ログの保持期間（最低1年）

### アクセス管理
- [ ] 強力なパスワードポリシー
- [ ] 多要素認証
- [ ] 最小権限の原則

### インシデント対応
- [ ] インシデント対応手順の文書化
- [ ] 定期的な訓練
- [ ] 報告義務の遵守

### 継続的改善
- [ ] 定期的なセキュリティレビュー
- [ ] ペネトレーションテスト
- [ ] 脆弱性スキャン
```

---

## 付録

### A. セキュリティ設定一覧

```bash
# .env - セキュリティ関連設定

# JWT
SECRET_KEY=<非常に長いランダム文字列>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# 暗号化
ENCRYPTION_KEY=<32文字以上のランダム文字列>

# CORS
CORS_ORIGINS=https://app.example.com

# レート制限
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# セキュリティ
SECURE_COOKIES=true
HSTS_ENABLED=true
```

### B. 関連ドキュメント

- [ログ管理仕様書](./LOGGING.md)
- [エラー処理仕様書](./ERROR_HANDLING.md)
- [インフラストラクチャ仕様書](./INFRASTRUCTURE.md)
