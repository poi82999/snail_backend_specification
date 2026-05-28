from datetime import time
from http import HTTPStatus
from uuid import uuid4

import pytest
from app.api.errors import AppError
from app.core.security import hash_password
from app.models.accounts import Owner
from app.models.design import Design, DesignDesigner
from app.models.enums import VerificationStatus
from app.models.shop import Designer, Shop
from app.schemas.designers import DesignerCreate, DesignerScheduleSet, ScheduleEntry
from app.services import designer_service
from sqlalchemy.ext.asyncio import AsyncSession


async def _owner(db_session: AsyncSession) -> Owner:
    owner = Owner(
        id=uuid4(),
        email=f"{uuid4().hex}@example.com",
        password_hash=hash_password("Strong123"),
        representative_name="대표",
        phone_number="010-0000-0000",
        verification_status=VerificationStatus.APPROVED,
    )
    db_session.add(owner)
    await db_session.flush()
    return owner


async def _shop(db_session: AsyncSession, owner: Owner) -> Shop:
    shop = Shop(
        id=uuid4(),
        owner_id=owner.id,
        name="테스트 샵",
        address="서울시 강남구",
        phone_number="02-0000-0000",
    )
    db_session.add(shop)
    await db_session.flush()
    return shop


async def _designer(db_session: AsyncSession, shop: Shop) -> Designer:
    designer = Designer(
        id=uuid4(),
        shop_id=shop.id,
        name="디자이너",
        specialty_tags=[],
    )
    db_session.add(designer)
    await db_session.flush()
    return designer


@pytest.mark.asyncio
async def test_create_designer_blocks_owner_without_own_shop(db_session: AsyncSession) -> None:
    shop_owner = await _owner(db_session)
    other_owner = await _owner(db_session)
    await _shop(db_session, shop_owner)

    with pytest.raises(AppError) as exc_info:
        await designer_service.create_designer(
            db_session,
            other_owner.id,
            DesignerCreate(name="타샵 디자이너", specialty_tags=[]),
        )

    assert exc_info.value.code == "SHOP_NOT_FOUND"
    assert exc_info.value.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_soft_disable_designer_with_linked_design(db_session: AsyncSession) -> None:
    owner = await _owner(db_session)
    shop = await _shop(db_session, owner)
    designer = await _designer(db_session, shop)
    design = Design(
        id=uuid4(),
        shop_id=shop.id,
        title="연결 디자인",
        base_price=30000,
        duration_minutes=60,
    )
    db_session.add(design)
    await db_session.flush()
    db_session.add(DesignDesigner(design_id=design.id, designer_id=designer.id))
    await db_session.flush()

    await designer_service.soft_disable_designer(db_session, owner.id, designer.id)

    assert designer.is_active is False


@pytest.mark.asyncio
async def test_set_designer_schedule_rejects_less_than_seven_entries(
    db_session: AsyncSession,
) -> None:
    owner = await _owner(db_session)
    shop = await _shop(db_session, owner)
    designer = await _designer(db_session, shop)

    with pytest.raises(AppError) as exc_info:
        await designer_service.set_designer_schedule(
            db_session,
            owner.id,
            designer.id,
            DesignerScheduleSet(
                entries=[
                    ScheduleEntry(
                        weekday=0,
                        start_time=time(10, 0),
                        end_time=time(18, 0),
                        is_day_off=False,
                    )
                ]
            ),
        )

    assert exc_info.value.code == "INVALID_DESIGNER_SCHEDULE"
    assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
