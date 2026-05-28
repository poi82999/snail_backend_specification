from datetime import UTC, datetime
from uuid import uuid4

from app.models.accounts import User
from app.models.design import Design
from app.models.enums import AssignedBy, PaymentMethod, ReservationStatus, Visibility
from app.models.reservation import Reservation
from app.models.shop import Designer, Shop
from app.services.notifications.templates import (
    NotificationTemplateKey,
    build_apns_payload,
    build_inbox_payload,
    build_kakao_payload,
    payload_from_models,
    render_apns,
    render_kakao,
)


def _context() -> tuple[Reservation, Shop, User, Designer, Design]:
    user = User(id=uuid4(), nickname="민지")
    shop = Shop(
        id=uuid4(),
        owner_id=uuid4(),
        name="스네일 네일",
        address="서울",
        phone_number="02-0000-0000",
        visibility=Visibility.ACTIVE,
        payment_method=PaymentMethod.BANK_TRANSFER_GUIDE,
    )
    designer = Designer(id=uuid4(), shop_id=shop.id, name="하나", specialty_tags=[])
    design = Design(
        id=uuid4(),
        shop_id=shop.id,
        title="핑크 프렌치",
        base_price=30000,
        duration_minutes=60,
    )
    reservation = Reservation(
        id=uuid4(),
        user_id=user.id,
        shop_id=shop.id,
        design_id=design.id,
        designer_id=designer.id,
        assigned_by=AssignedBy.USER,
        start_at=datetime(2026, 6, 1, 5, 30, tzinfo=UTC),
        end_at=datetime(2026, 6, 1, 6, 30, tzinfo=UTC),
        status=ReservationStatus.PAYMENT_PENDING,
        total_price=30000,
        payment_method_snapshot=PaymentMethod.BANK_TRANSFER_GUIDE,
        deposit_amount_snapshot=10000,
        bank_snapshot={
            "bank_name": "테스트은행",
            "account_number": "123-456",
            "account_holder": "대표",
        },
        idempotency_key="reservation-test",
    )
    return reservation, shop, user, designer, design


def test_build_inbox_payload_for_requested() -> None:
    reservation, shop, user, designer, design = _context()

    payload = build_inbox_payload(
        "RESERVATION_REQUESTED",
        reservation,
        shop,
        user,
        designer,
        design,
        {},
    )

    assert payload.title == "새 예약 요청"
    assert payload.resource_type == "reservation"
    assert payload.resource_id == reservation.id
    assert payload.deeplink.endswith(str(reservation.id))


def test_build_apns_payload_for_payment_required_includes_bank() -> None:
    reservation, shop, user, designer, design = _context()

    payload = build_apns_payload(
        "RESERVATION_PAYMENT_REQUIRED",
        reservation,
        shop,
        user,
        designer,
        design,
        {},
    )

    assert payload["aps"]["alert"]["title"] == "예약금 안내"
    assert "테스트은행" in payload["aps"]["alert"]["body"]
    assert payload["aps"]["sound"] == "default"
    assert payload["event"] == "RESERVATION_PAYMENT_REQUIRED"


def test_build_kakao_payload_uses_placeholder_template_code() -> None:
    reservation, shop, user, designer, design = _context()

    payload = build_kakao_payload(
        "RESERVATION_REQUESTED",
        reservation,
        shop,
        user,
        designer,
        design,
        {},
    )

    assert payload["templateCode"] == "SNAIL_RESV_REQUESTED_V1"
    assert "민지" in payload["content"]
    assert payload["metadata"]["reservation_id"] == str(reservation.id)


def test_build_apns_payload_for_completed_has_review_copy() -> None:
    reservation, shop, user, designer, design = _context()

    payload = build_apns_payload(
        "RESERVATION_COMPLETED",
        reservation,
        shop,
        user,
        designer,
        design,
        {},
    )

    assert payload["aps"]["alert"]["title"] == "시술 완료"
    assert "리뷰" in payload["aps"]["alert"]["body"]


def test_all_reservation_templates_render_for_kakao_and_apns() -> None:
    reservation, shop, user, designer, design = _context()
    payload = payload_from_models(reservation, shop, user, designer, design)

    for template_key in NotificationTemplateKey:
        kakao = render_kakao(template_key, payload)
        apns = render_apns(template_key, payload)

        assert kakao["template_code"].startswith("SNAIL_")
        assert "#{shop_name}" in kakao["variables"]
        assert apns["title"]
        assert apns["body"]
        assert apns["data"]["template_key"] == template_key.value
