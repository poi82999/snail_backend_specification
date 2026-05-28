from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest
from app.core import database
from app.core.security import hash_password, issue_access_token
from app.models.accounts import Owner, User, UserDeviceToken
from app.models.design import Design, DesignDesigner, DesignImage
from app.models.enums import (
    ActorType,
    AiAnalysisStatus,
    PaymentMethod,
    UploadTargetType,
    VerificationStatus,
    Visibility,
)
from app.models.ops import UploadObject
from app.models.shop import Designer, DesignerSchedule, DesignerTimeOff, Shop, ShopBusinessHour
from app.services.notifications import router as notification_service
from sqlalchemy.ext.asyncio import AsyncSession

KST = ZoneInfo("Asia/Seoul")


@dataclass(slots=True)
class E2EReservationContext:
    user: User
    user_token: str
    owner: Owner
    owner_token: str
    shop: Shop
    designer: Designer
    design: Design
    target_date: date
    start_at: datetime


class FakeRedis:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def enqueue_job(self, name: str, delivery_id: str) -> None:
        self.calls.append((name, delivery_id))


class _SessionContext:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def __aenter__(self) -> AsyncSession:
        return self._session

    async def __aexit__(self, *args: object) -> bool:
        return False


class _SessionFactory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def __call__(self) -> _SessionContext:
        return _SessionContext(self._session)


@pytest.fixture
def worker_sessionmaker(db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database, "_sessionmaker", _SessionFactory(db_session))


@pytest.fixture
def notification_queue(monkeypatch: pytest.MonkeyPatch) -> FakeRedis:
    queue = FakeRedis()
    monkeypatch.setattr(notification_service, "get_arq_pool", lambda: queue)
    return queue


