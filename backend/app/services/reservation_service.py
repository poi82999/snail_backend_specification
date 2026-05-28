from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from http import HTTPStatus
from typing import Literal
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import structlog
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import AppError
from app.models.accounts import User
from app.models.design import Design, DesignDesigner, DesignOption
from app.models.enums import AssignedBy, PaymentMethod, ReservationStatus
from app.models.reservation import Reservation
from app.models.shop import Designer, Shop
from app.schemas.reservations import (
    ReservationCreate,
    ReservationDesignerSummary,
    ReservationDesignSummary,
    ReservationMe,
    ReservationOwner,
    ReservationShopSummary,
    ReservationUserSummary,
)
from app.services import availability_service
from app.services.notifications import router as notification_service
from app.services.notifications.templates import (
    NotificationTemplateKey,
    ReservationNotificationPayload,
)
from app.services.reservation_policy import (
    ACTIVE_USER_RESERVATION_STATUSES,
    MAX_ACTIVE_USER_RESERVATIONS,
    can_mark_no_show,
    can_transition,
    ensure_slot_not_in_past,
    next_status_after_owner_accept,
    normalize_utc,
    validate_shop_payment_policy,
)
from app.utils.pagination import CursorParams, paginate_query

logger = structlog.get_logger()
KST = ZoneInfo("Asia/Seoul")
# TODO(A7): RESERVATION_REMINDER는 별도 스케줄러에서 예약 전날/당일 인큐한다.


def _invalid_transition() -> AppError:
    return AppError(
        "INVALID_TRANSITION",
        "허용되지 않는 예약 상태 변경입니다.",
        HTTPStatus.CONFLICT,
    )


def _ensure_transition(
    from_status: ReservationStatus,
    to_status: ReservationStatus,
    actor: Literal["user", "owner"],
) -> None:
    if not can_transition(from_status, to_status, actor):
        raise _invalid_transition()


def _local_day_bounds_utc(target_date: date) -> tuple[datetime, datetime]:
    start = datetime.combine(target_date, time.min).replace(tzinfo=KST).astimezone(UTC)
    return start, start + timedelta(days=1)


def _bank_snapshot(shop: Shop) -> dict[str, object] | None:
    if shop.payment_method == PaymentMethod.ON_SITE:
        return None
    return {
        "bank_name": shop.bank_name,
        "account_number": shop.bank_account_number,
        "account_holder": shop.bank_account_holder,
    }


def _apply_snapshots(reservation: Reservation, shop: Shop) -> None:
    reservation.payment_method_snapshot = shop.payment_method
    reservation.deposit_amount_snapshot = (
        shop.deposit_amount if shop.payment_method == PaymentMethod.BANK_TRANSFER_GUIDE else None
    )
    reservation.bank_snapshot = _bank_snapshot(shop)
    reservation.reservation_policy_snapshot = shop.reservation_policy


async def _flush_or_slot_taken(session: AsyncSession) -> None:
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise AppError(
            "SLOT_TAKEN",
            "이미 예약된 시간입니다.",
            HTTPStatus.CONFLICT,
        ) from exc


async def _notification_payload(
    session: AsyncSession,
    reservation: Reservation,
) -> ReservationNotificationPayload | None:
    return await notification_service.build_reservation_notification_payload(session, reservation)


async def _notify_user(
    session: AsyncSession,
    reservation: Reservation,
    template_key: NotificationTemplateKey,
) -> None:
    try:
        payload = await _notification_payload(session, reservation)
        if payload is None:
            return
        await notification_service.send_to_user(
            session,
            None,
            reservation.user_id,
            template_key,
            payload,
        )
    except Exception as exc:
        logger.info(
            "reservation.notification.skipped",
            reservation_id=str(reservation.id),
            template_key=template_key.value,
            reason=exc.__class__.__name__,
        )


async def _notify_owner(
    session: AsyncSession,
    reservation: Reservation,
    owner_id: UUID,
    template_key: NotificationTemplateKey,
) -> None:
    try:
        payload = await _notification_payload(session, reservation)
        if payload is None:
            return
        await notification_service.send_to_owner(
            session,
            None,
            owner_id,
            template_key,
            payload,
        )
    except Exception as exc:
        logger.info(
            "reservation.notification.skipped",
            reservation_id=str(reservation.id),
            template_key=template_key.value,
            reason=exc.__class__.__name__,
        )


