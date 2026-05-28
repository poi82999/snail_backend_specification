# DB Schema Notes

Source of truth:

- SQLAlchemy models: `app/models/*.py`
- Alembic migrations: `alembic/versions/*.py`

Current initial schema creates 31 tables.

## Core Tables

| Area | Tables |
| --- | --- |
| Accounts | `users`, `user_device_tokens`, `owners`, `business_verifications`, `password_reset_tokens` |
| Shop | `shops`, `shop_images`, `shop_business_hours` |
| Designer | `designers`, `designer_schedules`, `designer_time_offs` |
| Design | `designs`, `design_images`, `design_designers`, `llm_jobs` |
| Reservation | `reservations`, `idempotency_keys` |
| Community | `snaps`, `snap_images`, `snap_likes`, `comments`, `comment_likes`, `user_follows`, `favorite_designs` |
| Review | `reviews`, `review_images`, `review_replies` |
| Ops | `reports`, `owner_notifications`, `notification_deliveries`, `upload_objects` |

## Important Constraints

- `shops.owner_id` is unique for MVP 1 owner = 1 shop.
- `shops` rejects `auto_accept=true` with `payment_method=bank_transfer_guide`.
- `reviews.reservation_id` is unique for 1 reservation = max 1 review.
- `comments.depth` is limited to 1 or 2.
- `upload_objects.byte_size` is limited to 10 MB.
- `reservations.idempotency_key` is unique.
- Designer slot hard lock:
  - exclusion constraint blocks overlapping `payment_pending` or `confirmed` reservations for the same designer.
  - `pending` does not lock the slot.
- User active overlap:
  - exclusion constraint blocks overlapping `pending`, `payment_pending`, or `confirmed` reservations for the same user.

## Search

검색은 별도 엔진 없이 PostgreSQL 내에서 수행:

- `pg_trgm` GIN: `designs.title`, `designs.description` 오타/유사도
- ARRAY GIN: `designs.ai_tags`, `designs.owner_tags`, `designs.color_palette`
- `pgvector` HNSW(또는 IVFFlat): `designs.embedding vector(1536)` — OpenAI text-embedding-3-small. 컬럼은 A4가 마이그레이션으로 추가
- 지리 검색: `(longitude, latitude)`에 GiST 인덱스 (Shop)

Public search exposure must require:

```text
owner.verification_status = approved
AND shop.visibility = active
AND design.visibility = active
AND design.ai_analysis_status = done
AND design.deleted_at IS NULL
```

## Migration Policy

- Write SQLAlchemy model changes first.
- Generate or hand-write Alembic revision.
- Review destructive changes manually.
- In production, prefer forward-only fixes over downgrade-based rollback.
