# Backend Architecture

## Runtime

- FastAPI app: `app/main.py`
- API prefix: `/api/v1`
- DB access: SQLAlchemy 2 async session from `app/core/database.py`
- Cache/queue: Redis from `app/core/redis.py`
- Search: PostgreSQL pg_trgm + ai_tags ARRAY GIN + pgvector (no separate search engine in MVP)
- Common API behavior: request id middleware + common error handlers in `app/api`

## Local Components

```text
iOS app / owner web
  -> FastAPI
      -> PostgreSQL: transactional source of truth + search (pg_trgm + ARRAY GIN + pgvector)
      -> Redis: cache, idempotency TTL, arq jobs
      -> GCS: uploaded image objects
      -> OpenAI / LLM worker: design analysis
      -> APNs / Kakao Alimtalk: notifications
```

## Module Boundaries

| Module | Responsibility |
| --- | --- |
| `app/api` | Routers, request validation, auth dependencies, common errors |
| `app/models` | SQLAlchemy persistence model only |
| `app/schemas` | Pydantic request/response DTOs |
| `app/services` | Domain rules and cross-model workflows |
| `app/workers` | Async background jobs for LLM, image processing, notifications |
| `app/core` | Config, DB, Redis, security, logging |

## MVP Sequence

1. Owner auth and business verification
2. Owner shop/designer/design draft CRUD
3. Design image upload completion and LLM queue enqueue
4. Reservation creation and owner state transitions
5. Search indexing and public design/shop search
6. Owner notification inbox and delivery retries
7. Snaps/reviews/reports

## Guardrails

- Keep a modular monolith. Do not split services before MVP.
- Search runs on Postgres (pg_trgm + ARRAY GIN + pgvector). Defer external search engine until 5K+ designs or p95 > 500ms.
- Do not let UI-only guards enforce business rules. Recheck ownership, verification, status transitions, and reservation conflicts in services.
- API handlers should stay thin: parse input, call service, return DTO.
- Every write path that can be double-clicked or retried needs idempotency or a unique constraint.
