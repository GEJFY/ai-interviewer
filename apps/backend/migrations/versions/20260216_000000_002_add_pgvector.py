"""Add pgvector extension and vector column for knowledge items

Revision ID: 002
Revises: 001
Create Date: 2026-02-16 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Add a native vector column alongside the existing JSONB embedding column
    # This allows a gradual migration: existing code still works with JSONB,
    # while new queries can use the optimized vector column.
    op.add_column(
        "knowledge_items",
        sa.Column("embedding_vector", sa.Text(), nullable=True),
    )

    # Use raw SQL to set the proper vector type (1536 dimensions for OpenAI embeddings)
    op.execute(
        "ALTER TABLE knowledge_items "
        "ALTER COLUMN embedding_vector TYPE vector(1536) "
        "USING embedding_vector::vector(1536)"
    )

    # Create IVFFlat index for approximate nearest neighbor search
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_knowledge_items_embedding_vector "
        "ON knowledge_items USING ivfflat (embedding_vector vector_cosine_ops) "
        "WITH (lists = 100)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_knowledge_items_embedding_vector")
    op.drop_column("knowledge_items", "embedding_vector")
    op.execute("DROP EXTENSION IF EXISTS vector")
