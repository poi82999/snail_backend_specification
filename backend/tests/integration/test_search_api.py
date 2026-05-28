from uuid import uuid4

import pytest
from app.core.security import hash_password
from app.models.accounts import Owner
from app.models.design import Design
from app.models.enums import AiAnalysisStatus, VerificationStatus, Visibility
from app.models.shop import Shop
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.community_factories import (
    create_design as create_design_factory,
)
from tests.community_factories import (
    create_designer,
    create_owner,
    create_reservation,
    create_review,
    create_user,
)
from tests.community_factories import (
    create_shop as create_shop_factory,
)


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


async def _shop(db_session: AsyncSession, *, region: str = "강남") -> Shop:
    owner = await _owner(db_session)
    shop = Shop(
        id=uuid4(),
        owner_id=owner.id,
        name=f"{region} 네일샵",
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
    title: str,
    ai_tags: list[str] | None = None,
    color_palette: list[str] | None = None,
    base_price: int = 40000,
) -> Design:
    design = Design(
        id=uuid4(),
        shop_id=shop.id,
        title=title,
        base_price=base_price,
        duration_minutes=60,
        visibility=Visibility.ACTIVE,
        ai_analysis_status=AiAnalysisStatus.DONE,
        ai_tags=ai_tags or [],
        color_palette=color_palette or [],
    )
    db_session.add(design)
    await db_session.flush()
    return design


@pytest.mark.asyncio
async def test_search_natural_language_matches_korean_ai_tags(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    shop = await _shop(db_session)
    expected = await _design(
        db_session,
        shop,
        title="여리여리 핑크 네일",
        ai_tags=["러블리", "핑크", "내추럴"],
        color_palette=["핑크"],
    )
    await _design(db_session, shop, title="블랙 네일", ai_tags=["시크"], color_palette=["블랙"])

    response = await api_client.get("/api/v1/search", params={"q": "여리여리한 핑크"})

    assert response.status_code == 200
    assert response.json()["items"][0]["id"] == str(expected.id)


@pytest.mark.asyncio
async def test_search_typo_matches_trgm(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    shop = await _shop(db_session)
    expected = await _design(db_session, shop, title="프렌치 네일", ai_tags=[])

    response = await api_client.get("/api/v1/search", params={"q": "프랜치"})

    assert response.status_code == 200
    assert response.json()["items"][0]["id"] == str(expected.id)


@pytest.mark.asyncio
async def test_search_combines_color_and_price_filters(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    shop = await _shop(db_session)
    expected = await _design(
        db_session,
        shop,
        title="핑크 네일",
        ai_tags=["핑크"],
        color_palette=["핑크"],
        base_price=40000,
    )
    expensive = await _design(
        db_session,
        shop,
        title="비싼 핑크",
        ai_tags=["핑크"],
        color_palette=["핑크"],
        base_price=70000,
    )
    blue = await _design(
        db_session,
        shop,
        title="블루 네일",
        ai_tags=["블루"],
        color_palette=["블루"],
        base_price=30000,
    )

    response = await api_client.get(
        "/api/v1/search",
        params={"colors": "핑크", "price_max": "50000"},
    )

    assert response.status_code == 200
    ids = [item["id"] for item in response.json()["items"]]
    assert str(expected.id) in ids
    assert str(expensive.id) not in ids
    assert str(blue.id) not in ids


@pytest.mark.asyncio
async def test_search_empty_result_returns_recommendations(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    shop = await _shop(db_session, region="홍대")
    recommended = await _design(
        db_session,
        shop,
        title="추천 핑크",
        ai_tags=["핑크"],
        color_palette=["핑크"],
    )

    response = await api_client.get(
        "/api/v1/search",
        params={"q": "매칭없음", "region": "홍대"},
    )

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["recommendations"][0]["id"] == str(recommended.id)


@pytest.mark.asyncio
async def test_search_reviews_returns_batch_loaded_public_reviews(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user(db_session)
    owner = await create_owner(db_session)
    shop = await create_shop_factory(db_session, owner)
    designer = await create_designer(db_session, shop)
    design = await create_design_factory(db_session, shop)
    expected_ids = set()

    for rating in (5, 4, 3):
        reservation = await create_reservation(db_session, user, shop, design, designer)
        review = await create_review(db_session, reservation, rating=rating)
        review.body = f"review batch {rating}"
        expected_ids.add(str(review.id))
    await db_session.flush()

    response = await api_client.get(
        "/api/v1/search",
        params={"scope": "reviews", "limit": 3},
    )

    assert response.status_code == 200
    body = response.json()
    assert {item["id"] for item in body["items"]} == expected_ids
    assert all(item["author"]["id"] == str(user.id) for item in body["items"])
