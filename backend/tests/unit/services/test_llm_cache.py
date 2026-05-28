import json

import pytest
from app.services.llm import cache


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.expirations: dict[str, int | None] = {}

    async def get(self, name: str) -> str | None:
        return self.values.get(name)

    async def set(self, name: str, value: str, ex: int | None = None) -> None:
        self.values[name] = value
        self.expirations[name] = ex


def test_image_hash_cache_key_changes_with_prompt() -> None:
    first = cache.image_hash_cache_key("https://cdn.test/a.jpg", "gpt-4o-mini", "prompt-a")
    second = cache.image_hash_cache_key("https://cdn.test/a.jpg", "gpt-4o-mini", "prompt-b")

    assert first.startswith("llm:vision:gpt-4o-mini:")
    assert first != second


@pytest.mark.asyncio
async def test_vision_cache_hit_and_miss() -> None:
    redis = FakeRedis()
    key = cache.image_hash_cache_key("https://cdn.test/a.jpg", "gpt-4o-mini", "prompt")

    assert await cache.get_cached_vision(redis, key) is None

    await cache.set_cached_vision(redis, key, {"description": "핑크 네일", "model": "gpt-4o-mini"})

    assert json.loads(redis.values[key])["description"] == "핑크 네일"
    assert redis.expirations[key] == 86400
    assert await cache.get_cached_vision(redis, key) == {
        "description": "핑크 네일",
        "model": "gpt-4o-mini",
    }
