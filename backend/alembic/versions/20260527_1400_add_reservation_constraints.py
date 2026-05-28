"""add reservation slot constraints and lookup indexes

Revision ID: 20260527_1400
Revises: 20260527_1310
Create Date: 2026-05-27 14:00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260527_1400"
down_revision: str | None = "20260527_1310"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.execute(
        """
        ALTER TABLE reservations
        ADD CONSTRAINT excl_designer_slot_lock
        EXCLUDE USING gist (
            designer_id WITH =,
            tstzrange(start_at, end_at, '[)') WITH &&
        )
        WHERE (status IN ('PAYMENT_PENDING', 'CONFIRMED'))
        """
    )
    op.execute(
        """
        ALTER TABLE reservations
        ADD CONSTRAINT excl_user_active_overlap
        EXCLUDE USING gist (
            user_id WITH =,
            tstzrange(start_at, end_at, '[)') WITH &&
        )
        WHERE (status IN ('PENDING', 'PAYMENT_PENDING', 'CONFIRMED'))
        """
    )
    op.execute(
        """
        CREATE INDEX ix_reservations_shop_status_start
        ON reservations (shop_id, status, start_at)
        """
    )
    op.execute(
        """
        CREATE INDEX ix_reservations_user_status_start_desc
        ON reservations (user_id, status, start_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX ix_reservations_designer_start
        ON reservations (designer_id, start_at)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_reservations_designer_start")
    op.execute("DROP INDEX IF EXISTS ix_reservations_user_status_start_desc")
    op.execute("DROP INDEX IF EXISTS ix_reservations_shop_status_start")
    op.execute("ALTER TABLE reservations DROP CONSTRAINT IF EXISTS excl_user_active_overlap")
    op.execute("ALTER TABLE reservations DROP CONSTRAINT IF EXISTS excl_designer_slot_lock")
