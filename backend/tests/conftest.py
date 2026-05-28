from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from app.api import deps
from app.core.config import Settings, get_settings
from app.core.security import AppleIdentity, GoogleIdentity, hash_password, issue_access_token
from app.main import create_app
from app.models.accounts import Owner, User
from app.models.base import Base
from app.models.enums import ActorType, UploadTargetType
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis, from_url
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest.fixture(scope="session")
def event_loop() -> Iterator[asyncio.AbstractEventLoop]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def api_client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    app = create_app()

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[deps.db_session] = override_db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def settings_override(monkeypatch: pytest.MonkeyPatch) -> Iterator[Settings]:
    monkeypatch.setenv("ENV", "local")
    monkeypatch.setenv("JWT_SECRET", "x" * 32)
    get_settings.cache_clear()
    yield get_settings()
    get_settings.cache_clear()


@pytest.fixture
async def db_session(settings_override: Settings) -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(str(settings_override.DATABASE_URL), pool_pre_ping=True)
    connection = await engine.connect()
    transaction = await connection.begin()
    # 데모용 seed(commit된 데이터)와 테스트를 격리한다. 외부 트랜잭션 안에서 전 테이블을
    # 비워 테스트는 깨끗한 DB에서 시작하고, 끝에서 transaction.rollback()으로 TRUNCATE까지
    # 되돌려 seed 데이터를 원상 복구한다.
    table_names = ", ".join(f'"{name}"' for name in Base.metadata.tables)
    await connection.execute(text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE"))
    session_factory = async_sessionmaker(connection, expire_on_commit=False, autoflush=False)
    session = session_factory()
    await session.begin_nested()

    try:
        yield session
    finally:
        await session.rollback()
        await session.close()
        await transaction.rollback()
        await connection.close()
        await engine.dispose()


@pytest.fixture
async def redis_client(settings_override: Settings) -> AsyncIterator[Redis[str]]:
    client: Redis[str] = from_url(
        str(settings_override.REDIS_URL),
        encoding="utf-8",
        decode_responses=True,
    )
    await client.flushdb()
    try:
        yield client
    finally:
        await client.flushdb()
        await client.close()


@pytest.fixture
async def user_token(db_session: AsyncSession) -> str:
    user = User(
        id=uuid4(),
        apple_sub=f"apple-{uuid4().hex}",
        email=f"{uuid4().hex}@example.com",
        nickname=f"user_{uuid4().hex[:10]}",
    )
    db_session.add(user)
    await db_session.flush()
    return issue_access_token(ActorType.USER, user.id)


@pytest.fixture
async def owner_token(db_session: AsyncSession) -> str:
    owner = Owner(
        id=uuid4(),
        email=f"{uuid4().hex}@example.com",
        password_hash=hash_password("owner-password"),
        representative_name="테스트 사장님",
        phone_number="010-0000-0000",
    )
    db_session.add(owner)
    await db_session.flush()
    return issue_access_token(ActorType.OWNER, owner.id)


@pytest.fixture
def mock_apple_signin(monkeypatch: pytest.MonkeyPatch) -> AppleIdentity:
    from app.core import security

    identity = AppleIdentity(
        sub="apple-test-sub",
        email="apple@example.com",
        email_verified=True,
        is_private_email=False,
    )

    async def fake_verify_apple_id_token(_: str) -> AppleIdentity:
        return identity

    monkeypatch.setattr(security, "verify_apple_id_token", fake_verify_apple_id_token)
    return identity


@pytest.fixture
def mock_google_signin(monkeypatch: pytest.MonkeyPatch) -> GoogleIdentity:
    from app.core import security

    identity = GoogleIdentity(
        sub="google-test-sub",
        email="google@example.com",
        email_verified=True,
        name="테스트유저",
        picture="https://example.com/photo.jpg",
    )

    async def fake_verify_google_id_token(_: str) -> GoogleIdentity:
        return identity

    monkeypatch.setattr(security, "verify_google_id_token", fake_verify_google_id_token)
    return identity


@pytest.fixture
def mock_openai(monkeypatch: pytest.MonkeyPatch) -> Iterator[type[object]]:
    import openai
    from app.core.config import get_settings

    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    get_settings.cache_clear()

    class FakeEmbeddings:
        async def create(self, *args: object, **kwargs: object) -> SimpleNamespace:
            dimensions = int(kwargs.get("dimensions", 1536))
            return SimpleNamespace(
                data=[SimpleNamespace(embedding=[0.1] * dimensions)],
                model=kwargs.get("model", "text-embedding-3-small"),
            )

    class FakeChatCompletions:
        @staticmethod
        def _has_image(messages: object) -> bool:
            if not isinstance(messages, list):
                return False
            for message in messages:
                if not isinstance(message, dict):
                    continue
                content = message.get("content")
                if not isinstance(content, list):
                    continue
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "image_url":
                        return True
            return False

        async def create(self, *args: object, **kwargs: object) -> SimpleNamespace:
            model = kwargs.get("model", "gpt-4o-mini")
            if kwargs.get("response_format") == {"type": "json_object"}:
                content = (
                    '{"ai_tags":["clean","pink"],'
                    '"color_palette":["pink"],'
                    '"style_category":"simple",'
                    '"nail_shape":"round",'
                    '"confidence":0.87}'
                )
            elif self._has_image(kwargs.get("messages")):
                content = "깨끗한 핑크 프렌치 네일 디자인"
            else:
                content = '{"ai_tags":["clean"],"colors":["pink"]}'
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
                model=model,
            )

    class FakeChat:
        completions = FakeChatCompletions()

    class FakeAsyncOpenAI:
        def __init__(self, *args: object, **kwargs: object) -> None:
            self.chat = FakeChat()
            self.embeddings = FakeEmbeddings()

    monkeypatch.setattr(openai, "AsyncOpenAI", FakeAsyncOpenAI)
    yield FakeAsyncOpenAI
    get_settings.cache_clear()


