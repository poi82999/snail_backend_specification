from http import HTTPStatus

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas.common import ErrorBody, ErrorResponse

logger = structlog.get_logger()


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = HTTPStatus.BAD_REQUEST,
        field_errors: dict[str, str] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.field_errors = field_errors


def request_id_from(request: Request) -> str:
    return getattr(request.state, "request_id", "")


def error_payload(
    request: Request,
    body_or_code: ErrorBody | str,
    message: str | None = None,
    field_errors: dict[str, str] | None = None,
) -> dict[str, object]:
    body = (
        body_or_code
        if isinstance(body_or_code, ErrorBody)
        else ErrorBody(code=body_or_code, message=message or "", field_errors=field_errors)
    )
    return ErrorResponse(error=body, request_id=request_id_from(request)).model_dump()


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(
            request,
            ErrorBody(code=exc.code, message=exc.message, field_errors=exc.field_errors),
        ),
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    field_errors: dict[str, str] = {}
    for err in exc.errors():
        loc = ".".join(str(part) for part in err["loc"] if part not in {"body", "query", "path"})
        field_errors[loc or "request"] = str(err["msg"])

    return JSONResponse(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        content=error_payload(
            request,
            ErrorBody(
                code="VALIDATION_ERROR",
                message="입력값을 확인해주세요.",
                field_errors=field_errors,
            ),
        ),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "request.unhandled_exception",
        request_id=request_id_from(request),
        method=request.method,
        path=request.url.path,
        exc_info=exc,
    )
    return JSONResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        content=error_payload(request, "INTERNAL", "서버 오류"),
    )


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)
