from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal

SendStatus = Literal["sent", "skipped", "failed"]


class NotificationDeliveryStatus(StrEnum):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass(frozen=True, slots=True)
class TokenSendResult:
    token: str
    success: bool
    error: str | None = None


@dataclass(frozen=True, slots=True)
class SendResult:
    status: SendStatus
    provider_message_id: str | None = None
    reason: str | None = None
    retryable: bool = False
    invalid_tokens: list[str] = field(default_factory=list)
    results: list[TokenSendResult] = field(default_factory=list)


def mask_secret(value: str | None) -> str:
    if not value:
        return ""
    if len(value) <= 7:
        return "***"
    return f"{value[:4]}...{value[-3:]}"
