from datetime import UTC, datetime
from uuid import uuid4

import pytest
from app.api.errors import AppError
from app.utils.pagination import decode_cursor, encode_cursor


def test_cursor_round_trip() -> None:
    created_at = datetime(2026, 5, 27, 12, 30, tzinfo=UTC)
    id_ = uuid4()

    decoded_created_at, decoded_id = decode_cursor(encode_cursor(created_at, id_))

    assert decoded_created_at == created_at
    assert decoded_id == id_


def test_decode_cursor_rejects_invalid_value() -> None:
    with pytest.raises(AppError) as exc_info:
        decode_cursor("not-a-valid-cursor")

    assert exc_info.value.code == "INVALID_CURSOR"
    assert exc_info.value.status_code == 400
