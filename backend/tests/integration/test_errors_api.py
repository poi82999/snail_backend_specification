import pytest
from app.api.errors import install_error_handlers
from app.api.middleware import request_id_middleware
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_unhandled_exception_uses_standard_error_response() -> None:
    app = FastAPI()
    app.middleware("http")(request_id_middleware)
    install_error_handlers(app)

    @app.get("/boom")
    async def boom() -> None:
        raise RuntimeError("unexpected")

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/boom", headers={"X-Request-Id": "req-test"})

    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "INTERNAL", "message": "서버 오류", "field_errors": None},
        "request_id": "req-test",
    }
