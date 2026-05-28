from decimal import Decimal

import pytest
from app.services.llm import usage_counter


class FakeUsageRedis:
    def __init__(self) -> None:
        self.hashes: dict[str, dict[str, float]] = {}
        self.expirations: dict[str, int] = {}

    async def hincrby(self, name: str, key: str, amount: int = 1) -> int:
        fields = self.hashes.setdefault(name, {})
        fields[key] = fields.get(key, 0) + amount
        return int(fields[key])

    async def hincrbyfloat(self, name: str, key: str, amount: float = 1.0) -> float:
        fields = self.hashes.setdefault(name, {})
        fields[key] = fields.get(key, 0) + amount
        return fields[key]

    async def expire(self, name: str, time: int) -> bool:
        self.expirations[name] = time
        return True


def test_monthly_key() -> None:
    assert usage_counter.monthly_key("vision", "2026-05") == "llm:usage:vision:2026-05"


@pytest.mark.asyncio
async def test_incr_usage_accumulates_monthly_fields() -> None:
    redis = FakeUsageRedis()

    await usage_counter.incr_usage(redis, "gpt-4o-mini", 11, Decimal("0.25"))
    await usage_counter.incr_usage(redis, "gpt-4o-mini", 7, Decimal("0.10"))

    key = next(iter(redis.hashes))
    assert key.startswith("llm:usage:gpt-4o-mini:")
    assert redis.hashes[key]["calls"] == 2
    assert redis.hashes[key]["tokens"] == 18
    assert redis.hashes[key]["cost_estimate"] == pytest.approx(0.35)
    assert redis.expirations[key] == usage_counter.USAGE_KEY_TTL_SECONDS
