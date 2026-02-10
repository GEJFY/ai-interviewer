"""Interview Task model."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from grc_core.enums import TaskStatus, UseCaseType
from grc_core.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from grc_core.models.interview import Interview
    from grc_core.models.project import Project
    from grc_core.models.report import Report
    from grc_core.models.template import Template
    from grc_core.models.user import User


class InterviewTask(Base, TimestampMixin):
    """Interview Task entity - a batch of interviews to be conducted."""

    __tablename__ = "interview_tasks"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    use_case_type: Mapped[UseCaseType] = mapped_column(String(100), nullable=False)

    project_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    template_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("templates.id"), nullable=True
    )
    created_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=True
    )

    target_count: Mapped[int] = mapped_column(Integer, default=1)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        String(50), nullable=False, default=TaskStatus.PENDING
    )

    # Settings: anonymous_mode, language, etc.
    settings: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default="{}")

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
    template: Mapped["Template | None"] = relationship("Template", back_populates="tasks")
    created_by_user: Mapped["User | None"] = relationship(
        "User", back_populates="created_tasks", foreign_keys=[created_by]
    )
    interviews: Mapped[list["Interview"]] = relationship(
        "Interview", back_populates="task", cascade="all, delete-orphan"
    )
    reports: Mapped[list["Report"]] = relationship(
        "Report", back_populates="task", foreign_keys="Report.task_id"
    )
