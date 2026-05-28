"""add users.image_view_mode

Revision ID: 20260528_0920
Revises: 20260528_0910
Create Date: 2026-05-28 09:20:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260528_0920"
down_revision: str | None = "20260528_0910"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "image_view_mode",
            sa.String(length=10),
            nullable=False,
            server_default="MODEL",
        ),
    )
    op.create_check_constraint(
        "ck_users_image_view_mode",
        "users",
        "image_view_mode IN ('MODEL', 'WEAR')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_image_view_mode", "users", type_="check")
    op.drop_column("users", "image_view_mode")
