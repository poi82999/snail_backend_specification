from __future__ import annotations

import pytest
from app.models.enums import AiAnalysisStatus, Visibility
from httpx import AsyncClient

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
async def test_korean_natural_language_search_respects_public_exposure_guards(
    api_client: AsyncClient,
    e2e_factory,
) -> None:
    owner, _ = await e2e_factory.create_owner()
    shop = await e2e_factory.create_shop(owner, name="검색 노출 샵", visibility=Visibility.ACTIVE)
    designer = await e2e_factory.create_designer(shop)
    expected = await e2e_factory.create_design(
        shop,
        designer,
        title="여리여리 핑크 네일",
        ai_tags=["여리여리", "핑크"],
        color_palette=["핑크"],
    )

    pending = await e2e_factory.create_design(
        shop,
        designer,
        title="여리여리 핑크 네일 분석 대기",
        ai_status=AiAnalysisStatus.PENDING,
        ai_tags=[],
        color_palette=[],
    )
    hidden = await e2e_factory.create_design(
        shop,
        designer,
        title="숨겨진 여리여리 핑크 네일",
        visibility=Visibility.HIDDEN,
        ai_tags=["여리여리", "핑크"],
        color_palette=["핑크"],
    )

    unapproved_owner, _ = await e2e_factory.create_owner(approved=False)
    unapproved_shop = await e2e_factory.create_shop(
        unapproved_owner,
        name="미승인 샵",
        visibility=Visibility.ACTIVE,
    )
    unapproved_designer = await e2e_factory.create_designer(unapproved_shop)
    unapproved_design = await e2e_factory.create_design(
        unapproved_shop,
        unapproved_designer,
        title="미승인 여리여리 핑크 네일",
        ai_tags=["여리여리", "핑크"],
        color_palette=["핑크"],
    )

    draft_shop_owner, _ = await e2e_factory.create_owner()
    draft_shop = await e2e_factory.create_shop(
        draft_shop_owner,
        name="비공개 샵",
        visibility=Visibility.DRAFT,
    )
    draft_shop_designer = await e2e_factory.create_designer(draft_shop)
    draft_shop_design = await e2e_factory.create_design(
        draft_shop,
        draft_shop_designer,
        title="비공개 샵 여리여리 핑크 네일",
        ai_tags=["여리여리", "핑크"],
        color_palette=["핑크"],
    )

    response = await api_client.get(
        "/api/v1/search",
        params={"q": "여리여리한 핑크 네일", "scope": "designs"},
    )
    assert response.status_code == 200, response.text
    ids = [item["id"] for item in response.json()["items"]]

    assert str(expected.id) in ids
    assert str(pending.id) not in ids
    assert str(hidden.id) not in ids
    assert str(unapproved_design.id) not in ids
    assert str(draft_shop_design.id) not in ids
