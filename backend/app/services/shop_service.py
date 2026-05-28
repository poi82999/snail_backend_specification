from datetime import time
from http import HTTPStatus
from uuid import UUID, uuid4

import structlog
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.api.errors import AppError
from app.models.accounts import Owner
from app.models.enums import (
    ActorType,
    PaymentMethod,
    UploadTargetType,
    VerificationStatus,
    Visibility,
)
from app.models.ops import UploadObject
from app.models.shop import Shop, ShopBusinessHour, ShopImage
from app.schemas.shops import BusinessHourEntry, ShopCreate, ShopImageCreate, ShopUpdate
from app.services.owner_service import get_me
from app.services.reservation_policy import validate_shop_payment_policy
from app.utils.storage import upload_public_url

logger = structlog.get_logger()


def _validate_payment_storage(payment_method: PaymentMethod, deposit_amount: int | None) -> None:
    if payment_method == PaymentMethod.ON_SITE and deposit_amount is not None:
        raise AppError(
            "INVALID_PAYMENT_POLICY",
            "현장 결제 샵은 예약금을 설정할 수 없습니다.",
            HTTPStatus.BAD_REQUEST,
        )
    if payment_method == PaymentMethod.BANK_TRANSFER_GUIDE and (
        deposit_amount is None or deposit_amount < 1000
    ):
        raise AppError(
            "INVALID_PAYMENT_POLICY",
            "계좌이체 안내 샵은 1,000원 이상의 예약금이 필요합니다.",
            HTTPStatus.BAD_REQUEST,
        )


