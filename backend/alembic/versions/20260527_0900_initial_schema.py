"""initial schema

Revision ID: 20260527_0900
Revises:
Create Date: 2026-05-27 09:00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260527_0900"
down_revision: str | None = "0001_initial_extensions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE users (
            id UUID PRIMARY KEY,
            apple_sub VARCHAR(255) UNIQUE,
            email VARCHAR(320) UNIQUE,
            nickname VARCHAR(40) NOT NULL UNIQUE,
            profile_image_url TEXT,
            bio VARCHAR(200),
            interest_tags VARCHAR(40)[] NOT NULL DEFAULT '{}',
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE owners (
            id UUID PRIMARY KEY,
            email VARCHAR(320) NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            representative_name VARCHAR(80) NOT NULL,
            phone_number VARCHAR(30) NOT NULL,
            verification_status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
            verification_rejected_reason TEXT,
            login_failed_count INTEGER NOT NULL DEFAULT 0,
            locked_until TIMESTAMPTZ,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_owners_verification_status
              CHECK (verification_status IN ('PENDING','APPROVED','REJECTED'))
        );

        CREATE TABLE business_verifications (
            id UUID PRIMARY KEY,
            owner_id UUID NOT NULL REFERENCES owners(id),
            business_registration_number VARCHAR(40) NOT NULL,
            document_url TEXT NOT NULL,
            status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
            reviewed_at TIMESTAMPTZ,
            rejected_reason TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_business_verifications_status
              CHECK (status IN ('PENDING','APPROVED','REJECTED'))
        );

        CREATE TABLE password_reset_tokens (
            id UUID PRIMARY KEY,
            owner_id UUID NOT NULL REFERENCES owners(id),
            token_hash TEXT NOT NULL UNIQUE,
            expires_at TIMESTAMPTZ NOT NULL,
            used_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE user_device_tokens (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id),
            token TEXT NOT NULL,
            platform VARCHAR(20) NOT NULL DEFAULT 'ios',
            is_active BOOLEAN NOT NULL DEFAULT true,
            last_seen_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_user_device_tokens_user_token UNIQUE (user_id, token)
        );

        CREATE TABLE shops (
            id UUID PRIMARY KEY,
            owner_id UUID NOT NULL UNIQUE REFERENCES owners(id),
            name VARCHAR(120) NOT NULL,
            address TEXT NOT NULL,
            address_detail TEXT,
            region VARCHAR(80),
            latitude NUMERIC(9, 6),
            longitude NUMERIC(9, 6),
            phone_number VARCHAR(30) NOT NULL,
            introduction TEXT,
            thumbnail_url TEXT,
            visibility VARCHAR(30) NOT NULL DEFAULT 'DRAFT',
            auto_accept BOOLEAN NOT NULL DEFAULT false,
            reservation_policy TEXT,
            payment_method VARCHAR(40) NOT NULL DEFAULT 'ON_SITE',
            deposit_amount INTEGER,
            bank_name VARCHAR(80),
            bank_account_number VARCHAR(80),
            bank_account_holder VARCHAR(80),
            average_rating NUMERIC(3, 2) NOT NULL DEFAULT 0,
            review_count INTEGER NOT NULL DEFAULT 0,
            favorite_count INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_shops_visibility CHECK (visibility IN ('DRAFT','ACTIVE','HIDDEN')),
            CONSTRAINT ck_shops_payment_method
              CHECK (payment_method IN ('ON_SITE','BANK_TRANSFER_GUIDE')),
            CONSTRAINT ck_shops_auto_accept_payment
              CHECK (NOT auto_accept OR payment_method = 'ON_SITE'),
            CONSTRAINT ck_shops_deposit
              CHECK (
                (payment_method = 'ON_SITE' AND deposit_amount IS NULL)
                OR (payment_method = 'BANK_TRANSFER_GUIDE' AND deposit_amount >= 1000)
              )
        );

        CREATE TABLE shop_images (
            id UUID PRIMARY KEY,
            shop_id UUID NOT NULL REFERENCES shops(id),
            image_url TEXT NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0,
            is_thumbnail BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE shop_business_hours (
            id UUID PRIMARY KEY,
            shop_id UUID NOT NULL REFERENCES shops(id),
            weekday INTEGER NOT NULL,
            open_time TIME,
            close_time TIME,
            is_closed BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_shop_business_hours_day UNIQUE (shop_id, weekday),
            CONSTRAINT ck_shop_business_hours_weekday CHECK (weekday BETWEEN 0 AND 6)
        );

        CREATE TABLE designers (
            id UUID PRIMARY KEY,
            shop_id UUID NOT NULL REFERENCES shops(id),
            name VARCHAR(80) NOT NULL,
            position VARCHAR(80),
            career_years INTEGER,
            profile_image_url TEXT,
            specialty_tags VARCHAR(40)[] NOT NULL DEFAULT '{}',
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE designer_schedules (
            id UUID PRIMARY KEY,
            designer_id UUID NOT NULL REFERENCES designers(id),
            weekday INTEGER NOT NULL,
            start_time TIME,
            end_time TIME,
            break_start_time TIME,
            break_end_time TIME,
            is_day_off BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_designer_schedules_day UNIQUE (designer_id, weekday),
            CONSTRAINT ck_designer_schedules_weekday CHECK (weekday BETWEEN 0 AND 6)
        );

        CREATE TABLE designer_time_offs (
            id UUID PRIMARY KEY,
            designer_id UUID NOT NULL REFERENCES designers(id),
            off_date DATE NOT NULL,
            start_time TIME,
            end_time TIME,
            reason TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE designs (
            id UUID PRIMARY KEY,
            shop_id UUID NOT NULL REFERENCES shops(id),
            title VARCHAR(120) NOT NULL,
            description TEXT,
            base_price INTEGER NOT NULL,
            duration_minutes INTEGER NOT NULL,
            thumbnail_url TEXT,
            visibility VARCHAR(30) NOT NULL DEFAULT 'DRAFT',
            ai_analysis_status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
            owner_tags VARCHAR(40)[] NOT NULL DEFAULT '{}',
            ai_tags VARCHAR(40)[] NOT NULL DEFAULT '{}',
            color_palette VARCHAR(40)[] NOT NULL DEFAULT '{}',
            style_category VARCHAR(40),
            nail_shape VARCHAR(40),
            ai_confidence NUMERIC(4, 3),
            ai_error_code VARCHAR(80),
            ai_error_message TEXT,
            ai_model_version VARCHAR(120),
            search_indexed_at TIMESTAMPTZ,
            deleted_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_designs_visibility CHECK (visibility IN ('DRAFT','ACTIVE','HIDDEN')),
            CONSTRAINT ck_designs_ai_status
              CHECK (ai_analysis_status IN ('PENDING','IN_PROGRESS','DONE','FAILED')),
            CONSTRAINT ck_designs_price CHECK (base_price >= 0),
            CONSTRAINT ck_designs_duration CHECK (duration_minutes > 0)
        );

        CREATE TABLE design_designers (
            design_id UUID NOT NULL REFERENCES designs(id),
            designer_id UUID NOT NULL REFERENCES designers(id),
            PRIMARY KEY (design_id, designer_id),
            CONSTRAINT uq_design_designers UNIQUE (design_id, designer_id)
        );

        CREATE TABLE design_images (
            id UUID PRIMARY KEY,
            design_id UUID NOT NULL REFERENCES designs(id),
            original_url TEXT NOT NULL,
            processed_url TEXT,
            sort_order INTEGER NOT NULL DEFAULT 0,
            is_thumbnail BOOLEAN NOT NULL DEFAULT false,
            width INTEGER,
            height INTEGER,
            content_hash VARCHAR(128),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE reservations (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id),
            shop_id UUID NOT NULL REFERENCES shops(id),
            design_id UUID NOT NULL REFERENCES designs(id),
            designer_id UUID NOT NULL REFERENCES designers(id),
            assigned_by VARCHAR(30) NOT NULL DEFAULT 'AUTO',
            start_at TIMESTAMPTZ NOT NULL,
            end_at TIMESTAMPTZ NOT NULL,
            status VARCHAR(40) NOT NULL DEFAULT 'PENDING',
            user_request TEXT,
            total_price INTEGER NOT NULL,
            payment_method_snapshot VARCHAR(40) NOT NULL,
            deposit_amount_snapshot INTEGER,
            bank_snapshot JSONB,
            reservation_policy_snapshot TEXT,
            idempotency_key VARCHAR(120) NOT NULL,
            rejected_reason TEXT,
            cancelled_reason TEXT,
            user_payment_notified_at TIMESTAMPTZ,
            owner_payment_confirmed_at TIMESTAMPTZ,
            reminder_sent_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            no_show_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_reservations_idempotency_key UNIQUE (idempotency_key),
            CONSTRAINT ck_reservations_time CHECK (end_at > start_at),
            CONSTRAINT ck_reservations_assigned_by CHECK (assigned_by IN ('USER','AUTO','OWNER')),
            CONSTRAINT ck_reservations_status CHECK (
              status IN (
                'PENDING','PAYMENT_PENDING','CONFIRMED','REJECTED','CANCELLED_BY_USER',
                'CANCELLED_BY_SHOP','NO_SHOW','COMPLETED'
              )
            )
        );

        CREATE TABLE idempotency_keys (
            id UUID PRIMARY KEY,
            actor_type VARCHAR(30) NOT NULL,
            actor_id UUID NOT NULL,
            key VARCHAR(120) NOT NULL,
            request_hash VARCHAR(128) NOT NULL,
            response_status INTEGER,
            response_body JSONB,
            expires_at TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_idempotency_actor_key UNIQUE (actor_type, actor_id, key)
        );

        CREATE TABLE favorite_designs (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id),
            design_id UUID NOT NULL REFERENCES designs(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_favorite_designs_user_design UNIQUE (user_id, design_id)
        );

        CREATE TABLE user_follows (
            id UUID PRIMARY KEY,
            follower_id UUID NOT NULL REFERENCES users(id),
            following_id UUID NOT NULL REFERENCES users(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_user_follows_pair UNIQUE (follower_id, following_id),
            CONSTRAINT ck_user_follows_not_self CHECK (follower_id <> following_id)
        );

        CREATE TABLE snaps (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id),
            tagged_shop_id UUID REFERENCES shops(id),
            tagged_design_id UUID REFERENCES designs(id),
            tagged_designer_id UUID REFERENCES designers(id),
            tagged_reservation_id UUID REFERENCES reservations(id),
            body TEXT,
            tags VARCHAR(40)[] NOT NULL DEFAULT '{}',
            is_reservation_verified BOOLEAN NOT NULL DEFAULT false,
            like_count INTEGER NOT NULL DEFAULT 0,
            comment_count INTEGER NOT NULL DEFAULT 0,
            view_count INTEGER NOT NULL DEFAULT 0,
            deleted_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE snap_images (
            id UUID PRIMARY KEY,
            snap_id UUID NOT NULL REFERENCES snaps(id),
            image_url TEXT NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE snap_likes (
            id UUID PRIMARY KEY,
            snap_id UUID NOT NULL REFERENCES snaps(id),
            user_id UUID NOT NULL REFERENCES users(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_snap_likes_snap_user UNIQUE (snap_id, user_id)
        );

        CREATE TABLE comments (
            id UUID PRIMARY KEY,
            snap_id UUID NOT NULL REFERENCES snaps(id),
            parent_id UUID REFERENCES comments(id),
            author_type VARCHAR(30) NOT NULL,
            author_id UUID NOT NULL,
            body TEXT NOT NULL,
            depth INTEGER NOT NULL DEFAULT 1,
            like_count INTEGER NOT NULL DEFAULT 0,
            deleted_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_comments_author_type CHECK (author_type IN ('USER','OWNER','ADMIN','SYSTEM')),
            CONSTRAINT ck_comments_depth CHECK (depth BETWEEN 1 AND 2)
        );

        CREATE TABLE comment_likes (
            id UUID PRIMARY KEY,
            comment_id UUID NOT NULL REFERENCES comments(id),
            user_id UUID NOT NULL REFERENCES users(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_comment_likes_comment_user UNIQUE (comment_id, user_id)
        );

        CREATE TABLE reviews (
            id UUID PRIMARY KEY,
            reservation_id UUID NOT NULL REFERENCES reservations(id),
            user_id UUID NOT NULL REFERENCES users(id),
            shop_id UUID NOT NULL REFERENCES shops(id),
            design_id UUID NOT NULL REFERENCES designs(id),
            rating INTEGER NOT NULL,
            body TEXT,
            like_count INTEGER NOT NULL DEFAULT 0,
            deleted_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_reviews_reservation UNIQUE (reservation_id),
            CONSTRAINT ck_reviews_rating CHECK (rating BETWEEN 1 AND 5)
        );

        CREATE TABLE review_images (
            id UUID PRIMARY KEY,
            review_id UUID NOT NULL REFERENCES reviews(id),
            image_url TEXT NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE review_replies (
            id UUID PRIMARY KEY,
            review_id UUID NOT NULL REFERENCES reviews(id),
            owner_id UUID NOT NULL REFERENCES owners(id),
            body TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_review_replies_review UNIQUE (review_id)
        );

        CREATE TABLE reports (
            id UUID PRIMARY KEY,
            reporter_user_id UUID REFERENCES users(id),
            target_type VARCHAR(30) NOT NULL,
            target_id UUID NOT NULL,
            reason VARCHAR(80) NOT NULL,
            detail TEXT,
            status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
            action VARCHAR(30) NOT NULL DEFAULT 'NONE',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE llm_jobs (
            id UUID PRIMARY KEY,
            design_id UUID NOT NULL REFERENCES designs(id),
            design_image_id UUID REFERENCES design_images(id),
            job_type VARCHAR(30) NOT NULL,
            status VARCHAR(30) NOT NULL DEFAULT 'QUEUED',
            attempts INTEGER NOT NULL DEFAULT 0,
            request_payload JSONB,
            response_payload JSONB,
            error_code VARCHAR(80),
            error_message TEXT,
            started_at TIMESTAMPTZ,
            finished_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE owner_notifications (
            id UUID PRIMARY KEY,
            owner_id UUID NOT NULL REFERENCES owners(id),
            type VARCHAR(80) NOT NULL,
            title VARCHAR(120) NOT NULL,
            body TEXT NOT NULL,
            resource_type VARCHAR(40),
            resource_id UUID,
            deeplink TEXT,
            read_at TIMESTAMPTZ,
            metadata JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE notification_deliveries (
            id UUID PRIMARY KEY,
            owner_notification_id UUID REFERENCES owner_notifications(id),
            recipient_user_id UUID REFERENCES users(id),
            recipient_owner_id UUID REFERENCES owners(id),
            channel VARCHAR(40) NOT NULL,
            status VARCHAR(30) NOT NULL DEFAULT 'QUEUED',
            template_code VARCHAR(120),
            payload JSONB,
            provider_message_id VARCHAR(160),
            attempts INTEGER NOT NULL DEFAULT 0,
            next_retry_at TIMESTAMPTZ,
            sent_at TIMESTAMPTZ,
            failed_reason TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE upload_objects (
            id UUID PRIMARY KEY,
            owner_actor_type VARCHAR(30) NOT NULL,
            owner_actor_id UUID NOT NULL,
            target_type VARCHAR(40) NOT NULL,
            object_key TEXT NOT NULL UNIQUE,
            content_type VARCHAR(120) NOT NULL,
            byte_size INTEGER NOT NULL,
            original_url TEXT,
            processed_url TEXT,
            uploaded_at TIMESTAMPTZ,
            processed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_upload_objects_size CHECK (byte_size <= 10485760)
        );
        """
    )
    op.execute(
        """
        ALTER TABLE reservations
          ADD CONSTRAINT ex_reservations_designer_hard_lock
          EXCLUDE USING gist (
            designer_id WITH =,
            tstzrange(start_at, end_at, '[)') WITH &&
          )
          WHERE (status IN ('PAYMENT_PENDING', 'CONFIRMED'));

        ALTER TABLE reservations
          ADD CONSTRAINT ex_reservations_user_active_overlap
          EXCLUDE USING gist (
            user_id WITH =,
            tstzrange(start_at, end_at, '[)') WITH &&
          )
          WHERE (status IN ('PENDING', 'PAYMENT_PENDING', 'CONFIRMED'));

        CREATE INDEX ix_shops_region_trgm ON shops USING gin (region gin_trgm_ops);
        CREATE INDEX ix_designs_title_trgm ON designs USING gin (title gin_trgm_ops);
        CREATE INDEX ix_designs_owner_tags ON designs USING gin (owner_tags);
        CREATE INDEX ix_designs_ai_tags ON designs USING gin (ai_tags);
        CREATE INDEX ix_designs_public ON designs (visibility, ai_analysis_status, created_at DESC);
        CREATE INDEX ix_reservations_owner_calendar ON reservations (shop_id, start_at, status);
        CREATE INDEX ix_reservations_user_created ON reservations (user_id, created_at DESC);
        CREATE INDEX ix_snaps_feed ON snaps (created_at DESC) WHERE deleted_at IS NULL;
        CREATE INDEX ix_snaps_tagged_design ON snaps (tagged_design_id, created_at DESC);
        CREATE INDEX ix_reviews_shop_sort ON reviews (shop_id, created_at DESC) WHERE deleted_at IS NULL;
        CREATE INDEX ix_owner_notifications_unread
          ON owner_notifications (owner_id, created_at DESC) WHERE read_at IS NULL;
        CREATE INDEX ix_notification_deliveries_retry
          ON notification_deliveries (status, next_retry_at) WHERE status = 'FAILED';
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS upload_objects;
        DROP TABLE IF EXISTS notification_deliveries;
        DROP TABLE IF EXISTS owner_notifications;
        DROP TABLE IF EXISTS llm_jobs;
        DROP TABLE IF EXISTS reports;
        DROP TABLE IF EXISTS review_replies;
        DROP TABLE IF EXISTS review_images;
        DROP TABLE IF EXISTS reviews;
        DROP TABLE IF EXISTS comment_likes;
        DROP TABLE IF EXISTS comments;
        DROP TABLE IF EXISTS snap_likes;
        DROP TABLE IF EXISTS snap_images;
        DROP TABLE IF EXISTS snaps;
        DROP TABLE IF EXISTS user_follows;
        DROP TABLE IF EXISTS favorite_designs;
        DROP TABLE IF EXISTS idempotency_keys;
        DROP TABLE IF EXISTS reservations;
        DROP TABLE IF EXISTS design_images;
        DROP TABLE IF EXISTS design_designers;
        DROP TABLE IF EXISTS designs;
        DROP TABLE IF EXISTS designer_time_offs;
        DROP TABLE IF EXISTS designer_schedules;
        DROP TABLE IF EXISTS designers;
        DROP TABLE IF EXISTS shop_business_hours;
        DROP TABLE IF EXISTS shop_images;
        DROP TABLE IF EXISTS shops;
        DROP TABLE IF EXISTS user_device_tokens;
        DROP TABLE IF EXISTS password_reset_tokens;
        DROP TABLE IF EXISTS business_verifications;
        DROP TABLE IF EXISTS owners;
        DROP TABLE IF EXISTS users;
        """
    )
