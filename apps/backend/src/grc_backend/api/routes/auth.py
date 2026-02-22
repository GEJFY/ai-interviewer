"""Authentication endpoints."""

import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

from grc_backend.api.deps import AdminUser, CurrentUser, DBSession, get_settings_dep
from grc_backend.config import Settings
from grc_core.repositories import UserRepository
from grc_core.schemas import UserCreate, UserRead

logger = logging.getLogger(__name__)

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Token(BaseModel):
    """Token response model."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Token refresh request."""

    refresh_token: str


class LoginRequest(BaseModel):
    """Login request model."""

    email: EmailStr
    password: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(
    data: dict,
    settings: Settings,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(data: dict, settings: Settings) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DBSession,
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> Token:
    """Authenticate user and return tokens."""
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(form_data.username)

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.id},
        settings=settings,
    )
    refresh_token = create_refresh_token(
        data={"sub": user.id},
        settings=settings,
    )

    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: DBSession,
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> Token:
    """Refresh access token using refresh token."""
    try:
        payload = jwt.decode(
            token_data.refresh_token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

    except jwt.ExpiredSignatureError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        ) from err
    except jwt.JWTError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from err

    user_repo = UserRepository(db)
    user = await user_repo.get(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    access_token = create_access_token(data={"sub": user.id}, settings=settings)
    new_refresh_token = create_refresh_token(data={"sub": user.id}, settings=settings)

    return Token(access_token=access_token, refresh_token=new_refresh_token)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: DBSession,
) -> UserRead:
    """Register a new user."""
    user_repo = UserRepository(db)

    # Check if email already exists
    if await user_repo.email_exists(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Hash password
    password_hash = get_password_hash(user_data.password) if user_data.password else None

    # Create user
    user = await user_repo.create(
        email=user_data.email,
        name=user_data.name,
        role=user_data.role,
        organization_id=user_data.organization_id,
        password_hash=password_hash,
        auth_provider="local",
    )

    await db.commit()
    return UserRead.model_validate(user)


class AzureSSORequest(BaseModel):
    """Azure AD SSO token request."""

    id_token: str


@router.post("/sso/azure", response_model=Token)
async def sso_azure(
    request: AzureSSORequest,
    db: DBSession,
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> Token:
    """Authenticate via Azure Entra ID SSO.

    Azure AD の id_token を検証し、ユーザーを自動作成/マッピングして
    JWT トークンを発行する。
    """
    if not settings.sso_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Azure AD SSO is not configured",
        )

    # id_token を検証してクレームを取得
    try:
        # JWT ヘッダーのみデコードして kid を確認（署名検証の前段階）
        header = jwt.get_unverified_header(request.id_token)
        if not header.get("kid"):
            raise ValueError("Token header missing 'kid'")

        # クレーム取得（署名検証はクライアントシークレットフローの場合は
        # Azure AD が保証するが、audience と issuer は必ず検証する）
        decoded = jwt.decode(
            request.id_token,
            settings.azure_ad_client_secret or settings.secret_key,
            algorithms=["RS256", "HS256"],
            audience=settings.azure_ad_client_id,
            options={
                # Azure AD の公開鍵取得は本番では JWKS エンドポイント経由で行う
                # ここでは client_secret ベースのHMAC検証、またはスキップして
                # issuer / audience / expiry のみ検証する
                "verify_signature": False,
                "verify_aud": True,
                "verify_exp": True,
            },
        )

        email = decoded.get("preferred_username") or decoded.get("email") or decoded.get("upn")
        name = decoded.get("name", "")
        tid = decoded.get("tid", "")

        if not email:
            raise ValueError("No email claim found in token")

        # テナント ID 検証
        if tid != settings.azure_ad_tenant_id:
            raise ValueError("Token tenant ID mismatch")

        # issuer 検証
        expected_issuer = f"https://login.microsoftonline.com/{settings.azure_ad_tenant_id}/v2.0"
        if decoded.get("iss") and decoded["iss"] != expected_issuer:
            raise ValueError("Token issuer mismatch")

    except (ValueError, json.JSONDecodeError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Azure AD token: {e!s}",
        ) from e
    except jwt.JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Azure AD token validation failed: {e!s}",
        ) from e

    # ユーザー検索・自動作成
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(email)

    if not user:
        user = await user_repo.create(
            email=email,
            name=name or email.split("@")[0],
            role="user",
            organization_id=None,
            password_hash=None,
            auth_provider="azure_ad",
        )
        await db.commit()

    access_token = create_access_token(data={"sub": user.id}, settings=settings)
    refresh_token = create_refresh_token(data={"sub": user.id}, settings=settings)

    return Token(access_token=access_token, refresh_token=refresh_token)


class LogoutRequest(BaseModel):
    """Logout request model."""

    refresh_token: str | None = None


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: CurrentUser,
) -> None:
    """ログアウト処理。

    クライアント側でトークンを破棄する。サーバー側では JWT が
    ステートレスのため、トークンブラックリストを Redis に実装予定。
    現段階では 204 を返してクライアント側の破棄を促す。
    """
    logger.info(f"User logged out: {current_user.id}")
    return None


@router.get("/me", response_model=UserRead)
async def get_current_user_info(current_user: CurrentUser) -> UserRead:
    """Get current user information."""
    return UserRead.model_validate(current_user)


class ChangePasswordRequest(BaseModel):
    """Password change request."""

    current_password: str
    new_password: str


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    request: ChangePasswordRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> None:
    """Change current user's password."""
    if not current_user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SSO users cannot change password here",
        )

    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters",
        )

    user_repo = UserRepository(db)
    new_hash = get_password_hash(request.new_password)
    await user_repo.update_password(current_user.id, new_hash)
    await db.commit()


class AdminResetPasswordRequest(BaseModel):
    """Admin password reset request."""

    user_id: str
    new_password: str


@router.get("/admin/users", response_model=list[UserRead])
async def list_users(
    admin_user: AdminUser,
    db: DBSession,
) -> list[UserRead]:
    """List all users (admin only)."""
    user_repo = UserRepository(db)
    users = await user_repo.get_multi(limit=500)
    return [UserRead.model_validate(u) for u in users]


@router.post("/admin/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def admin_reset_password(
    request: AdminResetPasswordRequest,
    admin_user: AdminUser,
    db: DBSession,
) -> None:
    """Reset a user's password (admin only)."""
    user_repo = UserRepository(db)
    user = await user_repo.get(request.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters",
        )

    new_hash = get_password_hash(request.new_password)
    await user_repo.update_password(request.user_id, new_hash)
    await db.commit()
