"""User schemas."""

from datetime import datetime

from pydantic import EmailStr

from grc_core.enums import UserRole
from grc_core.schemas.base import BaseSchema


class UserBase(BaseSchema):
    """Base user schema."""

    email: EmailStr
    name: str
    role: UserRole = UserRole.VIEWER


class UserCreate(UserBase):
    """Schema for creating a user."""

    password: str | None = None
    organization_id: str | None = None


class UserUpdate(BaseSchema):
    """Schema for updating a user."""

    email: EmailStr | None = None
    name: str | None = None
    role: UserRole | None = None
    mfa_enabled: bool | None = None


class UserRead(UserBase):
    """Schema for reading a user."""

    id: str
    organization_id: str | None = None
    auth_provider: str
    mfa_enabled: bool
    created_at: datetime
    updated_at: datetime
