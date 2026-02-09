"""Transcript entry model."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from grc_core.enums import Speaker
from grc_core.models.base import Base

if TYPE_CHECKING:
    from grc_core.models.interview import Interview


class TranscriptEntry(Base):
    """Transcript entry - a single utterance in an interview."""

    __tablename__ = "transcript_entries"

    interview_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("interviews.id", ondelete="CASCADE"),
        nullable=False,
    )

    speaker: Mapped[Speaker] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_translated: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timing information
    timestamp_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Speech recognition confidence (0.0 - 1.0)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Edit tracking
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False)
    original_content: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    interview: Mapped["Interview"] = relationship("Interview", back_populates="transcript_entries")
