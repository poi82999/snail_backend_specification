from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from app.api.errors import AppError
from app.models.enums import ActorType
from app.models.reservation import IdempotencyKey
from app.utils.idempotency import with_idempotency


class FakeResult:
    def __init__(self, record: IdempotencyKey | None) -> None:
        self.record = record

    def scalar_one_or_none(self) -> IdempotencyKey | None:
        return self.record


class FakeSession:
    def __init__(self, record: IdempotencyKey | None) -> None:
        self.record = record
        self.added: list[IdempotencyKey] = []
        self.flush_count = 0

    async def execute(self, statement: object) -> FakeResult:
        return FakeResult(self.record)

    def add(self, record: IdempotencyKey) -> None:
        self.added.append(record)
        self.record = record

    async def flush(self) -> None:
        self.flush_count += 1


@pytest.mark.asyncio
async def test_idempotency_same_key_same_hash_returns_cached_response() -> None:
    actor_id = uuid4()
    record = IdempotencyKey(
        actor_type="user",
        actor_id=actor_id,
        key="idem-key",
        request_hash="request-hash",
        response_status=201,
        response_body={"ok": True},
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    session = FakeSession(record)

    async with with_idempotency(
        session,
        ActorType.USER,
        actor_id,
        "idem-key",
        "request-hash",
    ) as context:
        assert context.cached is True
        assert context.response_status == 201
        assert context.response_body == {"ok": True}


@pytest.mark.asyncio
async def test_idempotency_same_key_different_hash_raises_conflict() -> None:
    actor_id = uuid4()
    record = IdempotencyKey(
        actor_type="user",
        actor_id=actor_id,
        key="idem-key",
        request_hash="request-hash",
        response_status=201,
        response_body={"ok": True},
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    session = FakeSession(record)

    with pytest.raises(AppError) as exc_info:
        async with with_idempotency(
            session,
            ActorType.USER,
            actor_id,
            "idem-key",
            "other-hash",
        ):
            pass

    assert exc_info.value.code == "IDEMPOTENCY_MISMATCH"
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_idempotency_new_key_updates_response_after_context() -> None:
    actor_id = uuid4()
    session = FakeSession(None)

    async with with_idempotency(
        session,
        ActorType.USER,
        actor_id,
        "idem-key",
        "request-hash",
    ) as context:
        assert context.cached is False
        context.set_response(201, {"ok": True})

    assert session.added[0].response_status == 201
    assert session.added[0].response_body == {"ok": True}
    assert session.flush_count == 2
