"""replace design embedding index with hnsw

Revision ID: 20260527_1310
Revises: 20260527_1300
Create Date: 2026-05-27 13:10:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260527_1310"
down_revision: str | None = "20260527_1300"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_designs_embedding")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_designs_embedding
          ON designs USING hnsw (embedding vector_cosine_ops)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_designs_embedding")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_designs_embedding
          ON designs USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10)
        """
    )
