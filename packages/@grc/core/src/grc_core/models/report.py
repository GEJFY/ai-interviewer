"""Report model."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from grc_core.enums import ReportStatus, ReportType
from grc_core.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from grc_core.models.interview import Interview
    from grc_core.models.task import InterviewTask
    from grc_core.models.user import User


class Report(Base, TimestampMixin):
    """Report entity - generated documents from interviews."""

    __tablename__ = "reports"

    interview_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("interviews.id"), nullable=True
    )
    task_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("interview_tasks.id"), nullable=True
    )
    created_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=True
    )
    approved_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=True
    )

    report_type: Mapped[ReportType] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    # Report content (structure varies by report_type)
    content: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    format: Mapped[str] = mapped_column(String(50), default="json")

    status: Mapped[ReportStatus] = mapped_column(
        String(50), nullable=False, default=ReportStatus.DRAFT
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    interview: Mapped["Interview | None"] = relationship(
        "Interview", back_populates="reports", foreign_keys=[interview_id]
    )
    task: Mapped["InterviewTask | None"] = relationship(
        "InterviewTask", back_populates="reports", foreign_keys=[task_id]
    )
    created_by_user: Mapped["User | None"] = relationship(
        "User", back_populates="created_reports", foreign_keys=[created_by]
    )
    approved_by_user: Mapped["User | None"] = relationship(
        "User", back_populates="approved_reports", foreign_keys=[approved_by]
    )
