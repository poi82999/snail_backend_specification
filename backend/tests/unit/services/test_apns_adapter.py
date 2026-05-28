from types import SimpleNamespace
from uuid import uuid4

import pytest
from app.core.config import get_settings
from app.models.accounts import UserDeviceToken
from app.services.notifications import apns
from sqlalchemy.ext.asyncio import AsyncSession
from tests.community_factories import create_user


class _FirebaseTokenError(Exception):
    def __init__(self, code: str) -> None:
        self.code = code


def _batch_response(*responses: object) -> SimpleNamespace:
    return SimpleNamespace(
        responses=list(responses),
        success_count=sum(1 for response in responses if response.success),
    )


@pytest.fixture
def mock_firebase(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "./secrets/test-firebase.json")
    get_settings.cache_clear()
    monkeypatch.setattr(apns, "_firebase_app", lambda: object())


@pytest.mark.asyncio
async def test_apns_send_push_succeeds(
    mock_firebase: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_send_with_retry(**_: object) -> SimpleNamespace:
        return _batch_response(
            SimpleNamespace(success=True, message_id="fcm-message-1", exception=None)
        )

    monkeypatch.setattr(apns, "_send_with_retry", fake_send_with_retry)

    result = await apns.send_push(
        device_tokens=["token-1"],
        title="예약",
        body="확정",
        data={"reservation_id": "r1"},
    )

    assert result.status == "sent"
    assert result.provider_message_id == "fcm-message-1"
    assert result.results[0].success is True


@pytest.mark.asyncio
async def test_apns_invalid_token_is_deactivated(
    db_session: AsyncSession,
    mock_firebase: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = await create_user(db_session)
    token = UserDeviceToken(id=uuid4(), user_id=user.id, token="bad-token")
    db_session.add(token)
    await db_session.flush()

    async def fake_send_with_retry(**_: object) -> SimpleNamespace:
        return _batch_response(
            SimpleNamespace(
                success=False,
                message_id=None,
                exception=_FirebaseTokenError("UNREGISTERED"),
            )
        )

    monkeypatch.setattr(apns, "_send_with_retry", fake_send_with_retry)

    result = await apns.send_push(
        session=db_session,
        device_tokens=["bad-token"],
        title="예약",
        body="확정",
        data={"reservation_id": "r1"},
    )

    assert result.status == "failed"
    assert result.retryable is False
    assert result.invalid_tokens == ["bad-token"]
    assert token.is_active is False


@pytest.mark.asyncio
async def test_apns_send_skips_without_firebase_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    get_settings.cache_clear()

    result = await apns.send_push(
        device_tokens=["token-1"],
        title="예약",
        body="확정",
        data={"reservation_id": "r1"},
    )

    assert result.status == "skipped"
    assert result.reason == "channel_not_configured"
    get_settings.cache_clear()
