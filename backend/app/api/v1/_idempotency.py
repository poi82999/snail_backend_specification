from http import HTTPStatus
from typing import Annotated, cast
from uuid import UUID

from fastapi import Depends, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api.errors import AppError
from app.utils.idempotency import IdempotencyContext, hash_request, idempotency_key_header

SYSTEM_ACTOR_ID = UUID("00000000-0000-0000-0000-000000000000")


def require_idempotency_key(key: str | None) -> str:
    if key is None or not key.strip():
        raise AppError(
            "IDEMPOTENCY_KEY_REQUIRED",
            "Idempotency-Key 헤더가 필요합니다.",
            HTTPStatus.BAD_REQUEST,
        )
    return key


def required_idempotency_key(
    key: Annotated[str | None, Depends(idempotency_key_header)],
) -> str:
    return require_idempotency_key(key)


async def request_hash_for(request: Request) -> str:
    return hash_request(request.method, request.url.path, await request.body())


def cached_response(context: IdempotencyContext) -> Response:
    status_code = context.response_status or HTTPStatus.OK
    if status_code == HTTPStatus.NO_CONTENT:
        return Response(status_code=HTTPStatus.NO_CONTENT)
    return JSONResponse(status_code=status_code, content=context.response_body or {})


def response_body(model: BaseModel) -> dict[str, object]:
    return cast(dict[str, object], model.model_dump(mode="json"))
