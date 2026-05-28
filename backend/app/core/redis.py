from __future__ import annotations

from inspect import isawaitable

from arq import create_pool
from arq.connections import ArqRedis
from redis.asyncio import Redis, from_url

from app.core.config import get_settings
from app.workers.settings import redis_settings

_redis: Redis[str] | None = None
_arq_pool: ArqRedis | None = None


async def init_redis() -> Redis[str]:
    global _redis
    settings = get_settings()
    _redis = from_url(str(settings.REDIS_URL), encoding="utf-8", decode_responses=True)
    await _redis.ping()
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.close()
        _redis = None


def get_redis() -> Redis[str]:
    if _redis is None:
        raise RuntimeError("Redis not initialized — call init_redis() in lifespan")
    return _redis


async def init_arq_pool() -> ArqRedis:
    global _arq_pool
    _arq_pool = await create_pool(redis_settings())
    return _arq_pool


async def close_arq_pool() -> None:
    global _arq_pool
    if _arq_pool is not None:
        close_result = _arq_pool.close()
        if isawaitable(close_result):
            await close_result
        _arq_pool = None


def get_arq_pool() -> ArqRedis:
    if _arq_pool is None:
        raise RuntimeError("arq pool not initialized — call init_arq_pool() in lifespan")
    return _arq_pool
