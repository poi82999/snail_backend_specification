from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.core.security import hash_password, issue_access_token
from app.models.accounts import Owner, User
from app.models.community import Comment, Review, Snap
from app.models.design import Design
from app.models.enums import (
    ActorType,
    AiAnalysisStatus,
    PaymentMethod,
    ReservationStatus,
    UploadTargetType,
    VerificationStatus,
    Visibility,
)
from app.models.ops import UploadObject
from app.models.reservation import Reservation
from app.models.shop import Designer, Shop
from sqlalchemy.ext.asyncio import AsyncSession


def auth_headers(token: str, idempotency_key: str | None = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {token}"}
    if idempotency_key is not None:
        headers["Idempotency-Key"] = idempotency_key
    return headers


async def create_user(session: AsyncSession, nickname: str | None = None) -> User:
    user = User(
        id=uuid4(),
        apple_sub=f"apple-{uuid4().hex}",
        email=f"{uuid4().hex}@example.com",
        nickname=nickname or f"user_{uuid4().hex[:10]}",
    )
    session.add(user)
    await session.flush()
    return user


def user_token(user: User) -> str:
    return issue_access_token(ActorType.USER, user.id)


async def create_owner(session: AsyncSession, approved: bool = True) -> Owner:
    owner = Owner(
        id=uuid4(),
        email=f"{uuid4().hex}@example.com",
        password_hash=hash_password("Strong123"),
        representative_name=f"owner_{uuid4().hex[:8]}",
        phone_number="010-0000-0000",
        verification_status=(
            VerificationStatus.APPROVED if approved else VerificationStatus.PENDING
        ),
    )
    session.add(owner)
    await session.flush()
    return owner


def owner_token(owner: Owner) -> str:
    return issue_access_token(ActorType.OWNER, owner.id)


async def create_shop(
    session: AsyncSession,
    owner: Owner,
    visibility: Visibility = Visibility.ACTIVE,
    average_rating: Decimal | None = None,
    review_count: int = 0,
) -> Shop:
    shop = Shop(
        id=uuid4(),
        owner_id=owner.id,
        name=f"shop_{uuid4().hex[:8]}",
        address="Seoul",
        phone_number="02-0000-0000",
        visibility=visibility,
        average_rating=average_rating or Decimal("0.00"),
        review_count=review_count,
    )
    session.add(shop)
    await session.flush()
    return shop


async def create_designer(session: AsyncSession, shop: Shop) -> Designer:
    designer = Designer(
        id=uuid4(),
        shop_id=shop.id,
        name=f"designer_{uuid4().hex[:8]}",
        specialty_tags=[],
    )
    session.add(designer)
    await session.flush()
    return designer


async def create_design(
    session: AsyncSession,
    shop: Shop,
    visibility: Visibility = Visibility.ACTIVE,
    ai_analysis_status: AiAnalysisStatus = AiAnalysisStatus.DONE,
) -> Design:
    design = Design(
        id=uuid4(),
        shop_id=shop.id,
        title=f"design_{uuid4().hex[:8]}",
        base_price=30000,
        duration_minutes=60,
        visibility=visibility,
        ai_analysis_status=ai_analysis_status,
    )
    session.add(design)
    await session.flush()
    return design


async def create_reservation(
    session: AsyncSession,
    user: User,
    shop: Shop,
    design: Design,
    designer: Designer,
    status: ReservationStatus = ReservationStatus.COMPLETED,
) -> Reservation:
    start_at = datetime.now(UTC) + timedelta(days=1)
    reservation = Reservation(
        id=uuid4(),
        user_id=user.id,
        shop_id=shop.id,
        design_id=design.id,
        designer_id=designer.id,
        start_at=start_at,
        end_at=start_at + timedelta(minutes=60),
        status=status,
        total_price=30000,
        payment_method_snapshot=PaymentMethod.ON_SITE,
        idempotency_key=f"reservation-{uuid4()}",
    )
    session.add(reservation)
    await session.flush()
    return reservation


async def create_upload(
    session: AsyncSession,
    actor_type: ActorType,
    actor_id: object,
    target_type: UploadTargetType,
    object_key: str | None = None,
) -> UploadObject:
    key = object_key or f"{target_type.value}/{uuid4().hex}.jpg"
    upload = UploadObject(
        id=uuid4(),
        owner_actor_type=actor_type.value,
        owner_actor_id=actor_id,
        target_type=target_type,
        object_key=key,
        content_type="image/jpeg",
        byte_size=1024,
        original_url=f"https://cdn.test/{key}",
    )
    session.add(upload)
    await session.flush()
    return upload


async def create_snap(
    session: AsyncSession,
    user: User,
    tagged_shop_id: object | None = None,
    tagged_design_id: object | None = None,
) -> Snap:
    snap = Snap(
        id=uuid4(),
        user_id=user.id,
        body="snap body",
        tags=["simple"],
        tagged_shop_id=tagged_shop_id,
        tagged_design_id=tagged_design_id,
    )
    session.add(snap)
    await session.flush()
    return snap


async def create_comment(session: AsyncSession, snap: Snap, user: User) -> Comment:
    comment = Comment(
        id=uuid4(),
        snap_id=snap.id,
        parent_id=None,
        author_type=ActorType.USER,
        author_id=user.id,
        body="comment",
        depth=1,
    )
    session.add(comment)
    await session.flush()
    return comment


async def create_review(
    session: AsyncSession,
    reservation: Reservation,
    rating: int = 5,
) -> Review:
    review = Review(
        id=uuid4(),
        reservation_id=reservation.id,
        user_id=reservation.user_id,
        shop_id=reservation.shop_id,
        design_id=reservation.design_id,
        rating=rating,
        body="review",
    )
    session.add(review)
    await session.flush()
    return review
