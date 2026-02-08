"""Authentication endpoints."""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

from grc_backend.api.deps import DBSession, CurrentUser, get_settings_dep
from grc_backend.config import Settings
from grc_core.repositories import UserRepository
from grc_core.schemas import UserCreate, UserRead

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
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(data: dict, settings: Settings) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
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

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

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


@router.get("/me", response_model=UserRead)
async def get_current_user_info(current_user: CurrentUser) -> UserRead:
    """Get current user information."""
    return UserRead.model_validate(current_user)
