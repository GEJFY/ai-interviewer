"""Knowledge item model for RAG."""

from typing import TYPE_CHECKING, Any

from sqlalchemy import ARRAY, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from grc_core.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from grc_core.models.organization import Organization
    from grc_core.models.interview import Interview


class KnowledgeItem(Base, TimestampMixin):
    """Knowledge item entity - extracted knowledge for RAG."""

    __tablename__ = "knowledge_items"

    organization_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=True
    )
    source_interview_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("interviews.id"), nullable=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    source_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # 'interview', 'document', 'manual'

    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)

    # Vector embedding for similarity search (stored as JSON array)
    # In production, use pgvector extension: Vector(1536)
    embedding: Mapped[list[float] | None] = mapped_column(JSONB, nullable=True)

    # Additional metadata
    extra_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict, server_default="{}"
    )

    # Relationships
    organization: Mapped["Organization | None"] = relationship(
        "Organization", back_populates="knowledge_items"
    )
    source_interview: Mapped["Interview | None"] = relationship(
        "Interview", back_populates="knowledge_items"
    )
