"""Notification helper — fire-and-forget notification creation.

Usage from any route / service that has a DB session::

    from grc_backend.core.notifications import notify
    await notify(db, user_id=..., type="interview_completed", ...)
"""

from sqlalchemy.ext.asyncio import AsyncSession

from grc_core.repositories import NotificationRepository


async def notify(
    db: AsyncSession,
    *,
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    link: str | None = None,
) -> None:
    """Create a notification for a user.

    This is a convenience wrapper so callers don't need to import the
    repository directly.  The caller is responsible for committing the
    session (usually done at the end of the request).
    """
    repo = NotificationRepository(db)
    await repo.create(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link,
    )
