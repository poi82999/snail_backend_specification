import json
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import jwt
import pytest
from app.core import security
from app.core.config import Settings
from app.models.enums import ActorType
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


@pytest.fixture
def test_settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://u:p@localhost:5432/d",
        REDIS_URL="redis://localhost:6379/0",
        JWT_SECRET="x" * 32,
        APPLE_CLIENT_ID="com.snail.test",
    )
    monkeypatch.setattr(security, "get_settings", lambda: settings)
    return settings


def test_hash_and_verify_password() -> None:
    hashed = security.hash_password("plain-password")
    assert hashed != "plain-password"
    assert security.verify_password("plain-password", hashed) is True
    assert security.verify_password("wrong-password", hashed) is False


def test_issue_and_decode_access_refresh_tokens(test_settings: Settings) -> None:
    sub = uuid4()

    access = security.issue_access_token(ActorType.USER, sub, {"scope": "test"})
    refresh = security.issue_refresh_token(ActorType.USER, sub)

    access_payload = security.decode_token(access)
    refresh_payload = security.decode_token(refresh)

    assert access_payload["sub"] == str(sub)
    assert access_payload["actor_type"] == "user"
    assert access_payload["type"] == "access"
    assert access_payload["scope"] == "test"
    assert access_payload["jti"] != refresh_payload["jti"]
    assert refresh_payload["type"] == "refresh"


@pytest.mark.asyncio
async def test_verify_apple_id_token_fetches_jwks_with_httpx(
    monkeypatch: pytest.MonkeyPatch,
    test_settings: Settings,
) -> None:
    security._apple_jwks_cache.clear()
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(private_key.public_key()))
    public_jwk.update({"kid": "apple-test-kid", "alg": "RS256", "use": "sig"})
    now = datetime.now(UTC)
    id_token = jwt.encode(
        {
            "sub": "apple-sub",
            "email": "apple@example.com",
            "email_verified": "true",
            "is_private_email": "false",
            "iss": "https://appleid.apple.com",
            "aud": test_settings.APPLE_CLIENT_ID,
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        private_pem,
        algorithm="RS256",
        headers={"kid": "apple-test-kid"},
    )

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return {"keys": [public_jwk]}

    class FakeAsyncClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            return None

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def get(self, url: str) -> FakeResponse:
            assert url == security.APPLE_JWKS_URL
            return FakeResponse()

    monkeypatch.setattr(security.httpx, "AsyncClient", FakeAsyncClient)

    identity = await security.verify_apple_id_token(id_token)

    assert identity.sub == "apple-sub"
    assert identity.email == "apple@example.com"
    assert identity.email_verified is True
    assert identity.is_private_email is False
