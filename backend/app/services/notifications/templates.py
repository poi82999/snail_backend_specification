from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC
from enum import StrEnum
from typing import Any, TypedDict, cast
from uuid import UUID
from zoneinfo import ZoneInfo

import structlog

from app.core.config import get_settings
from app.models.accounts import User
from app.models.design import Design
from app.models.reservation import Reservation
from app.models.shop import Designer, Shop

logger = structlog.get_logger()
KST = ZoneInfo("Asia/Seoul")


class NotificationTemplateKey(StrEnum):
    RESERVATION_REQUESTED = "RESERVATION_REQUESTED"
    RESERVATION_CONFIRMED = "RESERVATION_CONFIRMED"
    RESERVATION_PAYMENT_REQUIRED = "RESERVATION_PAYMENT_REQUIRED"
    RESERVATION_REJECTED = "RESERVATION_REJECTED"
    RESERVATION_CANCELLED_BY_SHOP = "RESERVATION_CANCELLED_BY_SHOP"
    RESERVATION_NO_SHOW = "RESERVATION_NO_SHOW"
    RESERVATION_COMPLETED = "RESERVATION_COMPLETED"
    RESERVATION_CANCELLED_BY_USER = "RESERVATION_CANCELLED_BY_USER"
    RESERVATION_REMINDER = "RESERVATION_REMINDER"


class ReservationNotificationPayload(TypedDict, total=False):
    reservation_id: str
    shop_id: str
    user_id: str
    owner_id: str
    designer_id: str
    design_id: str
    shop_name: str
    user_name: str
    designer_name: str
    design_title: str
    date: str
    time: str
    bank_snapshot: dict[str, object] | str | None
    deposit_amount: int | None
    reject_reason: str | None
    cancel_reason: str | None
    deeplink: str


class KakaoRenderResult(TypedDict):
    template_code: str
    variables: dict[str, str]
    content: str


class ApnsRenderResult(TypedDict):
    title: str
    body: str
    data: dict[str, str]


@dataclass(frozen=True, slots=True)
class InboxContent:
    title: str
    body: str
    resource_type: str
    resource_id: UUID | None
    deeplink: str
    metadata: dict[str, object]


KAKAO_TEMPLATE_CODES: dict[NotificationTemplateKey, str] = {
    NotificationTemplateKey.RESERVATION_REQUESTED: "SNAIL_RESV_REQUESTED_V1",
    NotificationTemplateKey.RESERVATION_CONFIRMED: "SNAIL_RESV_CONFIRMED_V1",
    NotificationTemplateKey.RESERVATION_PAYMENT_REQUIRED: "SNAIL_RESV_PAYMENT_REQUIRED_V1",
    NotificationTemplateKey.RESERVATION_REJECTED: "SNAIL_RESV_REJECTED_V1",
    NotificationTemplateKey.RESERVATION_CANCELLED_BY_SHOP: "SNAIL_RESV_CANCELLED_SHOP_V1",
    NotificationTemplateKey.RESERVATION_NO_SHOW: "SNAIL_RESV_NO_SHOW_V1",
    NotificationTemplateKey.RESERVATION_COMPLETED: "SNAIL_RESV_COMPLETED_V1",
    NotificationTemplateKey.RESERVATION_CANCELLED_BY_USER: "SNAIL_RESV_CANCELLED_USER_V1",
    NotificationTemplateKey.RESERVATION_REMINDER: "SNAIL_RESV_REMINDER_V1",
}


def _template_key(value: NotificationTemplateKey | str) -> NotificationTemplateKey:
    return value if isinstance(value, NotificationTemplateKey) else NotificationTemplateKey(value)


def _template_codes() -> dict[NotificationTemplateKey, str]:
    settings = get_settings()
    if not settings.KAKAO_TEMPLATE_CODES_JSON:
        return KAKAO_TEMPLATE_CODES
    try:
        raw = json.loads(settings.KAKAO_TEMPLATE_CODES_JSON)
    except json.JSONDecodeError:
        logger.warning("notification.template_codes.invalid_json")
        return KAKAO_TEMPLATE_CODES
    if not isinstance(raw, dict):
        logger.warning("notification.template_codes.invalid_shape")
        return KAKAO_TEMPLATE_CODES
    merged = dict(KAKAO_TEMPLATE_CODES)
    for key, value in raw.items():
        if not isinstance(key, str) or not isinstance(value, str):
            continue
        try:
            merged[NotificationTemplateKey(key)] = value
        except ValueError:
            logger.warning("notification.template_codes.unknown_key", template_key=key)
    return merged


