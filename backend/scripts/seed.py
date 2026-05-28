from __future__ import annotations

import argparse
import asyncio
import logging
import os
import secrets
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from random import Random
from uuid import UUID, uuid4

from app.core.config import get_settings
from app.core.security import hash_password
from app.models import Base
from app.models.accounts import BusinessVerification, Owner, User, UserOAuthIdentity
from app.models.community import Review, Snap, SnapImage
from app.models.design import Design, DesignDesigner, DesignImage
from app.models.enums import (
    AiAnalysisStatus,
    AssignedBy,
    PaymentMethod,
    ReservationStatus,
    VerificationStatus,
    Visibility,
)
from app.models.reservation import Reservation
from app.models.shop import Designer, DesignerSchedule, DesignerTimeOff, Shop, ShopBusinessHour
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

logger = logging.getLogger("snail.seed")

OWNER_COUNT = 5
DESIGNERS_PER_SHOP = 3
DESIGNS_PER_SHOP = 100
USER_COUNT = 20
SNAP_COUNT = 30
REVIEW_COUNT = 50

TAG_POOL = [
    "여리여리",
    "러블리",
    "심플",
    "프렌치",
    "글리터",
    "시럽",
    "내추럴",
    "시크",
    "봄",
    "데일리",
]
COLOR_POOL = ["핑크", "화이트", "베이지", "블루", "라벤더", "레드", "실버", "블랙"]
STYLE_POOL = ["simple", "french", "glitter", "syrup", "lovely"]
SHAPE_POOL = ["round", "oval", "square", "almond"]


@dataclass(frozen=True, slots=True)
class SeedSummary:
    owners: int
    shops: int
    designers: int
    designs: int
    users: int
    snaps: int
    reviews: int


def _owner_password() -> str:
    password = os.environ.get("SEED_OWNER_PASSWORD")
    if password:
        return password
    logger.warning("SEED_OWNER_PASSWORD is not set; generated non-repeatable local password")
    return secrets.token_urlsafe(24)


