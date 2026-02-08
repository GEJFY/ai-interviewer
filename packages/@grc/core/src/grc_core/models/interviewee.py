"""Interviewee model."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from grc_core.models.base import Base

if TYPE_CHECKING:
    from grc_core.models.organization import Organization
    from grc_core.models.interview import Interview


class Interviewee(Base):
    """Interviewee entity - person being interviewed."""

    __tablename__ = "interviewees"

    organization_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=True
    )

    # Personal info (can be null for anonymous interviews)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    position: Mapped[str | None] = mapped_column(String(255), nullable=True)

    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)

    # Additional metadata
    metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, server_default="{}"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    organization: Mapped["Organization | None"] = relationship(
        "Organization", back_populates="interviewees"
    )
    interviews: Mapped[list["Interview"]] = relationship(
        "Interview", back_populates="interviewee"
    )
