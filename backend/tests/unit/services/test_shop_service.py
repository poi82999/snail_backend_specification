from datetime import time
from http import HTTPStatus
from uuid import uuid4

import pytest
from app.api.errors import AppError
from app.core.security import hash_password
from app.models.accounts import Owner
from app.models.enums import PaymentMethod, VerificationStatus
from app.models.shop import Shop
from app.schemas.shops import BusinessHourEntry, ShopCreate, ShopUpdate
from app.services import shop_service
from sqlalchemy.ext.asyncio import AsyncSession


def _shop_create(**overrides: object) -> ShopCreate:
    data: dict[str, object] = {
        "name": "테스트 샵",
        "address": "서울시 강남구",
        "phone_number": "02-0000-0000",
        "payment_method": PaymentMethod.ON_SITE,
        "auto_accept": False,
    }
    data.update(overrides)
    return ShopCreate.model_validate(data)


async def _owner(db_session: AsyncSession, *, approved: bool) -> Owner:
    owner = Owner(
        id=uuid4(),
        email=f"{uuid4().hex}@example.com",
        password_hash=hash_password("Strong123"),
        representative_name="대표",
        phone_number="010-0000-0000",
        verification_status=(
            VerificationStatus.APPROVED if approved else VerificationStatus.PENDING
        ),
    )
    db_session.add(owner)
    await db_session.flush()
    return owner


async def _shop(db_session: AsyncSession, owner: Owner) -> Shop:
    shop = Shop(
        id=uuid4(),
        owner_id=owner.id,
        name="기존 샵",
        address="서울시 서초구",
        phone_number="02-1111-1111",
    )
    db_session.add(shop)
    await db_session.flush()
    return shop


@pytest.mark.asyncio
async def test_create_shop_rejects_unapproved_owner(db_session: AsyncSession) -> None:
    owner = await _owner(db_session, approved=False)

    with pytest.raises(AppError) as exc_info:
        await shop_service.create_shop(db_session, owner.id, _shop_create())

    assert exc_info.value.code == "OWNER_NOT_APPROVED"
    assert exc_info.value.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_create_shop_rejects_duplicate_shop(db_session: AsyncSession) -> None:
    owner = await _owner(db_session, approved=True)
    await _shop(db_session, owner)

    with pytest.raises(AppError) as exc_info:
        await shop_service.create_shop(db_session, owner.id, _shop_create())

    assert exc_info.value.code == "SHOP_ALREADY_EXISTS"
    assert exc_info.value.status_code == HTTPStatus.CONFLICT


@pytest.mark.asyncio
async def test_create_shop_uses_payment_policy_validator(db_session: AsyncSession) -> None:
    owner = await _owner(db_session, approved=True)

    with pytest.raises(AppError) as exc_info:
        await shop_service.create_shop(
            db_session,
            owner.id,
            _shop_create(
                payment_method=PaymentMethod.BANK_TRANSFER_GUIDE,
                deposit_amount=1000,
                auto_accept=True,
            ),
        )
    assert exc_info.value.code == "INVALID_PAYMENT_POLICY"
    assert exc_info.value.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_update_shop_blocks_other_owner(db_session: AsyncSession) -> None:
    owner = await _owner(db_session, approved=True)
    other_owner = await _owner(db_session, approved=True)
    await _shop(db_session, owner)

    with pytest.raises(AppError) as exc_info:
        await shop_service.update_shop(
            db_session,
            other_owner.id,
            ShopUpdate(name="다른 사장님 수정"),
        )

    assert exc_info.value.code == "SHOP_NOT_FOUND"
    assert exc_info.value.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_business_hours_rejects_invalid_time_range(db_session: AsyncSession) -> None:
    owner = await _owner(db_session, approved=True)
    await _shop(db_session, owner)

    with pytest.raises(AppError) as exc_info:
        await shop_service.set_business_hours(
            db_session,
            owner.id,
            [
                BusinessHourEntry(
                    weekday=0,
                    open_time=time(12, 0),
                    close_time=time(11, 0),
                    is_closed=False,
                )
            ],
        )

    assert exc_info.value.code == "INVALID_BUSINESS_HOURS"
    assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
