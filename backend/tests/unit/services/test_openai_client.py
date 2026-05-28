import asyncio
from types import SimpleNamespace

import httpx
import openai
import pytest
from app.api.errors import AppError
from app.core.config import get_settings
from app.services.llm import openai_client


@pytest.mark.asyncio
async def test_vision_describe_maps_response(mock_openai: type[object]) -> None:
    result = await openai_client.vision_describe(
        "https://cdn.test/design.jpg",
        prompt="describe",
    )

    assert result["description"] == "깨끗한 핑크 프렌치 네일 디자인"
    assert result["model"] == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_classify_from_description_parses_json(mock_openai: type[object]) -> None:
    result = await openai_client.classify_from_description("깨끗한 핑크 프렌치 네일")

    assert result["ai_tags"] == ["clean", "pink"]
    assert result["color_palette"] == ["pink"]
    assert result["style_category"] == "simple"
    assert result["nail_shape"] == "round"
    assert result["confidence"] == 0.87


@pytest.mark.asyncio
async def test_embed_text_uses_1536_dimensions(mock_openai: type[object]) -> None:
    embedding = await openai_client.embed_text("깨끗한 핑크 네일 clean pink")

    assert len(embedding) == 1536
    assert embedding[:3] == [0.1, 0.1, 0.1]


@pytest.mark.asyncio
async def test_vision_describe_uses_semaphore(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    get_settings.cache_clear()
    state = {"active": 0, "max_active": 0}

    class FakeChatCompletions:
        async def create(self, *args: object, **kwargs: object) -> SimpleNamespace:
            state["active"] += 1
            state["max_active"] = max(state["max_active"], state["active"])
            await asyncio.sleep(0.01)
            state["active"] -= 1
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content="동시성 제한 테스트 네일"),
                    )
                ],
                model=kwargs.get("model", "gpt-4o-mini"),
            )

    class FakeChat:
        completions = FakeChatCompletions()

    class FakeAsyncOpenAI:
        def __init__(self, *args: object, **kwargs: object) -> None:
            self.chat = FakeChat()

    monkeypatch.setattr(openai, "AsyncOpenAI", FakeAsyncOpenAI)
    monkeypatch.setattr(openai_client, "_semaphore", asyncio.Semaphore(1))

    await asyncio.gather(
        openai_client.vision_describe("https://cdn.test/1.jpg", prompt="describe"),
        openai_client.vision_describe("https://cdn.test/2.jpg", prompt="describe"),
    )

    assert state["max_active"] == 1
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_vision_describe_retries_retryable_openai_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    get_settings.cache_clear()
    state = {"calls": 0}

    class FakeChatCompletions:
        async def create(self, *args: object, **kwargs: object) -> SimpleNamespace:
            state["calls"] += 1
            if state["calls"] == 1:
                raise openai.APIError(
                    "temporary",
                    request=httpx.Request("POST", "https://api.openai.test/v1/chat"),
                    body=None,
                )
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="재시도 성공"))],
                model=kwargs.get("model", "gpt-4o-mini"),
            )

    class FakeChat:
        completions = FakeChatCompletions()

    class FakeAsyncOpenAI:
        def __init__(self, *args: object, **kwargs: object) -> None:
            self.chat = FakeChat()

    monkeypatch.setattr(openai, "AsyncOpenAI", FakeAsyncOpenAI)

    result = await openai_client.vision_describe("https://cdn.test/retry.jpg", prompt="describe")

    assert result["description"] == "재시도 성공"
    assert state["calls"] == 2
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_bad_request_is_not_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    get_settings.cache_clear()
    state = {"calls": 0}
    request = httpx.Request("POST", "https://api.openai.test/v1/chat")

    class FakeChatCompletions:
        async def create(self, *args: object, **kwargs: object) -> SimpleNamespace:
            state["calls"] += 1
            raise openai.BadRequestError(
                "bad request",
                response=httpx.Response(400, request=request),
                body=None,
            )

    class FakeChat:
        completions = FakeChatCompletions()

    class FakeAsyncOpenAI:
        def __init__(self, *args: object, **kwargs: object) -> None:
            self.chat = FakeChat()

    monkeypatch.setattr(openai, "AsyncOpenAI", FakeAsyncOpenAI)

    with pytest.raises(AppError) as exc_info:
        await openai_client.vision_describe("https://cdn.test/bad.jpg", prompt="describe")

    assert exc_info.value.code == "OPENAI_REQUEST_REJECTED"
    assert state["calls"] == 1
    get_settings.cache_clear()