def _text(value: object, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _reservation_id(payload: ReservationNotificationPayload) -> UUID | None:
    raw = payload.get("reservation_id")
    if not raw:
        return None
    try:
        return UUID(str(raw))
    except ValueError:
        return None


def _deeplink(payload: ReservationNotificationPayload, recipient: str) -> str:
    if payload.get("deeplink"):
        return _text(payload["deeplink"])
    reservation_id = payload.get("reservation_id")
    if recipient == "owner":
        return f"snail://owner/reservations/{reservation_id}"
    return f"snail://reservations/{reservation_id}"


def _bank_snapshot_text(payload: ReservationNotificationPayload) -> str:
    bank_snapshot = payload.get("bank_snapshot")
    if isinstance(bank_snapshot, str):
        bank_text = bank_snapshot
    elif isinstance(bank_snapshot, dict):
        bank_name = _text(bank_snapshot.get("bank_name"), "계좌")
        account_number = _text(bank_snapshot.get("account_number"))
        holder = _text(bank_snapshot.get("account_holder"))
        bank_text = f"{bank_name} {account_number} {holder}".strip()
    else:
        bank_text = "입금 계좌"

    deposit_amount = payload.get("deposit_amount")
    if isinstance(deposit_amount, int):
        return f"{bank_text} / {deposit_amount:,}원"
    return bank_text


def _title_body(
    template_key: NotificationTemplateKey,
    payload: ReservationNotificationPayload,
) -> tuple[str, str]:
    shop_name = _text(payload.get("shop_name"), "샵")
    user_name = _text(payload.get("user_name"), "고객")
    designer_name = _text(payload.get("designer_name"), "디자이너")
    design_title = _text(payload.get("design_title"), "예약 디자인")
    date = _text(payload.get("date"), "예약일")
    time = _text(payload.get("time"), "예약시간")

    if template_key == NotificationTemplateKey.RESERVATION_REQUESTED:
        return (
            "새 예약 요청",
            f"{user_name}님이 {date} {time}에 예약을 요청했어요. {designer_name} / {design_title}",
        )
    if template_key == NotificationTemplateKey.RESERVATION_CONFIRMED:
        return "예약 확정", f"{shop_name} 예약이 확정됐어요. {date} {time}에 만나요."
    if template_key == NotificationTemplateKey.RESERVATION_PAYMENT_REQUIRED:
        return "예약금 안내", f"{shop_name}이 예약을 수락했어요. {_bank_snapshot_text(payload)}"
    if template_key == NotificationTemplateKey.RESERVATION_REJECTED:
        reason = _text(payload.get("reject_reason"), "샵 사정")
        return "예약 거절", f"{shop_name} 예약이 거절됐어요. 사유: {reason}"
    if template_key == NotificationTemplateKey.RESERVATION_CANCELLED_BY_SHOP:
        reason = _text(payload.get("cancel_reason"), "샵 사정")
        return "예약 취소", f"{shop_name} 예약이 취소됐어요. 사유: {reason}"
    if template_key == NotificationTemplateKey.RESERVATION_CANCELLED_BY_USER:
        reason = _text(payload.get("cancel_reason"), "고객 요청")
        return "고객 예약 취소", f"{user_name}님이 {date} {time} 예약을 취소했어요. 사유: {reason}"
    if template_key == NotificationTemplateKey.RESERVATION_NO_SHOW:
        return "노쇼 처리", f"{shop_name} 예약이 노쇼로 처리됐어요."
    if template_key == NotificationTemplateKey.RESERVATION_COMPLETED:
        return "시술 완료", f"{shop_name} 방문은 어떠셨나요? 리뷰를 남겨주세요."
    if template_key == NotificationTemplateKey.RESERVATION_REMINDER:
        return "예약 리마인드", f"내일 {time} {shop_name} 예약이 있어요."
    return "예약 알림", f"{shop_name} 예약 상태가 변경됐어요."


def _variables(payload: ReservationNotificationPayload) -> dict[str, str]:
    return {
        "#{shop_name}": _text(payload.get("shop_name"), "샵"),
        "#{user_name}": _text(payload.get("user_name"), "고객"),
        "#{designer_name}": _text(payload.get("designer_name"), "디자이너"),
        "#{design_title}": _text(payload.get("design_title"), "예약 디자인"),
        "#{date}": _text(payload.get("date"), "예약일"),
        "#{time}": _text(payload.get("time"), "예약시간"),
        "#{bank_snapshot}": _bank_snapshot_text(payload),
        "#{reject_reason}": _text(payload.get("reject_reason"), "샵 사정"),
        "#{cancel_reason}": _text(payload.get("cancel_reason"), "고객 요청"),
    }


def render_kakao(
    template_key: NotificationTemplateKey | str,
    payload: ReservationNotificationPayload,
) -> KakaoRenderResult:
    key = _template_key(template_key)
    _, body = _title_body(key, payload)
    return {
        "template_code": _template_codes()[key],
        "variables": _variables(payload),
        "content": body,
    }


def render_apns(
    template_key: NotificationTemplateKey | str,
    payload: ReservationNotificationPayload,
) -> ApnsRenderResult:
    key = _template_key(template_key)
    title, body = _title_body(key, payload)
    return {
        "title": title,
        "body": body,
        "data": {
            "template_key": key.value,
            "event": key.value,
            "reservation_id": _text(payload.get("reservation_id")),
            "shop_id": _text(payload.get("shop_id")),
            "deeplink": _deeplink(payload, "user"),
        },
    }


def render_inbox(
    template_key: NotificationTemplateKey | str,
    payload: ReservationNotificationPayload,
) -> InboxContent:
    key = _template_key(template_key)
    title, body = _title_body(key, payload)
    metadata: dict[str, object] = {
        "template_key": key.value,
        "reservation_id": _text(payload.get("reservation_id")),
        "shop_id": _text(payload.get("shop_id")),
        "user_id": _text(payload.get("user_id")),
        "designer_id": _text(payload.get("designer_id")),
        "design_id": _text(payload.get("design_id")),
    }
    return InboxContent(
        title=title,
        body=body,
        resource_type="reservation",
        resource_id=_reservation_id(payload),
        deeplink=_deeplink(payload, "owner"),
        metadata=metadata,
    )


def _local_datetime(reservation: Reservation) -> tuple[str, str]:
    value = reservation.start_at
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    local = value.astimezone(KST)
    return local.strftime("%m/%d"), local.strftime("%H:%M")


def _user_name(user: User) -> str:
    return user.nickname or "고객"


def payload_from_models(
    reservation: Reservation,
    shop: Shop,
    user: User,
    designer: Designer,
    design: Design,
) -> ReservationNotificationPayload:
    local_date, local_time = _local_datetime(reservation)
    return {
        "reservation_id": str(reservation.id),
        "shop_id": str(shop.id),
        "user_id": str(user.id),
        "owner_id": str(shop.owner_id),
        "designer_id": str(designer.id),
        "design_id": str(design.id),
        "shop_name": shop.name,
        "user_name": _user_name(user),
        "designer_name": designer.name,
        "design_title": design.title,
        "date": local_date,
        "time": local_time,
        "bank_snapshot": reservation.bank_snapshot,
        "deposit_amount": reservation.deposit_amount_snapshot,
        "reject_reason": reservation.rejected_reason,
        "cancel_reason": reservation.cancelled_reason,
    }


def build_kakao_payload(
    template_code: str,
    reservation: Reservation,
    shop: Shop,
    user: User,
    designer: Designer,
    design: Design,
    meta: dict[str, object],
) -> dict[str, object]:
    payload = payload_from_models(reservation, shop, user, designer, design)
    payload.update(cast(ReservationNotificationPayload, meta))
    rendered = render_kakao(template_code, payload)
    return {
        "templateCode": rendered["template_code"],
        "content": rendered["content"],
        "variables": rendered["variables"],
        "metadata": {
            "reservation_id": str(reservation.id),
            "shop_id": str(shop.id),
            "user_id": str(user.id),
            "designer_id": str(designer.id),
            "design_id": str(design.id),
        },
    }


def build_apns_payload(
    template_code: str,
    reservation: Reservation,
    shop: Shop,
    user: User,
    designer: Designer,
    design: Design,
    meta: dict[str, object],
) -> dict[str, Any]:
    payload = payload_from_models(reservation, shop, user, designer, design)
    payload.update(cast(ReservationNotificationPayload, meta))
    rendered = render_apns(template_code, payload)
    return {
        "aps": {
            "alert": {
                "title": rendered["title"],
                "body": rendered["body"],
            },
            "sound": "default",
            "category": template_code,
            "mutable-content": 1,
        },
        **rendered["data"],
    }


def build_inbox_payload(
    template_code: str,
    reservation: Reservation,
    shop: Shop,
    user: User,
    designer: Designer,
    design: Design,
    meta: dict[str, object],
) -> InboxContent:
    payload = payload_from_models(reservation, shop, user, designer, design)
    payload.update(cast(ReservationNotificationPayload, meta))
    return render_inbox(template_code, payload)
