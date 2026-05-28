"""add user oauth identities

Revision ID: 20260527_1000
Revises: 20260527_0900
Create Date: 2026-05-27 10:00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260527_1000"
down_revision: str | None = "20260527_0900"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE user_oauth_identities (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id),
            provider VARCHAR(40) NOT NULL,
            provider_sub VARCHAR(255) NOT NULL,
            email VARCHAR(320),
            raw_payload JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_user_oauth_identities_provider_sub UNIQUE (provider, provider_sub)
        );

        CREATE INDEX ix_user_oauth_identities_user_id
          ON user_oauth_identities (user_id);
        """
    )
    op.execute(
        """
        INSERT INTO user_oauth_identities (
            id,
            user_id,
            provider,
            provider_sub,
            email,
            raw_payload,
            created_at,
            updated_at
        )
        SELECT
            uuid_generate_v4(),
            users.id,
            'apple',
            users.apple_sub,
            users.email,
            NULL,
            now(),
            now()
        FROM users
        WHERE users.apple_sub IS NOT NULL
        ON CONFLICT (provider, provider_sub) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS user_oauth_identities")
