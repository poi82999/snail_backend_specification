import base64
from datetime import UTC, datetime
from http import HTTPStatus
from typing import Any, Generic, TypeVar, cast
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import asc, desc, literal, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.api.errors import AppError

T = TypeVar("T")


class CursorParams(BaseModel):
    cursor: str | None = None
    limit: int = Field(20, ge=1, le=50)


class PageResult(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None = None


def encode_cursor(created_at: datetime, id_: UUID) -> str:
    aware_created_at = (
        created_at if created_at.tzinfo is not None else created_at.replace(tzinfo=UTC)
    )
    payload = f"{aware_created_at.astimezone(UTC).isoformat()}|{id_}"
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii").rstrip("=")


def decode_cursor(cursor: str) -> tuple[datetime, UUID]:
    try:
        padding = "=" * (-len(cursor) % 4)
        decoded = base64.urlsafe_b64decode(f"{cursor}{padding}".encode("ascii")).decode("utf-8")
        created_at_raw, id_raw = decoded.split("|", maxsplit=1)
        created_at = datetime.fromisoformat(created_at_raw)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)
        return created_at.astimezone(UTC), UUID(id_raw)
    except Exception as exc:
        raise AppError(
            "INVALID_CURSOR",
            "페이지 커서가 올바르지 않습니다.",
            HTTPStatus.BAD_REQUEST,
        ) from exc


async def paginate_query(
    session: AsyncSession,
    query: Select[tuple[T]],
    model: type[Any],
    params: CursorParams,
    order_by_created_desc: bool = True,
) -> tuple[list[T], str | None]:
    model_any = cast(Any, model)
    created_at_col = model_any.created_at
    id_col = model_any.id
    statement = query

    if params.cursor:
        cursor_created_at, cursor_id = decode_cursor(params.cursor)
        cursor_tuple = tuple_(literal(cursor_created_at), literal(cursor_id))
        model_tuple = tuple_(created_at_col, id_col)
        statement = statement.where(
            model_tuple < cursor_tuple if order_by_created_desc else model_tuple > cursor_tuple
        )

    order_by: tuple[Any, Any] = (
        (desc(created_at_col), desc(id_col))
        if order_by_created_desc
        else (
            asc(created_at_col),
            asc(id_col),
        )
    )
    statement = statement.order_by(*order_by).limit(params.limit + 1)

    result = await session.scalars(statement)
    fetched = list(result.all())
    items = fetched[: params.limit]
    next_cursor = None
    if len(fetched) > params.limit and items:
        last = cast(Any, items[-1])
        next_cursor = encode_cursor(
            cast(datetime, last.created_at),
            cast(UUID, last.id),
        )
    return items, next_cursor
