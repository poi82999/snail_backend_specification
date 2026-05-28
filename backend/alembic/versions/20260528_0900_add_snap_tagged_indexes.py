"""add snap tagged design/shop indexes

Revision ID: 20260528_0900
Revises: 20260527_1400
Create Date: 2026-05-28 09:00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260528_0900"
down_revision: str | None = "20260527_1400"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_snaps_tagged_design_created
          ON snaps (tagged_design_id, created_at DESC)
          WHERE tagged_design_id IS NOT NULL AND deleted_at IS NULL
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_snaps_tagged_shop_created
          ON snaps (tagged_shop_id, created_at DESC)
          WHERE tagged_shop_id IS NOT NULL AND deleted_at IS NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_snaps_tagged_shop_created")
    op.execute("DROP INDEX IF EXISTS ix_snaps_tagged_design_created")
