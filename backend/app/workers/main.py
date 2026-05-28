from collections.abc import Callable
from typing import Any, ClassVar
from urllib.parse import urlparse

import structlog
from arq.connections import RedisSettings

from app.core.config import get_settings
from app.core.database import close_engine, init_engine
from app.core.logging import setup_logging
from app.workers.registry import REGISTERED_JOBS

logger = structlog.get_logger()


def build_redis_settings() -> RedisSettings:
    settings = get_settings()
    parsed = urlparse(str(settings.REDIS_URL))
    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        database=int(parsed.path.removeprefix("/") or "0"),
        password=parsed.password,
    )


async def on_startup(_: dict[str, Any]) -> None:
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL, json_output=settings.is_prod)
    init_engine()
    logger.info("worker.start")


async def on_shutdown(_: dict[str, Any]) -> None:
    await close_engine()
    logger.info("worker.stop")


class WorkerSettings:
    redis_settings = build_redis_settings()
    functions: ClassVar[list[Callable[..., Any]]] = REGISTERED_JOBS
    on_startup = on_startup
    on_shutdown = on_shutdown
    max_jobs = 10
    max_tries = 3
    job_timeout = 120