async def _get_owner_shop(session: AsyncSession, owner_id: UUID) -> Shop:
    shop = await session.scalar(select(Shop).where(Shop.owner_id == owner_id))
    if shop is None:
        raise AppError("SHOP_NOT_FOUND", "샵을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)
    return shop


async def _get_owner_reservation(
    session: AsyncSession,
    owner_id: UUID,
    reservation_id: UUID,
    *,
    for_update: bool = False,
) -> tuple[Reservation, Shop]:
    shop = await _get_owner_shop(session, owner_id)
    statement = select(Reservation).where(Reservation.id == reservation_id)
    if for_update:
        statement = statement.with_for_update()
    reservation = await session.scalar(statement)
    if reservation is None:
        raise AppError(
            "RESERVATION_NOT_FOUND",
            "예약을 찾을 수 없습니다.",
            HTTPStatus.NOT_FOUND,
        )
    if reservation.shop_id != shop.id:
        raise AppError("FORBIDDEN", "권한이 없습니다.", HTTPStatus.FORBIDDEN)
    return reservation, shop


async def _get_user_reservation(
    session: AsyncSession,
    user_id: UUID,
    reservation_id: UUID,
    *,
    for_update: bool = False,
) -> Reservation:
    statement = select(Reservation).where(
        Reservation.id == reservation_id,
        Reservation.user_id == user_id,
    )
    if for_update:
        statement = statement.with_for_update()
    reservation = await session.scalar(statement)
    if reservation is None:
        raise AppError(
            "RESERVATION_NOT_FOUND",
            "예약을 찾을 수 없습니다.",
            HTTPStatus.NOT_FOUND,
        )
    return reservation


async def _load_design_and_shop(session: AsyncSession, design_id: UUID) -> tuple[Design, Shop]:
    design = await session.scalar(
        select(Design).where(Design.id == design_id, Design.deleted_at.is_(None))
    )
    if design is None:
        raise AppError("DESIGN_NOT_FOUND", "디자인을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)
    shop = await session.get(Shop, design.shop_id)
    if shop is None:
        raise AppError("SHOP_NOT_FOUND", "샵을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)
    return design, shop


async def _lock_active_design_designers(
    session: AsyncSession,
    design: Design,
    designer_id: UUID | None,
) -> list[Designer]:
    statement = (
        select(Designer)
        .join(DesignDesigner, DesignDesigner.designer_id == Designer.id)
        .where(
            DesignDesigner.design_id == design.id,
            Designer.shop_id == design.shop_id,
            Designer.is_active.is_(True),
        )
        .order_by(Designer.id)
        .with_for_update()
    )
    if designer_id is not None:
        statement = statement.where(Designer.id == designer_id)
    designers = list((await session.scalars(statement)).all())
    if designer_id is not None and not designers:
        raise AppError(
            "DESIGNER_NOT_AVAILABLE",
            "해당 디자인을 담당할 수 있는 디자이너가 아닙니다.",
            HTTPStatus.UNPROCESSABLE_ENTITY,
        )
    if not designers:
        raise AppError(
            "NO_AVAILABLE_DESIGNER",
            "예약 가능한 디자이너가 없습니다.",
            HTTPStatus.CONFLICT,
        )
    return designers


async def _count_active_user_reservations(session: AsyncSession, user_id: UUID) -> int:
    count = await session.scalar(
        select(func.count())
        .select_from(Reservation)
        .where(
            Reservation.user_id == user_id,
            Reservation.status.in_(ACTIVE_USER_RESERVATION_STATUSES),
        )
    )
    return int(count or 0)


async def _ensure_user_limits(
    session: AsyncSession,
    user_id: UUID,
    shop_id: UUID,
    local_date: date,
) -> None:
    active_count = await _count_active_user_reservations(session, user_id)
    if active_count >= MAX_ACTIVE_USER_RESERVATIONS:
        raise AppError(
            "RESERVATION_LIMIT_EXCEEDED",
            "동시에 보유할 수 있는 활성 예약 수를 초과했습니다.",
            HTTPStatus.CONFLICT,
        )

    day_start, day_end = _local_day_bounds_utc(local_date)
    duplicate_id = await session.scalar(
        select(Reservation.id).where(
            Reservation.user_id == user_id,
            Reservation.shop_id == shop_id,
            Reservation.status.in_(ACTIVE_USER_RESERVATION_STATUSES),
            Reservation.start_at < day_end,
            Reservation.end_at > day_start,
        )
    )
    if duplicate_id is not None:
        raise AppError(
            "DUPLICATE_RESERVATION_SAME_DAY",
            "같은 샵에는 같은 날 한 번만 예약할 수 있습니다.",
            HTTPStatus.CONFLICT,
        )


async def _load_selected_options(
    session: AsyncSession,
    design_id: UUID,
    option_ids: list[UUID],
) -> list[DesignOption]:
    """선택 옵션이 모두 해당 디자인 소속 + 활성인지 검증 후 반환."""
    if not option_ids:
        return []
    unique_ids = list(dict.fromkeys(option_ids))
    options = list(
        (
            await session.scalars(
                select(DesignOption).where(
                    DesignOption.id.in_(unique_ids),
                    DesignOption.design_id == design_id,
                    DesignOption.is_active.is_(True),
                )
            )
        ).all()
    )
    if len(options) != len(unique_ids):
        raise AppError(
            "INVALID_DESIGN_OPTION",
            "선택한 옵션이 유효하지 않습니다.",
            HTTPStatus.UNPROCESSABLE_ENTITY,
        )
    return options


async def _resolve_designer_for_slot(
    session: AsyncSession,
    design: Design,
    start_at: datetime,
    requested_designer_id: UUID | None,
    effective_duration_minutes: int,
) -> tuple[UUID, AssignedBy]:
    target_date = start_at.astimezone(KST).date()
    slots = await availability_service.calculate_available_slots(
        session,
        design.id,
        target_date,
        effective_duration_minutes - design.duration_minutes,
    )
    target_slot = next(
        (
            slot
            for slot in slots
            if slot.start_at == start_at
            and slot.end_at == start_at + timedelta(minutes=effective_duration_minutes)
        ),
        None,
    )
    if target_slot is None:
        raise AppError("SLOT_TAKEN", "이미 예약된 시간입니다.", HTTPStatus.CONFLICT)

    if requested_designer_id is not None:
        if requested_designer_id not in target_slot.available_designer_ids:
            raise AppError("SLOT_TAKEN", "이미 예약된 시간입니다.", HTTPStatus.CONFLICT)
        return requested_designer_id, AssignedBy.USER

    return target_slot.available_designer_ids[0], AssignedBy.AUTO


async def create_reservation(
    session: AsyncSession,
    user_id: UUID,
    payload: ReservationCreate,
    idempotency_key: str,
) -> Reservation:
    design, shop = await _load_design_and_shop(session, payload.design_id)
    validate_shop_payment_policy(shop.auto_accept, shop.payment_method)

    start_at = normalize_utc(payload.start_at)
    ensure_slot_not_in_past(start_at)
    local_date = start_at.astimezone(KST).date()
    await _ensure_user_limits(session, user_id, shop.id, local_date)

    options = await _load_selected_options(session, design.id, payload.selected_option_ids)
    extra_duration = sum(option.duration_delta_min for option in options)
    total_price = design.base_price + sum(option.price_delta for option in options)
    effective_duration = design.duration_minutes + extra_duration

    await _lock_active_design_designers(session, design, payload.designer_id)
    designer_id, assigned_by = await _resolve_designer_for_slot(
        session,
        design,
        start_at,
        payload.designer_id,
        effective_duration,
    )
    end_at = start_at + timedelta(minutes=effective_duration)

    status = ReservationStatus.CONFIRMED if shop.auto_accept else ReservationStatus.PENDING
    reservation = Reservation(
        id=uuid4(),
        user_id=user_id,
        shop_id=shop.id,
        design_id=design.id,
        designer_id=designer_id,
        assigned_by=assigned_by,
        start_at=start_at,
        end_at=end_at,
        status=status,
        user_request=payload.user_request,
        selected_option_ids=[str(option.id) for option in options],
        total_price=total_price,
        payment_method_snapshot=shop.payment_method,
        idempotency_key=idempotency_key,
    )
    if status == ReservationStatus.CONFIRMED:
        _apply_snapshots(reservation, shop)

    session.add(reservation)
    await _flush_or_slot_taken(session)
    await session.refresh(reservation)

    await _notify_owner(
        session,
        reservation,
        shop.owner_id,
        NotificationTemplateKey.RESERVATION_REQUESTED,
    )
    if status == ReservationStatus.CONFIRMED:
        await _notify_user(session, reservation, NotificationTemplateKey.RESERVATION_CONFIRMED)
    logger.info("reservation.created", reservation_id=str(reservation.id), user_id=str(user_id))
    return reservation


async def owner_accept(
    session: AsyncSession,
    owner_id: UUID,
    reservation_id: UUID,
) -> Reservation:
    reservation, shop = await _get_owner_reservation(
        session,
        owner_id,
        reservation_id,
        for_update=True,
    )
    next_status = next_status_after_owner_accept(shop.payment_method)
    _ensure_transition(reservation.status, next_status, "owner")
    _apply_snapshots(reservation, shop)
    reservation.status = next_status
    if next_status == ReservationStatus.PAYMENT_PENDING:
        reservation.user_payment_notified_at = datetime.now(UTC)

    await _flush_or_slot_taken(session)
    await session.refresh(reservation)
    await _notify_user(
        session,
        reservation,
        NotificationTemplateKey.RESERVATION_PAYMENT_REQUIRED
        if next_status == ReservationStatus.PAYMENT_PENDING
        else NotificationTemplateKey.RESERVATION_CONFIRMED,
    )
    logger.info("reservation.accepted", reservation_id=str(reservation.id), owner_id=str(owner_id))
    return reservation


async def owner_confirm_payment(
    session: AsyncSession,
    owner_id: UUID,
    reservation_id: UUID,
) -> Reservation:
    reservation, _ = await _get_owner_reservation(
        session,
        owner_id,
        reservation_id,
        for_update=True,
    )
    _ensure_transition(reservation.status, ReservationStatus.CONFIRMED, "owner")
    if reservation.payment_method_snapshot != PaymentMethod.BANK_TRANSFER_GUIDE:
        raise AppError(
            "INVALID_PAYMENT_POLICY",
            "계좌이체 안내 예약만 입금 확인할 수 있습니다.",
            HTTPStatus.CONFLICT,
        )
    reservation.status = ReservationStatus.CONFIRMED
    reservation.owner_payment_confirmed_at = datetime.now(UTC)

    await _flush_or_slot_taken(session)
    await session.refresh(reservation)
    await _notify_user(session, reservation, NotificationTemplateKey.RESERVATION_CONFIRMED)
    logger.info(
        "reservation.payment_confirmed",
        reservation_id=str(reservation.id),
        owner_id=str(owner_id),
    )
    return reservation


async def owner_reject(
    session: AsyncSession,
    owner_id: UUID,
    reservation_id: UUID,
    reject_reason: str,
) -> Reservation:
    reservation, _ = await _get_owner_reservation(
        session,
        owner_id,
        reservation_id,
        for_update=True,
    )
    _ensure_transition(reservation.status, ReservationStatus.REJECTED, "owner")
    reservation.status = ReservationStatus.REJECTED
    reservation.rejected_reason = reject_reason

    await session.flush()
    await session.refresh(reservation)
    await _notify_user(session, reservation, NotificationTemplateKey.RESERVATION_REJECTED)
    logger.info("reservation.rejected", reservation_id=str(reservation.id), owner_id=str(owner_id))
    return reservation


async def shop_cancel(
    session: AsyncSession,
    owner_id: UUID,
    reservation_id: UUID,
    cancel_reason: str,
) -> Reservation:
    reservation, _ = await _get_owner_reservation(
        session,
        owner_id,
        reservation_id,
        for_update=True,
    )
    _ensure_transition(reservation.status, ReservationStatus.CANCELLED_BY_SHOP, "owner")
    reservation.status = ReservationStatus.CANCELLED_BY_SHOP
    reservation.cancelled_reason = cancel_reason

    await session.flush()
    await session.refresh(reservation)
    await _notify_user(
        session,
        reservation,
        NotificationTemplateKey.RESERVATION_CANCELLED_BY_SHOP,
    )
    logger.info(
        "reservation.cancelled_by_shop",
        reservation_id=str(reservation.id),
        owner_id=str(owner_id),
    )
    return reservation


async def user_cancel(
    session: AsyncSession,
    user_id: UUID,
    reservation_id: UUID,
    cancel_reason: str,
) -> Reservation:
    reservation = await _get_user_reservation(
        session,
        user_id,
        reservation_id,
        for_update=True,
    )
    _ensure_transition(reservation.status, ReservationStatus.CANCELLED_BY_USER, "user")
    reservation.status = ReservationStatus.CANCELLED_BY_USER
    reservation.cancelled_reason = cancel_reason

    await session.flush()
    await session.refresh(reservation)
    shop = await session.get(Shop, reservation.shop_id)
    if shop is not None:
        await _notify_owner(
            session,
            reservation,
            shop.owner_id,
            NotificationTemplateKey.RESERVATION_CANCELLED_BY_USER,
        )
    logger.info(
        "reservation.cancelled_by_user",
        reservation_id=str(reservation.id),
        user_id=str(user_id),
    )
    return reservation


async def mark_no_show(
    session: AsyncSession,
    owner_id: UUID,
    reservation_id: UUID,
) -> Reservation:
    reservation, _ = await _get_owner_reservation(
        session,
        owner_id,
        reservation_id,
        for_update=True,
    )
    _ensure_transition(reservation.status, ReservationStatus.NO_SHOW, "owner")
    if not can_mark_no_show(reservation.status, reservation.start_at):
        raise AppError(
            "NO_SHOW_TOO_EARLY",
            "예약 시작 30분 후부터 노쇼 처리할 수 있습니다.",
            HTTPStatus.CONFLICT,
        )
    reservation.status = ReservationStatus.NO_SHOW
    reservation.no_show_at = datetime.now(UTC)

    await session.flush()
    await session.refresh(reservation)
    await _notify_user(session, reservation, NotificationTemplateKey.RESERVATION_NO_SHOW)
    logger.info("reservation.no_show", reservation_id=str(reservation.id), owner_id=str(owner_id))
    return reservation


async def mark_completed(
    session: AsyncSession,
    owner_id: UUID,
    reservation_id: UUID,
) -> Reservation:
    reservation, _ = await _get_owner_reservation(
        session,
        owner_id,
        reservation_id,
        for_update=True,
    )
    _ensure_transition(reservation.status, ReservationStatus.COMPLETED, "owner")
    reservation.status = ReservationStatus.COMPLETED
    reservation.completed_at = datetime.now(UTC)

    await session.flush()
    await session.refresh(reservation)
    await _notify_user(session, reservation, NotificationTemplateKey.RESERVATION_COMPLETED)
    logger.info("reservation.completed", reservation_id=str(reservation.id), owner_id=str(owner_id))
    return reservation


async def get_user_reservation(
    session: AsyncSession,
    user_id: UUID,
    reservation_id: UUID,
) -> Reservation:
    return await _get_user_reservation(session, user_id, reservation_id)


async def list_user_reservations(
    session: AsyncSession,
    user_id: UUID,
    status: ReservationStatus | None,
    params: CursorParams,
) -> tuple[list[Reservation], str | None]:
    statement = select(Reservation).where(Reservation.user_id == user_id)
    if status is not None:
        statement = statement.where(Reservation.status == status)
    return await paginate_query(session, statement, Reservation, params)


async def get_owner_reservation(
    session: AsyncSession,
    owner_id: UUID,
    reservation_id: UUID,
) -> Reservation:
    reservation, _ = await _get_owner_reservation(session, owner_id, reservation_id)
    return reservation


async def list_owner_reservations(
    session: AsyncSession,
    owner_id: UUID,
    status: ReservationStatus | None,
    from_date: date | None,
    to_date: date | None,
    params: CursorParams,
) -> tuple[list[Reservation], str | None]:
    if from_date is not None and to_date is not None and from_date > to_date:
        raise AppError(
            "INVALID_DATE_RANGE",
            "조회 시작일은 종료일보다 늦을 수 없습니다.",
            HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    shop = await _get_owner_shop(session, owner_id)
    statement = select(Reservation).where(Reservation.shop_id == shop.id)
    if status is not None:
        statement = statement.where(Reservation.status == status)
    if from_date is not None:
        start, _ = _local_day_bounds_utc(from_date)
        statement = statement.where(Reservation.end_at > start)
    if to_date is not None:
        _, end = _local_day_bounds_utc(to_date)
        statement = statement.where(Reservation.start_at < end)
    return await paginate_query(session, statement, Reservation, params)


def _shop_summary(shop: Shop | None) -> ReservationShopSummary | None:
    if shop is None:
        return None
    return ReservationShopSummary(
        id=shop.id,
        name=shop.name,
        region=shop.region,
        thumbnail_url=shop.thumbnail_url,
    )


def _designer_summary(designer: Designer | None) -> ReservationDesignerSummary | None:
    if designer is None:
        return None
    return ReservationDesignerSummary(
        id=designer.id,
        name=designer.name,
        position=designer.position,
        profile_image_url=designer.profile_image_url,
    )


def _design_summary(design: Design | None) -> ReservationDesignSummary | None:
    if design is None:
        return None
    return ReservationDesignSummary(
        id=design.id,
        title=design.title,
        base_price=design.base_price,
        duration_minutes=design.duration_minutes,
        thumbnail_url=design.thumbnail_url,
    )


def _user_summary(user: User | None) -> ReservationUserSummary | None:
    if user is None:
        return None
    return ReservationUserSummary(
        id=user.id,
        nickname=user.nickname,
        profile_image_url=user.profile_image_url,
    )


async def to_me(session: AsyncSession, reservation: Reservation) -> ReservationMe:
    shop = await session.get(Shop, reservation.shop_id)
    designer = await session.get(Designer, reservation.designer_id)
    design = await session.get(Design, reservation.design_id)
    return ReservationMe(
        id=reservation.id,
        shop_id=reservation.shop_id,
        design_id=reservation.design_id,
        designer_id=reservation.designer_id,
        assigned_by=reservation.assigned_by,
        start_at=normalize_utc(reservation.start_at),
        end_at=normalize_utc(reservation.end_at),
        status=reservation.status,
        user_request=reservation.user_request,
        total_price=reservation.total_price,
        payment_method_snapshot=reservation.payment_method_snapshot,
        deposit_amount_snapshot=reservation.deposit_amount_snapshot,
        bank_snapshot=reservation.bank_snapshot,
        reservation_policy_snapshot=reservation.reservation_policy_snapshot,
        rejected_reason=reservation.rejected_reason,
        cancelled_reason=reservation.cancelled_reason,
        user_payment_notified_at=reservation.user_payment_notified_at,
        owner_payment_confirmed_at=reservation.owner_payment_confirmed_at,
        reminder_sent_at=reservation.reminder_sent_at,
        completed_at=reservation.completed_at,
        no_show_at=reservation.no_show_at,
        shop=_shop_summary(shop),
        designer=_designer_summary(designer),
        design=_design_summary(design),
        created_at=reservation.created_at,
        updated_at=reservation.updated_at,
    )


async def to_owner(session: AsyncSession, reservation: Reservation) -> ReservationOwner:
    base = await to_me(session, reservation)
    user = await session.get(User, reservation.user_id)
    return ReservationOwner(
        **base.model_dump(),
        user_id=reservation.user_id,
        user=_user_summary(user),
    )


owner_accept_reservation = owner_accept
owner_reject_reservation = owner_reject
owner_cancel_reservation = shop_cancel
owner_mark_no_show = mark_no_show
owner_complete_reservation = mark_completed
user_cancel_reservation = user_cancel
to_public = to_me
