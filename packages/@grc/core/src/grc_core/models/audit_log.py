"""Audit log model for tracking all system actions."""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from grc_core.models.base import Base


class AuditLog(Base):
    """Audit log entry - tracks all user actions for compliance."""

    __tablename__ = "audit_logs"

    user_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=True
    )

    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), nullable=True
    )

    # Action details (before/after state, parameters, etc.)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Request metadata
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
