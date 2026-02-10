"""User repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from grc_core.enums import UserRole
from grc_core.models.user import User
from grc_core.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_external_id(self, auth_provider: str, external_id: str) -> User | None:
        """Get user by external auth ID (for SSO)."""
        result = await self.session.execute(
            select(User).where(
                User.auth_provider == auth_provider,
                User.external_id == external_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_organization(
        self,
        organization_id: str,
        *,
        role: UserRole | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """Get users by organization."""
        query = select(User).where(User.organization_id == organization_id)

        if role:
            query = query.where(User.role == role)

        query = query.offset(skip).limit(limit).order_by(User.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def email_exists(self, email: str) -> bool:
        """Check if email is already registered."""
        user = await self.get_by_email(email)
        return user is not None

    async def update_password(self, id: str, password_hash: str) -> User | None:
        """Update user's password hash."""
        return await self.update(id, password_hash=password_hash)

    async def enable_mfa(self, id: str) -> User | None:
        """Enable MFA for a user."""
        return await self.update(id, mfa_enabled=True)

    async def disable_mfa(self, id: str) -> User | None:
        """Disable MFA for a user."""
        return await self.update(id, mfa_enabled=False)
