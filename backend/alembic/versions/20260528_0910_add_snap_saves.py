"""add snap_saves table and snaps.save_count

Revision ID: 20260528_0910
Revises: 20260528_0900
Create Date: 2026-05-28 09:10:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260528_0910"
down_revision: str | None = "20260528_0900"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "snaps",
        sa.Column("save_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "snap_saves",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("snap_id", sa.UUID(as_uuid=True), sa.ForeignKey("snaps.id"), nullable=False),
        sa.Column("user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("snap_id", "user_id", name="uq_snap_saves_snap_user"),
    )
    op.create_index("ix_snap_saves_user_id", "snap_saves", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_snap_saves_user_id", table_name="snap_saves")
    op.drop_table("snap_saves")
    op.drop_column("snaps", "save_count")