async def _truncate_all(session: AsyncSession) -> None:
    table_names = ", ".join(f'"{table.name}"' for table in reversed(Base.metadata.sorted_tables))
    await session.execute(text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE"))


def _placeholder_url(label: str) -> str:
    return f"https://placehold.co/512x512?text={label.replace(' ', '+')}"


def _rating_average(values: list[int]) -> Decimal:
    if not values:
        return Decimal("0.00")
    average = Decimal(sum(values)) / Decimal(len(values))
    return average.quantize(Decimal("0.01"))


async def _seed_owners_and_shops(
    session: AsyncSession,
    password_hash: str,
) -> tuple[list[Owner], list[Shop], dict[UUID, list[Designer]]]:
    owners: list[Owner] = []
    shops: list[Shop] = []
    designers_by_shop: dict[UUID, list[Designer]] = {}
    today = date.today()

    for index in range(OWNER_COUNT):
        owner = Owner(
            id=uuid4(),
            email=f"owner{index + 1}@seed.snail.local",
            password_hash=password_hash,
            representative_name=f"시드 대표 {index + 1}",
            phone_number=f"010-9000-{index + 1:04d}",
            verification_status=VerificationStatus.APPROVED,
        )
        session.add(owner)
        owners.append(owner)
    await session.flush()

    for index, owner in enumerate(owners):
        session.add(
            BusinessVerification(
                id=uuid4(),
                owner_id=owner.id,
                business_registration_number=f"100-00-{index + 1:05d}",
                document_url=_placeholder_url(f"license {index + 1}"),
                status=VerificationStatus.APPROVED,
                reviewed_at=datetime.now(UTC),
            )
        )
        shop = Shop(
            id=uuid4(),
            owner_id=owner.id,
            name=f"스네일 네일 {index + 1}",
            address=f"서울시 강남구 데모로 {index + 1}",
            address_detail=f"{index + 2}층",
            region="강남" if index % 2 == 0 else "홍대",
            phone_number=f"02-5000-{index + 1:04d}",
            introduction="데모용 승인 샵입니다.",
            thumbnail_url=_placeholder_url(f"shop {index + 1}"),
            visibility=Visibility.ACTIVE,
            payment_method=(
                PaymentMethod.ON_SITE if index < 3 else PaymentMethod.BANK_TRANSFER_GUIDE
            ),
            auto_accept=index == 0,
            reservation_policy="예약 변경과 취소는 샵으로 문의해주세요.",
            deposit_amount=10000 if index >= 3 else None,
            bank_name="스네일은행" if index >= 3 else None,
            bank_account_number=f"123-45-{index + 1:06d}" if index >= 3 else None,
            bank_account_holder=owner.representative_name if index >= 3 else None,
        )
        session.add(shop)
        shops.append(shop)
    await session.flush()

    for shop_index, shop in enumerate(shops):
        for weekday in range(7):
            is_closed = weekday == 6
            session.add(
                ShopBusinessHour(
                    id=uuid4(),
                    shop_id=shop.id,
                    weekday=weekday,
                    open_time=None if is_closed else time(10, 0),
                    close_time=None if is_closed else time(20, 0),
                    is_closed=is_closed,
                )
            )

        designers: list[Designer] = []
        for designer_index in range(DESIGNERS_PER_SHOP):
            designer = Designer(
                id=uuid4(),
                shop_id=shop.id,
                name=f"디자이너 {shop_index + 1}-{designer_index + 1}",
                position="시니어" if designer_index == 0 else "네일리스트",
                career_years=6 - designer_index,
                profile_image_url=_placeholder_url(
                    f"designer {shop_index + 1}-{designer_index + 1}"
                ),
                specialty_tags=["핑크", "심플"] if designer_index == 0 else ["아트", "글리터"],
                is_active=True,
            )
            session.add(designer)
            designers.append(designer)
        await session.flush()

        for designer_index, designer in enumerate(designers):
            for weekday in range(7):
                is_day_off = weekday == 6
                session.add(
                    DesignerSchedule(
                        id=uuid4(),
                        designer_id=designer.id,
                        weekday=weekday,
                        start_time=None if is_day_off else time(10, 0),
                        end_time=None if is_day_off else time(20, 0),
                        break_start_time=None if is_day_off else time(14, 0),
                        break_end_time=None if is_day_off else time(15, 0),
                        is_day_off=is_day_off,
                    )
                )
            if designer_index == 2:
                session.add(
                    DesignerTimeOff(
                        id=uuid4(),
                        designer_id=designer.id,
                        off_date=today + timedelta(days=7 + shop_index),
                        start_time=time(16, 0),
                        end_time=time(18, 0),
                        reason="데모 부분 휴무",
                    )
                )
        designers_by_shop[shop.id] = designers

    await session.flush()
    return owners, shops, designers_by_shop


async def _seed_designs(
    session: AsyncSession,
    rng: Random,
    shops: list[Shop],
    designers_by_shop: dict[UUID, list[Designer]],
) -> tuple[list[Design], dict[UUID, list[UUID]]]:
    designs: list[Design] = []
    design_designer_ids: dict[UUID, list[UUID]] = {}

    for shop_index, shop in enumerate(shops):
        shop_designers = designers_by_shop[shop.id]
        for local_index in range(DESIGNS_PER_SHOP):
            global_index = shop_index * DESIGNS_PER_SHOP + local_index + 1
            color = rng.choice(COLOR_POOL)
            style = rng.choice(STYLE_POOL)
            tags = list(dict.fromkeys([color, rng.choice(TAG_POOL), rng.choice(TAG_POOL)]))
            image_url = _placeholder_url(f"design {global_index}")
            design = Design(
                id=uuid4(),
                shop_id=shop.id,
                title=f"{color} {style} 네일 {global_index}",
                description=f"{color} 컬러 중심의 {style} 스타일 데모 디자인입니다.",
                base_price=rng.choice([30000, 35000, 40000, 45000, 50000, 60000, 70000]),
                duration_minutes=rng.choice([60, 90, 120]),
                thumbnail_url=image_url,
                visibility=Visibility.ACTIVE,
                ai_analysis_status=AiAnalysisStatus.DONE,
                owner_tags=[style, color],
                ai_tags=tags,
                color_palette=[color],
                style_category=style,
                nail_shape=rng.choice(SHAPE_POOL),
                ai_confidence=Decimal("0.910"),
                ai_model_version="seed-v1",
                search_indexed_at=datetime.now(UTC),
                embedding=None,
            )
            session.add(design)
            designs.append(design)
            linked_designers = rng.sample(shop_designers, k=rng.randint(1, len(shop_designers)))
            design_designer_ids[design.id] = [designer.id for designer in linked_designers]
            await session.flush()
            session.add(
                DesignImage(
                    id=uuid4(),
                    design_id=design.id,
                    original_url=image_url,
                    processed_url=None,
                    sort_order=0,
                    is_thumbnail=True,
                    width=512,
                    height=512,
                )
            )
            for designer in linked_designers:
                session.add(DesignDesigner(design_id=design.id, designer_id=designer.id))

    await session.flush()
    return designs, design_designer_ids


async def _seed_users(session: AsyncSession) -> list[User]:
    users: list[User] = []
    for index in range(USER_COUNT):
        apple_sub = f"seed-apple-{index + 1:02d}"
        user = User(
            id=uuid4(),
            apple_sub=apple_sub,
            email=f"user{index + 1}@seed.snail.local",
            nickname=f"seed_user_{index + 1:02d}",
            profile_image_url=_placeholder_url(f"user {index + 1}"),
            bio="데모 유저입니다.",
            interest_tags=["핑크", "심플"] if index % 2 == 0 else ["글리터", "프렌치"],
            is_active=True,
        )
        session.add(user)
        users.append(user)
    await session.flush()

    for user in users:
        session.add(
            UserOAuthIdentity(
                id=uuid4(),
                user_id=user.id,
                provider="apple",
                provider_sub=user.apple_sub or f"seed-apple-{user.id}",
                email=user.email,
                raw_payload={"mock_identity": True},
            )
        )
    await session.flush()
    return users


async def _seed_snaps(
    session: AsyncSession,
    rng: Random,
    users: list[User],
    designs: list[Design],
) -> list[Snap]:
    snaps: list[Snap] = []
    for index in range(SNAP_COUNT):
        design = rng.choice(designs) if index % 3 != 0 else None
        snap = Snap(
            id=uuid4(),
            user_id=rng.choice(users).id,
            tagged_shop_id=design.shop_id if design is not None else None,
            tagged_design_id=design.id if design is not None else None,
            body=f"데모 스네일 {index + 1}",
            tags=rng.sample(TAG_POOL, k=3),
            is_reservation_verified=False,
            like_count=rng.randint(0, 40),
            comment_count=rng.randint(0, 10),
            view_count=rng.randint(20, 300),
        )
        session.add(snap)
        snaps.append(snap)
    await session.flush()

    for index, snap in enumerate(snaps):
        session.add(
            SnapImage(
                id=uuid4(),
                snap_id=snap.id,
                image_url=_placeholder_url(f"snail {index + 1}"),
                sort_order=0,
            )
        )
    await session.flush()
    return snaps


async def _seed_reviews(
    session: AsyncSession,
    rng: Random,
    users: list[User],
    designs: list[Design],
    design_designer_ids: dict[UUID, list[UUID]],
    shops_by_id: dict[UUID, Shop],
) -> list[Review]:
    reviews: list[Review] = []
    ratings_by_shop: dict[UUID, list[int]] = {shop_id: [] for shop_id in shops_by_id}

    for index in range(REVIEW_COUNT):
        design = rng.choice(designs)
        user = rng.choice(users)
        designer_id = rng.choice(design_designer_ids[design.id])
        start_at = datetime.now(UTC) - timedelta(days=index + 1, hours=rng.randint(0, 8))
        reservation = Reservation(
            id=uuid4(),
            user_id=user.id,
            shop_id=design.shop_id,
            design_id=design.id,
            designer_id=designer_id,
            assigned_by=AssignedBy.USER,
            start_at=start_at,
            end_at=start_at + timedelta(minutes=design.duration_minutes),
            status=ReservationStatus.COMPLETED,
            user_request="데모 리뷰 기반 예약",
            total_price=design.base_price,
            payment_method_snapshot=shops_by_id[design.shop_id].payment_method,
            idempotency_key=f"seed-reservation-{uuid4()}",
            completed_at=start_at + timedelta(minutes=design.duration_minutes),
        )
        session.add(reservation)
        await session.flush()

        rating = rng.choice([4, 5, 5, 5, 3])
        ratings_by_shop[design.shop_id].append(rating)
        review = Review(
            id=uuid4(),
            reservation_id=reservation.id,
            user_id=user.id,
            shop_id=design.shop_id,
            design_id=design.id,
            rating=rating,
            body=f"데모 리뷰 {index + 1}: 시술이 만족스러웠습니다.",
            like_count=rng.randint(0, 15),
        )
        session.add(review)
        reviews.append(review)

    for shop_id, ratings in ratings_by_shop.items():
        shop = shops_by_id[shop_id]
        shop.review_count = len(ratings)
        shop.average_rating = _rating_average(ratings)

    await session.flush()
    return reviews


async def seed_database(*, reset: bool) -> SeedSummary:
    settings = get_settings()
    engine = create_async_engine(str(settings.DATABASE_URL), pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    started_at = datetime.now(UTC)
    rng = Random(20260527)  # noqa: S311 - deterministic demo seed data, not security-sensitive.

    async with session_factory() as session:
        if reset:
            await _truncate_all(session)
            await session.commit()

        password_hash = hash_password(_owner_password())
        owners, shops, designers_by_shop = await _seed_owners_and_shops(session, password_hash)
        designs, design_designer_ids = await _seed_designs(
            session,
            rng,
            shops,
            designers_by_shop,
        )
        users = await _seed_users(session)
        snaps = await _seed_snaps(session, rng, users, designs)
        reviews = await _seed_reviews(
            session,
            rng,
            users,
            designs,
            design_designer_ids,
            {shop.id: shop for shop in shops},
        )
        await session.commit()

    await engine.dispose()
    elapsed = (datetime.now(UTC) - started_at).total_seconds()
    summary = SeedSummary(
        owners=len(owners),
        shops=len(shops),
        designers=sum(len(designers) for designers in designers_by_shop.values()),
        designs=len(designs),
        users=len(users),
        snaps=len(snaps),
        reviews=len(reviews),
    )
    logger.info("seed.completed", extra={"summary": summary, "elapsed_sec": round(elapsed, 2)})
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed Snail demo data.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Truncate application tables before inserting seed data.",
    )
    return parser.parse_args()


async def async_main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    args = parse_args()
    summary = await seed_database(reset=bool(args.reset))
    logger.info("seed.summary %s", summary)


if __name__ == "__main__":
    asyncio.run(async_main())
