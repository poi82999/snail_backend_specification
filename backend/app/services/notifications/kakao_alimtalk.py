from __future__ import annotations

from base64 import b64encode
from collections.abc import Mapping
from typing import Any, cast
from uuid import uuid4

import httpx
import structlog
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.services.notifications.types import SendResult

logger = structlog.get_logger()

BIZPPURIO_MESSAGE_URL = "https://api.bizppurio.com/v3/message"
INFORMATIONAL_TEMPLATE_BANNED_WORDS = ("광고", "(광고)")


class _RetryableBizppurioError(Exception):
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(f"Bizppurio retryable status {status_code}")


def _basic_auth(user_id: str, api_key: str) -> str:
    raw = f"{user_id}:{api_key}".encode()
    return f"Basic {b64encode(raw).decode('ascii')}"


def _content_from_variables(variables: Mapping[str, object]) -> str:
    content = variables.get("content")
    if isinstance(content, str) and content:
        return content
    body = variables.get("body")
    if isinstance(body, str) and body:
        return body
    return " ".join(str(value) for value in variables.values() if value is not None)


def _has_advertising_words(variables: Mapping[str, object]) -> bool:
    text = " ".join(str(value) for value in variables.values() if value is not None)
    return any(word in text for word in INFORMATIONAL_TEMPLATE_BANNED_WORDS)


async def _post_with_retry(
    client: httpx.AsyncClient,
    url: str,
    *,
    request_body: dict[str, object],
    headers: dict[str, str],
) -> httpx.Response:
    last_response: httpx.Response | None = None
    try:
        async for attempt in AsyncRetrying(
            retry=retry_if_exception_type(
                (httpx.TimeoutException, httpx.TransportError, _RetryableBizppurioError)
            ),
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=0.1, min=0.1, max=1),
            reraise=True,
        ):
            with attempt:
                response = await client.post(url, json=request_body, headers=headers)
                last_response = response
                if response.status_code >= 500:
                    raise _RetryableBizppurioError(response.status_code)
                return response
    except _RetryableBizppurioError:
        if last_response is not None:
            return last_response
        raise
    raise RuntimeError("Bizppurio request did not run")


async def send_alimtalk(
    *,
    sender_key: str | None = None,
    template_code: str | None = None,
    phone_number: str | None,
    variables: Mapping[str, object] | None = None,
    payload: Mapping[str, object] | None = None,
) -> SendResult:
    settings = get_settings()
    resolved_sender_key = sender_key or settings.KAKAO_SENDER_KEY
    resolved_template_code = template_code or str(
        (payload or {}).get("templateCode") or (payload or {}).get("template_code") or ""
    )
    resolved_variables: Mapping[str, object] = (
        variables
        if variables is not None
        else cast(Mapping[str, object], (payload or {}).get("variables") or payload or {})
    )

    if not resolved_sender_key or not settings.BIZPPURIO_USER_ID or not settings.BIZPPURIO_API_KEY:
        return SendResult(status="skipped", reason="channel_not_configured")
    if not phone_number:
        return SendResult(status="skipped", reason="recipient_phone_missing")
    if not resolved_template_code:
        return SendResult(status="failed", reason="template_code_missing", retryable=False)
    if _has_advertising_words(resolved_variables):
        return SendResult(status="failed", reason="advertising_terms_not_allowed", retryable=False)

    content = str((payload or {}).get("content") or _content_from_variables(resolved_variables))
    request_body: dict[str, object] = {
        "account": settings.BIZPPURIO_USER_ID,
        "refkey": uuid4().hex,
        "type": "at",
        "from": resolved_sender_key,
        "to": phone_number,
        "content": content,
        "templateCode": resolved_template_code,
        "variables": dict(resolved_variables),
    }
    headers = {
        "Authorization": _basic_auth(settings.BIZPPURIO_USER_ID, settings.BIZPPURIO_API_KEY),
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await _post_with_retry(
                client,
                BIZPPURIO_MESSAGE_URL,
                request_body=request_body,
                headers=headers,
            )
    except (httpx.TimeoutException, httpx.TransportError) as exc:
        logger.warning("notification.kakao.request_failed", error=exc.__class__.__name__)
        return SendResult(status="failed", reason="request_failed", retryable=True)

    if response.status_code >= 500:
        logger.warning("notification.kakao.server_error", status_code=response.status_code)
        return SendResult(
            status="failed",
            reason=f"http_{response.status_code}",
            retryable=True,
        )
    if response.status_code >= 400:
        logger.warning("notification.kakao.client_error", status_code=response.status_code)
        return SendResult(
            status="failed",
            reason=f"http_{response.status_code}",
            retryable=False,
        )

    try:
        response_body: Any = response.json()
    except ValueError:
        logger.warning(
            "notification.kakao.invalid_response",
            status_code=response.status_code,
        )
        return SendResult(status="failed", reason="invalid_response", retryable=True)

    if not isinstance(response_body, dict):
        return SendResult(status="failed", reason="invalid_response", retryable=True)

    code = str(response_body.get("code", ""))
    provider_message_id = response_body.get("messageKey") or response_body.get("msgid")
    if code in {"1000", "0", "OK"}:
        return SendResult(
            status="sent",
            provider_message_id=cast(str | None, provider_message_id),
        )

    reason = str(response_body.get("description") or response_body.get("message") or code)
    logger.warning("notification.kakao.failed", provider_code=code, reason=reason[:200])
    return SendResult(
        status="failed",
        provider_message_id=cast(str | None, provider_message_id),
        reason=reason,
        retryable=False,
    )
