"""add pre-a5 foreign key indexes

Revision ID: 20260527_1300
Revises: 20260527_1200
Create Date: 2026-05-27 13:00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260527_1300"
down_revision: str | None = "20260527_1200"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE INDEX IF NOT EXISTS ix_designs_shop_id ON designs (shop_id)")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_designs_deleted_at_active
          ON designs (deleted_at)
          WHERE deleted_at IS NULL
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_snaps_user_id ON snaps (user_id)")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_snaps_deleted_at_active
          ON snaps (deleted_at)
          WHERE deleted_at IS NULL
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_comments_snap_id ON comments (snap_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_comments_parent_id ON comments (parent_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_comments_author_id ON comments (author_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_reviews_shop_id ON reviews (shop_id)")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_reports_target
          ON reports (target_type, target_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_user_follows_following_id
          ON user_follows (following_id)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_user_follows_following_id")
    op.execute("DROP INDEX IF EXISTS ix_reports_target")
    op.execute("DROP INDEX IF EXISTS ix_reviews_shop_id")
    op.execute("DROP INDEX IF EXISTS ix_comments_author_id")
    op.execute("DROP INDEX IF EXISTS ix_comments_parent_id")
    op.execute("DROP INDEX IF EXISTS ix_comments_snap_id")
    op.execute("DROP INDEX IF EXISTS ix_snaps_deleted_at_active")
    op.execute("DROP INDEX IF EXISTS ix_snaps_user_id")
    op.execute("DROP INDEX IF EXISTS ix_designs_deleted_at_active")
    op.execute("DROP INDEX IF EXISTS ix_designs_shop_id")
