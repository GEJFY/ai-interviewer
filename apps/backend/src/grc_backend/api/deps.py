"""FastAPI dependencies."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from grc_ai import AIConfig, AIProvider, create_ai_provider
from grc_backend.config import Settings, get_settings
from grc_core.database import get_database
from grc_core.models import User
from grc_core.repositories import UserRepository

# Security
security = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    db = get_database()
    async with db.session() as session:
        yield session


async def get_settings_dep() -> Settings:
    """Get application settings."""
    return get_settings()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError as err:
        raise credentials_exception from err

    user_repo = UserRepository(db)
    user = await user_repo.get(user_id)

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Ensure user is active."""
    # Add any active user checks here
    return current_user


async def require_admin(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """Require admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def require_manager_or_admin(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """Require manager or admin role."""
    if current_user.role not in ("admin", "manager"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager or admin access required",
        )
    return current_user


def get_ai_provider(
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> AIProvider:
    """Get AI provider based on configuration."""
    config_dict = {"provider": settings.ai_provider}

    if settings.ai_provider == "azure" and settings.azure_openai_api_key:
        config_dict["azure"] = {
            "api_key": settings.azure_openai_api_key,
            "endpoint": settings.azure_openai_endpoint,
            "deployment_name": settings.azure_openai_deployment_name,
            "api_version": settings.azure_openai_api_version,
        }
    elif settings.ai_provider == "aws":
        config_dict["aws"] = {
            "access_key_id": settings.aws_access_key_id or None,
            "secret_access_key": settings.aws_secret_access_key or None,
            "region": settings.aws_region,
            "model_id": settings.aws_bedrock_model_id,
        }
    elif settings.ai_provider == "gcp":
        config_dict["gcp"] = {
            "project_id": settings.gcp_project_id,
            "location": settings.gcp_location,
        }

    config = AIConfig(**config_dict)
    return create_ai_provider(config)


# Type aliases for dependency injection
DBSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_active_user)]
AdminUser = Annotated[User, Depends(require_admin)]
ManagerUser = Annotated[User, Depends(require_manager_or_admin)]
AIProviderDep = Annotated[AIProvider, Depends(get_ai_provider)]
