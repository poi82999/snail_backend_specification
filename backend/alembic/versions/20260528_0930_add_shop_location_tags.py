"""add shops.location_tags + geo index

Revision ID: 20260528_0930
Revises: 20260528_0920
Create Date: 2026-05-28 09:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY

revision: str = "20260528_0930"
down_revision: str | None = "20260528_0920"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "shops",
        sa.Column(
            "location_tags",
            ARRAY(sa.String(length=40)),
            nullable=False,
            server_default="{}",
        ),
    )
    op.create_index(
        "ix_shops_location_tags",
        "shops",
        ["location_tags"],
        postgresql_using="gin",
    )
    op.create_index(
        "ix_shops_lat_lng",
        "shops",
        ["latitude", "longitude"],
        postgresql_where=sa.text("latitude IS NOT NULL AND longitude IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_shops_lat_lng", table_name="shops")
    op.drop_index("ix_shops_location_tags", table_name="shops")
    op.drop_column("shops", "location_tags")