class E2EFactory:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def auth_headers(token: str, idempotency_key: str | None = None) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {token}"}
        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    @staticmethod
    def future_date(days: int = 7) -> date:
        return datetime.now(KST).date() + timedelta(days=days)

    @staticmethod
    def local_at(target_date: date, value: time) -> datetime:
        return datetime.combine(target_date, value).replace(tzinfo=KST).astimezone(UTC)

    async def create_upload(
        self,
        actor_type: ActorType,
        actor_id: UUID,
        target_type: UploadTargetType,
        *,
        object_key: str | None = None,
        original_url: str | None = None,
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
            original_url=original_url or f"https://cdn.test/{key}",
            uploaded_at=datetime.now(UTC),
        )
        self.session.add(upload)
        await self.session.flush()
        return upload

    async def create_user(
        self,
        *,
        nickname: str | None = None,
        with_device_token: bool = False,
    ) -> tuple[User, str]:
        user = User(
            id=uuid4(),
            apple_sub=f"apple-{uuid4().hex}",
            email=f"{uuid4().hex}@example.com",
            nickname=nickname or f"user_{uuid4().hex[:10]}",
            interest_tags=[],
        )
        self.session.add(user)
        await self.session.flush()
        if with_device_token:
            self.session.add(
                UserDeviceToken(
                    id=uuid4(),
                    user_id=user.id,
                    token=f"apns-{uuid4().hex}",
                    platform="ios",
                    is_active=True,
                    last_seen_at=datetime.now(UTC),
                )
            )
            await self.session.flush()
        return user, issue_access_token(ActorType.USER, user.id)

    async def create_owner(self, *, approved: bool = True) -> tuple[Owner, str]:
        owner = Owner(
            id=uuid4(),
            email=f"{uuid4().hex}@example.com",
            password_hash=hash_password("TestOwnerPassword1!"),
            representative_name="테스트 대표",
            phone_number="010-0000-0000",
            verification_status=(
                VerificationStatus.APPROVED if approved else VerificationStatus.PENDING
            ),
        )
        self.session.add(owner)
        await self.session.flush()
        return owner, issue_access_token(ActorType.OWNER, owner.id)

    async def create_shop(
        self,
        owner: Owner,
        *,
        name: str = "E2E 네일샵",
        region: str = "강남",
        visibility: Visibility = Visibility.ACTIVE,
        payment_method: PaymentMethod = PaymentMethod.ON_SITE,
        auto_accept: bool = False,
    ) -> Shop:
        bank_fields = (
            {
                "deposit_amount": 10000,
                "bank_name": "테스트은행",
                "bank_account_number": "123-456-7890",
                "bank_account_holder": owner.representative_name,
            }
            if payment_method == PaymentMethod.BANK_TRANSFER_GUIDE
            else {
                "deposit_amount": None,
                "bank_name": None,
                "bank_account_number": None,
                "bank_account_holder": None,
            }
        )
        shop = Shop(
            id=uuid4(),
            owner_id=owner.id,
            name=name,
            address="서울시 강남구 테헤란로",
            address_detail="2층",
            region=region,
            phone_number="02-0000-0000",
            introduction="E2E 테스트 샵",
            visibility=visibility,
            payment_method=payment_method,
            auto_accept=auto_accept,
            reservation_policy="예약 변경은 샵에 문의해주세요.",
            **bank_fields,
        )
        self.session.add(shop)
        await self.session.flush()
        return shop

    async def create_designer(self, shop: Shop, *, name: str = "지우") -> Designer:
        designer = Designer(
            id=uuid4(),
            shop_id=shop.id,
            name=name,
            position="시니어",
            career_years=5,
            specialty_tags=["핑크", "심플"],
            is_active=True,
        )
        self.session.add(designer)
        await self.session.flush()
        return designer

    async def set_open_slot(
        self,
        shop: Shop,
        designer: Designer,
        target_date: date,
        *,
        start: time = time(9, 0),
        end: time = time(18, 0),
    ) -> None:
        weekday = target_date.weekday()
        self.session.add_all(
            [
                ShopBusinessHour(
                    id=uuid4(),
                    shop_id=shop.id,
                    weekday=weekday,
                    open_time=start,
                    close_time=end,
                    is_closed=False,
                ),
                DesignerSchedule(
                    id=uuid4(),
                    designer_id=designer.id,
                    weekday=weekday,
                    start_time=start,
                    end_time=end,
                    is_day_off=False,
                ),
            ]
        )
        await self.session.flush()

    async def add_time_off(
        self,
        designer: Designer,
        target_date: date,
        *,
        start: time = time(15, 0),
        end: time = time(16, 0),
    ) -> None:
        self.session.add(
            DesignerTimeOff(
                id=uuid4(),
                designer_id=designer.id,
                off_date=target_date,
                start_time=start,
                end_time=end,
                reason="E2E 부분 휴무",
            )
        )
        await self.session.flush()

    async def create_design(
        self,
        shop: Shop,
        designer: Designer,
        *,
        title: str = "여리여리 핑크 네일",
        description: str = "투명하고 러블리한 핑크 네일",
        visibility: Visibility = Visibility.ACTIVE,
        ai_status: AiAnalysisStatus = AiAnalysisStatus.DONE,
        ai_tags: list[str] | None = None,
        color_palette: list[str] | None = None,
    ) -> Design:
        image_url = f"https://placehold.co/512x512?text=design+{uuid4().hex[:6]}"
        design = Design(
            id=uuid4(),
            shop_id=shop.id,
            title=title,
            description=description,
            base_price=45000,
            duration_minutes=60,
            thumbnail_url=image_url,
            visibility=visibility,
            ai_analysis_status=ai_status,
            owner_tags=["봄", "러블리"],
            ai_tags=ai_tags or ["여리여리", "핑크", "러블리"],
            color_palette=color_palette or ["핑크"],
            style_category="simple",
            nail_shape="round",
        )
        self.session.add(design)
        await self.session.flush()
        self.session.add_all(
            [
                DesignDesigner(design_id=design.id, designer_id=designer.id),
                DesignImage(
                    id=uuid4(),
                    design_id=design.id,
                    original_url=image_url,
                    processed_url=None,
                    sort_order=0,
                    is_thumbnail=True,
                ),
            ]
        )
        await self.session.flush()
        return design

    async def ready_reservation_context(
        self,
        *,
        payment_method: PaymentMethod = PaymentMethod.ON_SITE,
        auto_accept: bool = False,
        with_device_token: bool = False,
        days: int = 7,
    ) -> E2EReservationContext:
        user, user_token = await self.create_user(with_device_token=with_device_token)
        owner, owner_token = await self.create_owner()
        shop = await self.create_shop(
            owner,
            payment_method=payment_method,
            auto_accept=auto_accept,
        )
        designer = await self.create_designer(shop)
        design = await self.create_design(shop, designer)
        target_date = self.future_date(days)
        await self.set_open_slot(shop, designer, target_date)
        start_at = self.local_at(target_date, time(9, 0))
        return E2EReservationContext(
            user=user,
            user_token=user_token,
            owner=owner,
            owner_token=owner_token,
            shop=shop,
            designer=designer,
            design=design,
            target_date=target_date,
            start_at=start_at,
        )

    @staticmethod
    def reservation_payload(ctx: E2EReservationContext) -> dict[str, object]:
        return {
            "design_id": str(ctx.design.id),
            "designer_id": str(ctx.designer.id),
            "start_at": ctx.start_at.isoformat(),
            "user_request": "창가 자리면 좋겠습니다.",
        }


@pytest.fixture
def e2e_factory(db_session: AsyncSession) -> E2EFactory:
    return E2EFactory(db_session)
