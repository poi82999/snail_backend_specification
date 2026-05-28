from __future__ import annotations

import hashlib
import json
from typing import Any, Protocol, cast


class VisionCacheRedis(Protocol):
    async def get(self, name: str) -> Any: ...

    async def set(self, name: str, value: str, ex: int | None = None) -> Any: ...


def image_hash_cache_key(image_url: str, model: str, prompt: str) -> str:
    image_hash = hashlib.sha256(image_url.encode("utf-8")).hexdigest()
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    return f"llm:vision:{model}:{image_hash}:{prompt_hash}"


async def get_cached_vision(redis: VisionCacheRedis, key: str) -> dict[str, object] | None:
    raw = await redis.get(key)
    if raw is None:
        return None
    if isinstance(raw, bytes):
        raw_text = raw.decode("utf-8")
    elif isinstance(raw, str):
        raw_text = raw
    else:
        return None

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    return cast(dict[str, object], parsed)


async def set_cached_vision(
    redis: VisionCacheRedis,
    key: str,
    payload: dict[str, object],
    ttl: int = 86400,
) -> None:
    await redis.set(key, json.dumps(payload, ensure_ascii=False), ex=ttl)
