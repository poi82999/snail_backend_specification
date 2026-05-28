from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import sentry_sdk
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.fastapi import FastApiIntegration

from app.api.errors import install_error_handlers
from app.api.middleware import request_id_middleware
from app.api.v1 import api_v1_router
from app.core.config import get_settings
from app.core.database import close_engine, init_engine
from app.core.logging import setup_logging
from app.core.redis import close_arq_pool, close_redis, init_arq_pool, init_redis

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL, json_output=settings.is_prod)

    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            environment=settings.ENV,
            integrations=[FastApiIntegration()],
        )

    init_engine()
    await init_redis()
    await init_arq_pool()
    logger.info("app.start", env=settings.ENV, version=settings.APP_VERSION)
    try:
        yield
    finally:
        await close_arq_pool()
        await close_redis()
        await close_engine()
        logger.info("app.stop")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url=None if settings.is_prod else "/docs",
        redoc_url=None if settings.is_prod else "/redoc",
        openapi_url=None if settings.is_prod else "/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.middleware("http")(request_id_middleware)
    install_error_handlers(app)

    app.include_router(api_v1_router, prefix="/api/v1")
    return app


app = create_app()
