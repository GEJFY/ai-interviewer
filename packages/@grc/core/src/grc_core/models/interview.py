"""Interview model."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from grc_core.enums import InterviewStatus
from grc_core.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from grc_core.models.interviewee import Interviewee
    from grc_core.models.knowledge import KnowledgeItem
    from grc_core.models.report import Report
    from grc_core.models.task import InterviewTask
    from grc_core.models.transcript import TranscriptEntry
    from grc_core.models.user import User


class Interview(Base, TimestampMixin):
    """Interview entity - a single interview session."""

    __tablename__ = "interviews"

    task_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("interview_tasks.id", ondelete="CASCADE"),
        nullable=False,
    )
    interviewee_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("interviewees.id"), nullable=True
    )
    interviewer_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=True
    )

    language: Mapped[str] = mapped_column(String(10), default="ja")
    status: Mapped[InterviewStatus] = mapped_column(
        String(50), nullable=False, default=InterviewStatus.SCHEDULED
    )

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # AI-generated summary
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # AI analysis results (key findings, risks, follow-ups)
    ai_analysis: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Additional metadata (settings, context, etc.)
    extra_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict, server_default="{}"
    )

    # Relationships
    task: Mapped["InterviewTask"] = relationship("InterviewTask", back_populates="interviews")
    interviewee: Mapped["Interviewee | None"] = relationship(
        "Interviewee", back_populates="interviews"
    )
    interviewer: Mapped["User | None"] = relationship(
        "User", back_populates="conducted_interviews", foreign_keys=[interviewer_id]
    )
    transcript_entries: Mapped[list["TranscriptEntry"]] = relationship(
        "TranscriptEntry", back_populates="interview", cascade="all, delete-orphan"
    )
    reports: Mapped[list["Report"]] = relationship(
        "Report", back_populates="interview", foreign_keys="Report.interview_id"
    )
    knowledge_items: Mapped[list["KnowledgeItem"]] = relationship(
        "KnowledgeItem", back_populates="source_interview"
    )
