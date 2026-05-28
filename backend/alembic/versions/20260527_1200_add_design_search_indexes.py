"""add design search indexes

Revision ID: 20260527_1200
Revises: 20260527_1100
Create Date: 2026-05-27 12:00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260527_1200"
down_revision: str | None = "20260527_1100"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("ALTER TABLE designs ADD COLUMN IF NOT EXISTS embedding vector(1536) NULL")

    context = op.get_context()
    with context.autocommit_block():
        op.execute(
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_designs_embedding
              ON designs USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10)
            """
        )

    op.execute("CREATE INDEX IF NOT EXISTS ix_designs_ai_tags ON designs USING gin (ai_tags)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_designs_owner_tags ON designs USING gin (owner_tags)")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_designs_color_palette
          ON designs USING gin (color_palette)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_designs_title_trgm
          ON designs USING gin (title gin_trgm_ops)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_designs_description_trgm
          ON designs USING gin (description gin_trgm_ops)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_shops_location
          ON shops (latitude, longitude)
          WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_shops_location")
    op.execute("DROP INDEX IF EXISTS ix_designs_description_trgm")
    op.execute("DROP INDEX IF EXISTS ix_designs_color_palette")
    op.execute("DROP INDEX IF EXISTS ix_designs_embedding")
    op.execute("ALTER TABLE designs DROP COLUMN IF EXISTS embedding")
