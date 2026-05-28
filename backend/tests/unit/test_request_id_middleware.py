import logging

import pytest
import structlog
from app.api.middleware import request_id_middleware
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from structlog.testing import ReturnLoggerFactory
from structlog.types import EventDict


@pytest.mark.asyncio
async def test_request_id_is_bound_to_structlog_contextvars() -> None:
    events: list[EventDict] = []

    def capture(_: object, __: str, event_dict: EventDict) -> EventDict:
        events.append(dict(event_dict))
        return event_dict

    structlog.configure(
        processors=[structlog.contextvars.merge_contextvars, capture],
        logger_factory=ReturnLoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=False,
    )
    try:
        app = FastAPI()
        app.middleware("http")(request_id_middleware)

        @app.get("/log")
        async def log_route() -> dict[str, bool]:
            structlog.get_logger().info("route.logged")
            return {"ok": True}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/log", headers={"X-Request-Id": "req-unit"})

        assert response.status_code == 200
        assert any(event.get("request_id") == "req-unit" for event in events)
    finally:
        structlog.contextvars.clear_contextvars()
        structlog.reset_defaults()
