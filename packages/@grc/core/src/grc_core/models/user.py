"""User model."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from grc_core.enums import UserRole
from grc_core.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from grc_core.models.interview import Interview
    from grc_core.models.notification import Notification
    from grc_core.models.organization import Organization
    from grc_core.models.project import Project
    from grc_core.models.report import Report
    from grc_core.models.task import InterviewTask
    from grc_core.models.template import Template


class User(Base, TimestampMixin):
    """User entity - represents system users (interviewers, admins, etc.)."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(String(50), nullable=False, default=UserRole.VIEWER)

    organization_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=True
    )

    # Authentication
    auth_provider: Mapped[str] = mapped_column(String(50), nullable=False, default="local")
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    organization: Mapped["Organization | None"] = relationship(
        "Organization", back_populates="users"
    )
    created_projects: Mapped[list["Project"]] = relationship(
        "Project", back_populates="created_by_user", foreign_keys="Project.created_by"
    )
    created_tasks: Mapped[list["InterviewTask"]] = relationship(
        "InterviewTask",
        back_populates="created_by_user",
        foreign_keys="InterviewTask.created_by",
    )
    created_templates: Mapped[list["Template"]] = relationship(
        "Template", back_populates="created_by_user", foreign_keys="Template.created_by"
    )
    conducted_interviews: Mapped[list["Interview"]] = relationship(
        "Interview",
        back_populates="interviewer",
        foreign_keys="Interview.interviewer_id",
    )
    created_reports: Mapped[list["Report"]] = relationship(
        "Report", back_populates="created_by_user", foreign_keys="Report.created_by"
    )
    approved_reports: Mapped[list["Report"]] = relationship(
        "Report", back_populates="approved_by_user", foreign_keys="Report.approved_by"
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )
