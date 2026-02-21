"""Notification endpoints."""

from fastapi import APIRouter, Query

from grc_backend.api.deps import CurrentUser, DBSession
from grc_core.repositories import NotificationRepository
from grc_core.schemas import NotificationRead, UnreadCountResponse
from grc_core.schemas.base import PaginatedResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse[NotificationRead])
async def list_notifications(
    db: DBSession,
    current_user: CurrentUser,
    unread_only: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[NotificationRead]:
    """List notifications for the current user."""
    repo = NotificationRepository(db)
    skip = (page - 1) * page_size
    notifications = await repo.get_for_user(
        current_user.id,
        unread_only=unread_only,
        skip=skip,
        limit=page_size,
    )
    total = (
        await repo.unread_count(current_user.id)
        if unread_only
        else await repo.count(filters={"user_id": current_user.id})
    )
    return PaginatedResponse(
        items=[NotificationRead.model_validate(n) for n in notifications],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if total else 0,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    db: DBSession,
    current_user: CurrentUser,
) -> UnreadCountResponse:
    """Get unread notification count for the current user."""
    repo = NotificationRepository(db)
    count = await repo.unread_count(current_user.id)
    return UnreadCountResponse(unread_count=count)


@router.post("/{notification_id}/read", response_model=NotificationRead)
async def mark_as_read(
    notification_id: str,
    db: DBSession,
    current_user: CurrentUser,
) -> NotificationRead:
    """Mark a notification as read."""
    repo = NotificationRepository(db)
    notif = await repo.mark_read(notification_id, current_user.id)
    if not notif:
        from grc_backend.core.errors import NotFoundError

        raise NotFoundError(
            message="Notification not found",
            resource_type="Notification",
            resource_id=notification_id,
        )
    await db.commit()
    return NotificationRead.model_validate(notif)


@router.post("/read-all")
async def mark_all_as_read(
    db: DBSession,
    current_user: CurrentUser,
) -> dict[str, int]:
    """Mark all notifications as read for the current user."""
    repo = NotificationRepository(db)
    updated = await repo.mark_all_read(current_user.id)
    await db.commit()
    return {"updated": updated}
