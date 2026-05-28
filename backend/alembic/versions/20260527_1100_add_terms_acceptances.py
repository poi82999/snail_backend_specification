"""add terms acceptances

Revision ID: 20260527_1100
Revises: 20260527_1000
Create Date: 2026-05-27 11:00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260527_1100"
down_revision: str | None = "20260527_1000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE terms_acceptances (
            id UUID PRIMARY KEY,
            actor_type VARCHAR(30) NOT NULL,
            actor_id UUID NOT NULL,
            policy_type VARCHAR(40) NOT NULL,
            version VARCHAR(20) NOT NULL,
            accepted_at TIMESTAMPTZ NOT NULL,
            ip_address VARCHAR(64),
            user_agent TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_terms_acceptances_actor_policy_version
              UNIQUE (actor_type, actor_id, policy_type, version)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX ix_terms_acceptances_actor
          ON terms_acceptances (actor_type, actor_id)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS terms_acceptances")
