from __future__ import annotations

import asyncio
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import firebase_admin  # type: ignore[import-untyped]
import structlog
from firebase_admin import credentials, exceptions, messaging
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import AsyncRetrying, retry_if_exception, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.models.accounts import UserDeviceToken
from app.services.notifications.types import SendResult, TokenSendResult, mask_secret

logger = structlog.get_logger()

INVALID_TOKEN_CODES = {
    "UNREGISTERED",
    "INVALID_ARGUMENT",
    "registration-token-not-registered",
    "invalid-argument",
}
RETRYABLE_CODES = {"INTERNAL", "UNAVAILABLE", "UNKNOWN", "internal", "unavailable"}


def _configured() -> bool:
    settings = get_settings()
    return bool(settings.GOOGLE_APPLICATION_CREDENTIALS)


def _firebase_app() -> firebase_admin.App:
    settings = get_settings()
    try:
        return firebase_admin.get_app()
    except ValueError:
        credential_path = Path(settings.GOOGLE_APPLICATION_CREDENTIALS)
        cred = credentials.Certificate(str(credential_path))
        options: dict[str, str] = {}
        if settings.GCP_PROJECT_ID:
            options["projectId"] = settings.GCP_PROJECT_ID
        return firebase_admin.initialize_app(cred, options or None)


def _exception_code(exc: BaseException | None) -> str | None:
    if exc is None:
        return None
    code = getattr(exc, "code", None)
    if code is not None:
        return str(code)
    cause = getattr(exc, "cause", None)
    if cause is not None:
        status = getattr(cause, "status", None)
        if status is not None:
            return str(status)
    return exc.__class__.__name__


def _is_invalid_token(exc: BaseException | None) -> bool:
    code = _exception_code(exc)
    return code in INVALID_TOKEN_CODES


def _is_retryable_exception(exc: BaseException) -> bool:
    if isinstance(exc, TimeoutError):
        return True
    if isinstance(exc, exceptions.FirebaseError):
        status_code = getattr(exc, "http_response", None)
        if status_code is not None and getattr(status_code, "status_code", 0) >= 500:
            return True
        code = _exception_code(exc)
        return code in RETRYABLE_CODES
    return False


def _string_data(data: Mapping[str, object]) -> dict[str, str]:
    return {str(key): str(value) for key, value in data.items() if value is not None}


def _send_multicast(
    *,
    app: firebase_admin.App,
    device_tokens: list[str],
    title: str,
    body: str,
    data: Mapping[str, object],
) -> messaging.BatchResponse:
    message = messaging.MulticastMessage(
        tokens=device_tokens,
        notification=messaging.Notification(title=title, body=body),
        data=_string_data(data),
        apns=messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(sound="default"),
            )
        ),
    )
    send_each = getattr(messaging, "send_each_for_multicast", None)
    if send_each is not None:
        return cast(messaging.BatchResponse, send_each(message, app=app))
    return cast(messaging.BatchResponse, messaging.send_multicast(message, app=app))


async def _send_with_retry(
    *,
    app: firebase_admin.App,
    device_tokens: list[str],
    title: str,
    body: str,
    data: Mapping[str, object],
) -> messaging.BatchResponse:
    async for attempt in AsyncRetrying(
        retry=retry_if_exception(_is_retryable_exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.1, min=0.1, max=1),
        reraise=True,
    ):
        with attempt:
            return await asyncio.wait_for(
                asyncio.to_thread(
                    _send_multicast,
                    app=app,
                    device_tokens=device_tokens,
                    title=title,
                    body=body,
                    data=data,
                ),
                timeout=10,
            )
    raise RuntimeError("Firebase multicast request did not run")


async def _mark_invalid_tokens(
    session: AsyncSession | None,
    invalid_tokens: list[str],
) -> None:
    if session is None or not invalid_tokens:
        return
    await session.execute(
        update(UserDeviceToken)
        .where(UserDeviceToken.token.in_(invalid_tokens))
        .values(is_active=False)
    )
    await session.flush()


async def send_push(
    *,
    device_tokens: list[str],
    title: str,
    body: str,
    data: Mapping[str, object],
    session: AsyncSession | None = None,
) -> SendResult:
    if not _configured():
        return SendResult(status="skipped", reason="channel_not_configured")
    if not device_tokens:
        return SendResult(status="skipped", reason="no_active_device_token")

    try:
        app = _firebase_app()
        response = await _send_with_retry(
            app=app,
            device_tokens=device_tokens,
            title=title,
            body=body,
            data=data,
        )
    except (TimeoutError, exceptions.FirebaseError) as exc:
        logger.warning("notification.apns.request_failed", error=exc.__class__.__name__)
        return SendResult(
            status="failed",
            reason=_exception_code(exc) or "request_failed",
            retryable=_is_retryable_exception(exc),
        )

    results: list[TokenSendResult] = []
    invalid_tokens: list[str] = []
    retryable_errors: list[str] = []
    first_success_id: str | None = None

    for token, token_response in zip(device_tokens, response.responses, strict=False):
        message_id = getattr(token_response, "message_id", None)
        if token_response.success:
            if first_success_id is None and message_id is not None:
                first_success_id = str(message_id)
            results.append(TokenSendResult(token=token, success=True))
            continue

        token_exc = cast(BaseException | None, token_response.exception)
        error_code = _exception_code(token_exc) or "unknown"
        results.append(TokenSendResult(token=token, success=False, error=error_code))
        if _is_invalid_token(token_exc):
            invalid_tokens.append(token)
            logger.info("notification.apns.invalid_token", device_token=mask_secret(token))
        elif error_code in RETRYABLE_CODES:
            retryable_errors.append(error_code)

    await _mark_invalid_tokens(session, invalid_tokens)

    if response.success_count > 0:
        return SendResult(
            status="sent",
            provider_message_id=first_success_id,
            invalid_tokens=invalid_tokens,
            results=results,
        )
    if invalid_tokens and not retryable_errors:
        return SendResult(
            status="failed",
            reason="invalid_device_token",
            retryable=False,
            invalid_tokens=invalid_tokens,
            results=results,
        )
    return SendResult(
        status="failed",
        reason=retryable_errors[0] if retryable_errors else "apns_failed",
        retryable=bool(retryable_errors),
        invalid_tokens=invalid_tokens,
        results=results,
    )


async def send_apns(
    *,
    device_tokens: list[str],
    payload: dict[str, Any],
    session: AsyncSession | None = None,
) -> SendResult:
    alert = cast(dict[str, object], cast(dict[str, object], payload.get("aps") or {}).get("alert"))
    data = {key: value for key, value in payload.items() if key != "aps"}
    return await send_push(
        device_tokens=device_tokens,
        title=str(alert.get("title") or "예약 알림"),
        body=str(alert.get("body") or ""),
        data=data,
        session=session,
    )
