import pytest
from app.core.config import get_settings
from app.services.notifications import kakao_alimtalk


@pytest.mark.asyncio
async def test_kakao_send_succeeds(mock_httpx_kakao: dict[str, object]) -> None:
    result = await kakao_alimtalk.send_alimtalk(
        sender_key="sender-key",
        template_code="SNAIL_RESV_REQUESTED_V1",
        phone_number="010-0000-0000",
        variables={"#{shop_name}": "스네일 네일", "content": "새 예약"},
    )

    assert result.status == "sent"
    assert result.provider_message_id == "kakao-message-1"
    assert len(mock_httpx_kakao["calls"]) == 1


@pytest.mark.asyncio
async def test_kakao_send_failed_code_is_retryable(
    mock_httpx_kakao: dict[str, object],
) -> None:
    mock_httpx_kakao["response"] = {"code": "3000", "message": "temporary failure"}

    result = await kakao_alimtalk.send_alimtalk(
        sender_key="sender-key",
        template_code="SNAIL_RESV_REQUESTED_V1",
        phone_number="010-0000-0000",
        variables={"#{shop_name}": "스네일 네일", "content": "새 예약"},
    )

    assert result.status == "failed"
    assert result.retryable is False
    assert result.reason == "temporary failure"


@pytest.mark.asyncio
async def test_kakao_send_skips_without_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KAKAO_SENDER_KEY", "")
    monkeypatch.setenv("BIZPPURIO_USER_ID", "")
    monkeypatch.setenv("BIZPPURIO_API_KEY", "")
    get_settings.cache_clear()

    result = await kakao_alimtalk.send_alimtalk(
        sender_key="",
        template_code="SNAIL_RESV_REQUESTED_V1",
        phone_number="010-0000-0000",
        variables={"#{shop_name}": "스네일 네일"},
    )

    assert result.status == "skipped"
    assert result.reason == "channel_not_configured"
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_kakao_retries_5xx_then_succeeds(
    mock_httpx_kakao: dict[str, object],
) -> None:
    mock_httpx_kakao["status_codes"] = [500, 502, 200]

    result = await kakao_alimtalk.send_alimtalk(
        sender_key="sender-key",
        template_code="SNAIL_RESV_REQUESTED_V1",
        phone_number="010-0000-0000",
        variables={"#{shop_name}": "스네일 네일", "content": "새 예약"},
    )

    assert result.status == "sent"
    assert len(mock_httpx_kakao["calls"]) == 3
