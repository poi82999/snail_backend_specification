from typing import ClassVar
from urllib.parse import urlparse

from arq.connections import RedisSettings

from app.core.config import get_settings


def redis_settings() -> RedisSettings:
    settings = get_settings()
    parsed = urlparse(str(settings.REDIS_URL))
    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        database=int(parsed.path.removeprefix("/") or "0"),
        password=parsed.password,
    )


class WorkerSettings:
    redis_settings = redis_settings()
    functions: ClassVar[list[object]] = []
    max_jobs = 10
    job_timeout = 120
