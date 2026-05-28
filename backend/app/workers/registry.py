from collections.abc import Callable
from typing import Any, TypeVar

RegisteredJob = Callable[..., Any]
JobFunc = TypeVar("JobFunc", bound=RegisteredJob)

REGISTERED_JOBS: list[RegisteredJob] = []


def register_job(fn: JobFunc) -> JobFunc:
    REGISTERED_JOBS.append(fn)
    return fn


from app.workers import llm_pipeline as _llm_pipeline  # noqa: E402,F401
from app.workers import notifications as _notifications  # noqa: E402,F401
