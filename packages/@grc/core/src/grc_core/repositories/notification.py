"""Notification repository."""

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from grc_core.models.notification import Notification
from grc_core.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    """Repository for notification operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Notification)

    async def get_for_user(
        self,
        user_id: str,
        *,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Notification]:
        """Get notifications for a user, newest first."""
        query = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        if unread_only:
            query = query.where(Notification.is_read.is_(False))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def unread_count(self, user_id: str) -> int:
        """Count unread notifications for a user."""
        result = await self.session.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )
        return result.scalar() or 0

    async def mark_read(self, notification_id: str, user_id: str) -> Notification | None:
        """Mark a single notification as read."""
        notif = await self.get(notification_id)
        if notif is None or notif.user_id != user_id:
            return None
        notif.is_read = True
        await self.session.flush()
        await self.session.refresh(notif)
        return notif

    async def mark_all_read(self, user_id: str) -> int:
        """Mark all notifications as read for a user. Returns updated count."""
        result = await self.session.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .values(is_read=True)
        )
        await self.session.flush()
        return result.rowcount  # type: ignore[return-value]