@pytest.fixture
def mock_gcs(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core import gcs

    async def fake_issue_signed_upload_url(
        target_type: UploadTargetType,
        content_type: str,
        max_bytes: int = 10 * 1024 * 1024,
    ) -> gcs.SignedUploadResponse:
        object_key = f"{target_type.value}/00/test.jpg"
        return gcs.SignedUploadResponse(
            upload_url="https://example.test/upload",
            object_key=object_key,
            gcs_uri=f"gs://test-bucket/{object_key}",
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
            headers={
                "Content-Type": content_type,
                "x-goog-content-length-range": f"0,{max_bytes}",
            },
        )

    monkeypatch.setattr(gcs, "issue_signed_upload_url", fake_issue_signed_upload_url)
    monkeypatch.setattr(gcs, "get_public_url", lambda object_key: f"https://cdn.test/{object_key}")


@pytest.fixture
def mock_kakao(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    response = {"ok": True, "provider_message_id": "kakao-test-message"}
    try:
        import app.services.kakao_client as kakao_client
    except ModuleNotFoundError:
        return response

    monkeypatch.setattr(kakao_client, "send", AsyncMock(return_value=response), raising=False)
    return response


@pytest.fixture
def mock_apns(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    response = {"ok": True, "provider_message_id": "apns-test-message"}
    try:
        import app.services.apns_client as apns_client
    except ModuleNotFoundError:
        return response

    monkeypatch.setattr(apns_client, "send", AsyncMock(return_value=response), raising=False)
    return response


@pytest.fixture
def mock_httpx_kakao(monkeypatch: pytest.MonkeyPatch) -> Iterator[dict[str, object]]:
    from app.core.config import get_settings
    from app.services.notifications import kakao_alimtalk

    monkeypatch.setenv("KAKAO_SENDER_KEY", "sender-key")
    monkeypatch.setenv("BIZPPURIO_USER_ID", "biz-user")
    monkeypatch.setenv("BIZPPURIO_API_KEY", "biz-api-key")
    get_settings.cache_clear()

    state: dict[str, object] = {
        "calls": [],
        "response": {"code": "1000", "messageKey": "kakao-message-1"},
        "status_codes": [],
    }

    class FakeResponse:
        def __init__(self, status_code: int) -> None:
            self.status_code = status_code
            self.text = '{"code":"1000"}'

        def json(self) -> dict[str, object]:
            return dict(state["response"])  # type: ignore[arg-type]

    class FakeAsyncClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            state["client_kwargs"] = kwargs

        async def __aenter__(self) -> FakeAsyncClient:
            return self

        async def __aexit__(self, *args: object) -> bool:
            return False

        async def post(self, url: str, **kwargs: object) -> FakeResponse:
            calls = state["calls"]
            assert isinstance(calls, list)
            calls.append({"url": url, **kwargs})
            status_codes = state["status_codes"]
            if isinstance(status_codes, list) and status_codes:
                status_code = int(status_codes.pop(0))
            else:
                status_code = 200
            return FakeResponse(status_code)

    monkeypatch.setattr(kakao_alimtalk.httpx, "AsyncClient", FakeAsyncClient)
    yield state
    get_settings.cache_clear()


@pytest.fixture
def mock_httpx_apns(monkeypatch: pytest.MonkeyPatch) -> Iterator[dict[str, object]]:
    from app.core.config import get_settings
    from app.services.notifications import apns

    monkeypatch.setenv("APNS_TEAM_ID", "TEAMID1234")
    monkeypatch.setenv("APNS_KEY_ID", "KEYID1234")
    monkeypatch.setenv("APNS_PRIVATE_KEY_PATH", "./secrets/apns-test.p8")
    monkeypatch.setenv("APNS_BUNDLE_ID", "app.snail.test")
    monkeypatch.setenv("APNS_USE_SANDBOX", "true")
    get_settings.cache_clear()

    state: dict[str, object] = {"calls": []}

    class FakeResponse:
        def __init__(self, status_code: int, body: dict[str, object], apns_id: str) -> None:
            self.status_code = status_code
            self._body = body
            self.headers = {"apns-id": apns_id}
            self.text = str(body)

        def json(self) -> dict[str, object]:
            return dict(self._body)

    class FakeAsyncClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            state["client_kwargs"] = kwargs

        async def __aenter__(self) -> FakeAsyncClient:
            return self

        async def __aexit__(self, *args: object) -> bool:
            return False

        async def post(self, url: str, **kwargs: object) -> FakeResponse:
            calls = state["calls"]
            assert isinstance(calls, list)
            calls.append({"url": url, **kwargs})
            if "bad-token" in url:
                return FakeResponse(400, {"reason": "BadDeviceToken"}, "bad-apns-id")
            return FakeResponse(200, {}, "apns-message-1")

    monkeypatch.setattr(apns, "_provider_token", AsyncMock(return_value="provider-token"))
    monkeypatch.setattr(apns.httpx, "AsyncClient", FakeAsyncClient)
    yield state
    get_settings.cache_clear()
