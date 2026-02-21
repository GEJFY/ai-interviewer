"""Notification schemas."""

from datetime import datetime

from grc_core.schemas.base import BaseSchema


class NotificationRead(BaseSchema):
    """Notification response schema."""

    id: str
    notification_type: str
    title: str
    message: str
    link: str | None = None
    is_read: bool
    created_at: datetime


class NotificationCreate(BaseSchema):
    """Schema for creating a notification (internal use)."""

    user_id: str
    notification_type: str
    title: str
    message: str
    link: str | None = None


class UnreadCountResponse(BaseSchema):
    """Response containing unread notification count."""

    unread_count: int
