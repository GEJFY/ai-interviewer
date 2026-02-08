"""Project model."""

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from grc_core.enums import ProjectStatus
from grc_core.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from grc_core.models.organization import Organization
    from grc_core.models.user import User
    from grc_core.models.task import InterviewTask


class Project(Base, TimestampMixin):
    """Project entity - represents an audit/advisory engagement."""

    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    organization_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=True
    )
    created_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=True
    )

    status: Mapped[ProjectStatus] = mapped_column(
        String(50), nullable=False, default=ProjectStatus.ACTIVE
    )
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Relationships
    organization: Mapped["Organization | None"] = relationship(
        "Organization", back_populates="projects"
    )
    created_by_user: Mapped["User | None"] = relationship(
        "User", back_populates="created_projects", foreign_keys=[created_by]
    )
    tasks: Mapped[list["InterviewTask"]] = relationship(
        "InterviewTask", back_populates="project", cascade="all, delete-orphan"
    )
