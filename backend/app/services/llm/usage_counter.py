from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Protocol


class UsageRedis(Protocol):
    async def hincrby(self, name: str, key: str, amount: int = 1) -> Any: ...

    async def hincrbyfloat(self, name: str, key: str, amount: float = 1.0) -> Any: ...

    async def expire(self, name: str, time: int) -> Any: ...


USAGE_KEY_TTL_SECONDS = 60 * 60 * 24 * 370


def monthly_key(prefix: str, year_month: str) -> str:
    return f"llm:usage:{prefix}:{year_month}"


def _current_year_month() -> str:
    return datetime.now(UTC).strftime("%Y-%m")


async def incr_usage(
    redis: UsageRedis,
    model: str,
    tokens: int,
    cost_estimate: Decimal | float | int,
) -> None:
    key = monthly_key(model, _current_year_month())
    await redis.hincrby(key, "calls", 1)
    await redis.hincrby(key, "tokens", max(0, tokens))
    await redis.hincrbyfloat(key, "cost_estimate", float(cost_estimate))
    await redis.expire(key, USAGE_KEY_TTL_SECONDS)
