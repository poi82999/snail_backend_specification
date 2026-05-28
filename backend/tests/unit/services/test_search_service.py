from uuid import uuid4

import pytest
from app.api.errors import AppError
from app.core.security import hash_password
from app.models.accounts import Owner, User
from app.models.community import FavoriteDesign
from app.models.design import Design
from app.models.enums import AiAnalysisStatus, VerificationStatus, Visibility
from app.models.shop import Shop
from app.schemas.search import SearchQuery
from app.services import search_service
from sqlalchemy.ext.asyncio import AsyncSession


async def _owner(db_session: AsyncSession, *, approved: bool = True) -> Owner:
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


async def _shop(db_session: AsyncSession, owner: Owner, *, region: str = "강남") -> Shop:
    shop = Shop(
        id=uuid4(),
        owner_id=owner.id,
        name=f"샵 {uuid4().hex[:6]}",
        address="서울시 강남구",
        region=region,
        phone_number="02-0000-0000",
        visibility=Visibility.ACTIVE,
    )
    db_session.add(shop)
    await db_session.flush()
    return shop


async def _design(
    db_session: AsyncSession,
    shop: Shop,
    *,
    title: str = "핑크 프렌치 네일",
    ai_tags: list[str] | None = None,
    color_palette: list[str] | None = None,
    visibility: Visibility = Visibility.ACTIVE,
    ai_status: AiAnalysisStatus = AiAnalysisStatus.DONE,
    base_price: int = 30000,
) -> Design:
    design = Design(
        id=uuid4(),
        shop_id=shop.id,
        title=title,
        base_price=base_price,
        duration_minutes=60,
        visibility=visibility,
        ai_analysis_status=ai_status,
        ai_tags=ai_tags or [],
        color_palette=color_palette or [],
    )
    db_session.add(design)
    await db_session.flush()
    return design


async def _favorite(db_session: AsyncSession, design: Design, count: int) -> None:
    for _ in range(count):
        user = User(
            id=uuid4(),
            apple_sub=f"apple-{uuid4().hex}",
            email=f"{uuid4().hex}@example.com",
            nickname=f"user_{uuid4().hex[:10]}",
        )
        db_session.add(user)
        await db_session.flush()
        db_session.add(FavoriteDesign(id=uuid4(), user_id=user.id, design_id=design.id))
    await db_session.flush()


@pytest.mark.asyncio
async def test_search_designs_scores_ai_tag_match(db_session: AsyncSession) -> None:
    owner = await _owner(db_session)
    shop = await _shop(db_session, owner)
    await _design(db_session, shop, ai_tags=["핑크", "러블리"], color_palette=["핑크"])

    result = await search_service.search_designs(
        db_session,
        None,
        SearchQuery(q="핑크"),
    )

    assert result.items
    assert result.items[0].score is not None
    assert result.items[0].score > 0


@pytest.mark.asyncio
async def test_search_designs_excludes_guard_violations(db_session: AsyncSession) -> None:
    owner = await _owner(db_session)
    shop = await _shop(db_session, owner)
    visible = await _design(db_session, shop, title="보이는 디자인", ai_tags=["핑크"])
    hidden = await _design(
        db_session,
        shop,
        title="숨긴 디자인",
        ai_tags=["핑크"],
        visibility=Visibility.HIDDEN,
    )

    result = await search_service.search_designs(
        db_session,
        None,
        SearchQuery(q="핑크"),
    )

    ids = {item.id for item in result.items}
    assert visible.id in ids
    assert hidden.id not in ids


@pytest.mark.asyncio
async def test_search_designs_sorts_by_popular(db_session: AsyncSession) -> None:
    owner = await _owner(db_session)
    shop = await _shop(db_session, owner)
    less_popular = await _design(db_session, shop, title="인기 낮음")
    more_popular = await _design(db_session, shop, title="인기 높음")
    await _favorite(db_session, less_popular, 1)
    await _favorite(db_session, more_popular, 3)

    result = await search_service.search_designs(
        db_session,
        None,
        SearchQuery(sort="popular"),
    )

    assert [item.id for item in result.items[:2]] == [more_popular.id, less_popular.id]


@pytest.mark.asyncio
async def test_search_designs_returns_recommendations_for_empty_result(
    db_session: AsyncSession,
) -> None:
    owner = await _owner(db_session)
    shop = await _shop(db_session, owner, region="홍대")
    recommended = await _design(db_session, shop, title="추천 디자인", ai_tags=["핑크"])

    result = await search_service.search_designs(
        db_session,
        None,
        SearchQuery(q="매칭없음", region="홍대"),
    )

    assert result.items == []
    assert [item.id for item in result.recommendations] == [recommended.id]


@pytest.mark.asyncio
async def test_search_designs_rejects_distance_sort(db_session: AsyncSession) -> None:
    with pytest.raises(AppError) as exc_info:
        await search_service.search_designs(
            db_session,
            None,
            SearchQuery(sort="distance"),
        )

    assert exc_info.value.code == "DISTANCE_SORT_NOT_SUPPORTED"
