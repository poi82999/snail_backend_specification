from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import AppError
from app.models.enums import ActorType
from app.models.reservation import IdempotencyKey


def hash_request(method: str, path: str, body_bytes: bytes) -> str:
    digest = sha256()
    digest.update(method.upper().encode("utf-8"))
    digest.update(b"\n")
    digest.update(path.encode("utf-8"))
    digest.update(b"\n")
    digest.update(body_bytes)
    return digest.hexdigest()


@dataclass(slots=True)
class IdempotencyContext:
    record: IdempotencyKey | None
    is_cached: bool = False
    response_status: int | None = None
    response_body: dict[str, object] | None = None

    @property
    def cached(self) -> bool:
        return self.is_cached

    @classmethod
    def cached_response(
        cls,
        response_status: int | None,
        response_body: dict[str, object] | None,
    ) -> "IdempotencyContext":
        return cls(
            record=None,
            is_cached=True,
            response_status=response_status,
            response_body=response_body,
        )

    def set_response(
        self,
        status: int,
        body: Mapping[str, object] | None,
    ) -> None:
        self.response_status = status
        self.response_body = dict(body) if body is not None else None


def _actor_type_value(actor_type: ActorType | str) -> str:
    return actor_type.value if isinstance(actor_type, ActorType) else actor_type


@asynccontextmanager
async def with_idempotency(
    session: AsyncSession,
    actor_type: ActorType | str,
    actor_id: UUID,
    key: str,
    request_hash: str,
    ttl_hours: int = 24,
) -> AsyncIterator[IdempotencyContext]:
    """
    FastAPI service usage:

        async with with_idempotency(session, ActorType.USER, user_id, key, req_hash) as idem:
            if idem.cached:
                return JSONResponse(status_code=idem.response_status, content=idem.response_body)
            body = {"reservation_id": str(reservation.id)}
            idem.set_response(201, body)
            return body

    The surrounding service transaction should commit the domain write and idempotency row together.
    """
    actor_type_value = _actor_type_value(actor_type)
    statement = (
        select(IdempotencyKey)
        .where(
            IdempotencyKey.actor_type == actor_type_value,
            IdempotencyKey.actor_id == actor_id,
            IdempotencyKey.key == key,
        )
        .with_for_update()
    )
    result = await session.execute(statement)
    existing = result.scalar_one_or_none()

    if existing is not None:
        if existing.request_hash != request_hash:
            raise AppError(
                "IDEMPOTENCY_MISMATCH",
                "동일한 멱등키로 다른 요청을 처리할 수 없습니다.",
                HTTPStatus.CONFLICT,
            )
        yield IdempotencyContext.cached_response(existing.response_status, existing.response_body)
        return

    now = datetime.now(UTC)
    record = IdempotencyKey(
        actor_type=actor_type_value,
        actor_id=actor_id,
        key=key,
        request_hash=request_hash,
        expires_at=now + timedelta(hours=ttl_hours),
    )
    session.add(record)
    await session.flush()

    context = IdempotencyContext(record=record)
    try:
        yield context
    except Exception:
        raise
    else:
        if context.response_status is not None:
            record.response_status = context.response_status
            record.response_body = context.response_body
            await session.flush()


def idempotency_key_header(
    x_idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> str | None:
    return x_idempotency_key