async def _shop_with_details(session: AsyncSession, shop_id: UUID) -> Shop:
    shop = await session.scalar(
        select(Shop)
        .where(Shop.id == shop_id)
        .options(
            joinedload(Shop.owner),
            selectinload(Shop.images),
            selectinload(Shop.business_hours),
        )
    )
    if shop is None:
        raise AppError("SHOP_NOT_FOUND", "샵을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)
    return shop


async def get_my_shop(session: AsyncSession, owner_id: UUID) -> Shop | None:
    await get_me(session, owner_id)
    shop = await session.scalar(
        select(Shop)
        .where(Shop.owner_id == owner_id)
        .options(
            joinedload(Shop.owner),
            selectinload(Shop.images),
            selectinload(Shop.business_hours),
        )
    )
    return shop


async def _get_required_my_shop(session: AsyncSession, owner_id: UUID) -> Shop:
    shop = await get_my_shop(session, owner_id)
    if shop is None:
        raise AppError("SHOP_NOT_FOUND", "샵을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)
    return shop


async def create_shop(session: AsyncSession, owner_id: UUID, payload: ShopCreate) -> Shop:
    owner = await get_me(session, owner_id)
    if owner.verification_status != VerificationStatus.APPROVED:
        raise AppError(
            "OWNER_NOT_APPROVED",
            "사업자 인증 후 샵을 등록할 수 있습니다.",
            HTTPStatus.FORBIDDEN,
        )

    existing = await session.scalar(select(Shop.id).where(Shop.owner_id == owner_id))
    if existing is not None:
        raise AppError("SHOP_ALREADY_EXISTS", "이미 등록된 샵이 있습니다.", HTTPStatus.CONFLICT)

    validate_shop_payment_policy(payload.auto_accept, payload.payment_method)
    _validate_payment_storage(payload.payment_method, payload.deposit_amount)

    shop = Shop(
        id=uuid4(),
        owner_id=owner_id,
        name=payload.name,
        address=payload.address,
        address_detail=payload.address_detail,
        region=payload.region,
        latitude=payload.latitude,
        longitude=payload.longitude,
        phone_number=payload.phone_number,
        introduction=payload.introduction,
        visibility=Visibility.DRAFT,
        auto_accept=payload.auto_accept,
        reservation_policy=payload.reservation_policy,
        payment_method=payload.payment_method,
        deposit_amount=payload.deposit_amount,
        bank_name=payload.bank_name,
        bank_account_number=payload.bank_account_number,
        bank_account_holder=payload.bank_account_holder,
    )
    session.add(shop)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise AppError(
            "SHOP_ALREADY_EXISTS",
            "이미 등록된 샵이 있습니다.",
            HTTPStatus.CONFLICT,
        ) from exc
    await session.refresh(shop)
    logger.info("shop.created", owner_id=str(owner_id), shop_id=str(shop.id))
    return await _shop_with_details(session, shop.id)


async def update_shop(session: AsyncSession, owner_id: UUID, payload: ShopUpdate) -> Shop:
    shop = await _get_required_my_shop(session, owner_id)

    for field in ("name", "address", "phone_number", "payment_method", "auto_accept"):
        if field in payload.model_fields_set and getattr(payload, field) is None:
            raise AppError(
                "VALIDATION_ERROR",
                "필수 샵 정보는 비울 수 없습니다.",
                HTTPStatus.BAD_REQUEST,
            )

    payment_method = (
        payload.payment_method if payload.payment_method is not None else shop.payment_method
    )
    auto_accept = payload.auto_accept if payload.auto_accept is not None else shop.auto_accept
    deposit_amount = shop.deposit_amount
    if "deposit_amount" in payload.model_fields_set:
        deposit_amount = payload.deposit_amount

    validate_shop_payment_policy(auto_accept, payment_method)
    _validate_payment_storage(payment_method, deposit_amount)

    for field in (
        "name",
        "address",
        "address_detail",
        "region",
        "latitude",
        "longitude",
        "phone_number",
        "introduction",
        "payment_method",
        "deposit_amount",
        "bank_name",
        "bank_account_number",
        "bank_account_holder",
        "auto_accept",
        "reservation_policy",
    ):
        if field in payload.model_fields_set:
            setattr(shop, field, getattr(payload, field))

    await session.flush()
    await session.refresh(shop)
    logger.info("shop.updated", owner_id=str(owner_id), shop_id=str(shop.id))
    return await _shop_with_details(session, shop.id)


def _business_hour_by_weekday(entries: list[BusinessHourEntry]) -> dict[int, BusinessHourEntry]:
    by_weekday: dict[int, BusinessHourEntry] = {}
    for entry in entries:
        if entry.weekday in by_weekday:
            raise AppError(
                "INVALID_BUSINESS_HOURS",
                "요일별 영업시간은 중복될 수 없습니다.",
                HTTPStatus.BAD_REQUEST,
            )
        by_weekday[entry.weekday] = entry
    return by_weekday


def _validate_business_hour(entry: BusinessHourEntry) -> tuple[time | None, time | None, bool]:
    if entry.is_closed:
        return None, None, True
    if entry.open_time is None or entry.close_time is None:
        raise AppError(
            "INVALID_BUSINESS_HOURS",
            "영업일에는 시작 시간과 종료 시간이 필요합니다.",
            HTTPStatus.BAD_REQUEST,
        )
    if entry.open_time >= entry.close_time:
        raise AppError(
            "INVALID_BUSINESS_HOURS",
            "영업 시작 시간은 종료 시간보다 빨라야 합니다.",
            HTTPStatus.BAD_REQUEST,
        )
    return entry.open_time, entry.close_time, False


async def set_business_hours(
    session: AsyncSession,
    owner_id: UUID,
    entries: list[BusinessHourEntry],
) -> None:
    shop = await _get_required_my_shop(session, owner_id)
    by_weekday = _business_hour_by_weekday(entries)

    existing_hours = (
        await session.scalars(select(ShopBusinessHour).where(ShopBusinessHour.shop_id == shop.id))
    ).all()
    existing_by_weekday = {hour.weekday: hour for hour in existing_hours}

    for weekday in range(7):
        entry = by_weekday.get(
            weekday,
            BusinessHourEntry(weekday=weekday, open_time=None, close_time=None, is_closed=True),
        )
        open_time, close_time, is_closed = _validate_business_hour(entry)
        existing = existing_by_weekday.get(weekday)
        if existing is None:
            session.add(
                ShopBusinessHour(
                    id=uuid4(),
                    shop_id=shop.id,
                    weekday=weekday,
                    open_time=open_time,
                    close_time=close_time,
                    is_closed=is_closed,
                )
            )
        else:
            existing.open_time = open_time
            existing.close_time = close_time
            existing.is_closed = is_closed

    await session.flush()
    logger.info("shop.business_hours_set", owner_id=str(owner_id), shop_id=str(shop.id))


async def _get_owner_upload(
    session: AsyncSession,
    owner_id: UUID,
    object_key: str,
    target_type: UploadTargetType,
) -> UploadObject:
    upload = await session.scalar(
        select(UploadObject).where(
            UploadObject.object_key == object_key,
            UploadObject.owner_actor_type == ActorType.OWNER.value,
            UploadObject.owner_actor_id == owner_id,
            UploadObject.target_type == target_type,
        )
    )
    if upload is None:
        raise AppError("UPLOAD_NOT_FOUND", "업로드 파일을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)
    return upload


async def add_shop_image(
    session: AsyncSession,
    owner_id: UUID,
    payload: ShopImageCreate,
) -> ShopImage:
    shop = await _get_required_my_shop(session, owner_id)
    upload = await _get_owner_upload(
        session,
        owner_id,
        payload.upload_object_key,
        UploadTargetType.SHOP,
    )
    image_url = upload_public_url(upload)
    if payload.is_thumbnail:
        await session.execute(
            update(ShopImage).where(ShopImage.shop_id == shop.id).values(is_thumbnail=False)
        )
        shop.thumbnail_url = image_url

    image = ShopImage(
        id=uuid4(),
        shop_id=shop.id,
        image_url=image_url,
        sort_order=payload.sort_order,
        is_thumbnail=payload.is_thumbnail,
    )
    session.add(image)
    await session.flush()
    await session.refresh(image)
    logger.info(
        "shop.image_added", owner_id=str(owner_id), shop_id=str(shop.id), image_id=str(image.id)
    )
    return image


async def delete_shop_image(session: AsyncSession, owner_id: UUID, image_id: UUID) -> None:
    shop = await _get_required_my_shop(session, owner_id)
    image = await session.scalar(
        select(ShopImage).where(ShopImage.id == image_id, ShopImage.shop_id == shop.id)
    )
    if image is None:
        raise AppError(
            "SHOP_IMAGE_NOT_FOUND",
            "샵 이미지를 찾을 수 없습니다.",
            HTTPStatus.NOT_FOUND,
        )
    if image.is_thumbnail and shop.thumbnail_url == image.image_url:
        shop.thumbnail_url = None
    await session.delete(image)
    await session.flush()
    logger.info(
        "shop.image_deleted", owner_id=str(owner_id), shop_id=str(shop.id), image_id=str(image_id)
    )


async def get_public_shop(session: AsyncSession, shop_id: UUID) -> Shop:
    shop = await session.scalar(
        select(Shop)
        .join(Owner, Owner.id == Shop.owner_id)
        .where(
            Shop.id == shop_id,
            Shop.visibility == Visibility.ACTIVE,
            Owner.verification_status == VerificationStatus.APPROVED,
            Owner.is_active.is_(True),
        )
        .options(selectinload(Shop.images), selectinload(Shop.business_hours))
    )
    if shop is None:
        raise AppError("SHOP_NOT_FOUND", "샵을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)
    return shop
