from http import HTTPStatus

import pytest
from app.api.errors import AppError
from app.models.enums import PaymentMethod, ReservationStatus
from app.services.reservation_policy import can_transition, validate_shop_payment_policy


def test_can_transition_allows_expected_matrix() -> None:
    allowed = {
        ("owner", ReservationStatus.PENDING, ReservationStatus.CONFIRMED),
        ("owner", ReservationStatus.PENDING, ReservationStatus.PAYMENT_PENDING),
        ("owner", ReservationStatus.PENDING, ReservationStatus.REJECTED),
        ("owner", ReservationStatus.PAYMENT_PENDING, ReservationStatus.CONFIRMED),
        ("owner", ReservationStatus.PAYMENT_PENDING, ReservationStatus.REJECTED),
        ("owner", ReservationStatus.PAYMENT_PENDING, ReservationStatus.CANCELLED_BY_SHOP),
        ("owner", ReservationStatus.CONFIRMED, ReservationStatus.COMPLETED),
        ("owner", ReservationStatus.CONFIRMED, ReservationStatus.NO_SHOW),
        ("owner", ReservationStatus.CONFIRMED, ReservationStatus.CANCELLED_BY_SHOP),
        ("user", ReservationStatus.PENDING, ReservationStatus.CANCELLED_BY_USER),
        ("user", ReservationStatus.PAYMENT_PENDING, ReservationStatus.CANCELLED_BY_USER),
        ("user", ReservationStatus.CONFIRMED, ReservationStatus.CANCELLED_BY_USER),
    }

    statuses = list(ReservationStatus)
    for actor in ("owner", "user"):
        for from_status in statuses:
            for to_status in statuses:
                assert can_transition(
                    actor=actor, from_status=from_status, to_status=to_status
                ) is ((actor, from_status, to_status) in allowed)


def test_validate_shop_payment_policy_raises_app_error() -> None:
    with pytest.raises(AppError) as exc_info:
        validate_shop_payment_policy(True, PaymentMethod.BANK_TRANSFER_GUIDE)

    assert exc_info.value.code == "INVALID_PAYMENT_POLICY"
    assert exc_info.value.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
