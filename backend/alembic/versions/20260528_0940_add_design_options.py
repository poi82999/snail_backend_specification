"""add design_options + reservations.selected_option_ids

Revision ID: 20260528_0940
Revises: 20260528_0930
Create Date: 2026-05-28 09:40:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "20260528_0940"
down_revision: str | None = "20260528_0930"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "design_options",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("design_id", sa.UUID(as_uuid=True), sa.ForeignKey("designs.id"), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("price_delta", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_delta_min", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
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
        sa.CheckConstraint("kind IN ('EXTEND', 'REMOVAL', 'CARE')", name="ck_design_options_kind"),
    )
    op.create_index("ix_design_options_design_id", "design_options", ["design_id"])
    op.add_column(
        "reservations",
        sa.Column(
            "selected_option_ids",
            JSONB(),
            nullable=False,
            server_default="[]",
        ),
    )


def downgrade() -> None:
    op.drop_column("reservations", "selected_option_ids")
    op.drop_index("ix_design_options_design_id", table_name="design_options")
    op.drop_table("design_options")
