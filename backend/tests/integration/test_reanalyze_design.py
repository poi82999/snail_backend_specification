from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from app.models.design import Design
from app.models.enums import AiAnalysisStatus
from app.services import design_service
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.community_factories import (
    auth_headers,
    create_design,
    create_owner,
    create_shop,
    owner_token,
)


@pytest.mark.asyncio
async def test_reanalyze_design_resets_status_and_enqueues_job(
    api_client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pool = SimpleNamespace(enqueue_job=AsyncMock())
    monkeypatch.setattr(design_service, "get_arq_pool", lambda: pool)
    owner = await create_owner(db_session)
    shop = await create_shop(db_session, owner)
    design = await create_design(
        db_session,
        shop,
        ai_analysis_status=AiAnalysisStatus.DONE,
    )

    response = await api_client.post(
        f"/api/v1/shops/me/designs/{design.id}/reanalyze",
        headers=auth_headers(owner_token(owner), f"reanalyze-{uuid4()}"),
    )

    assert response.status_code == 202, response.text
    body = response.json()
    assert body["design_id"] == str(design.id)
    assert datetime.fromisoformat(body["queued_at"]) is not None
    await db_session.refresh(design)
    assert design.ai_analysis_status == AiAnalysisStatus.PENDING
    pool.enqueue_job.assert_awaited_once_with("analyze_design", str(design.id))


@pytest.mark.asyncio
async def test_reanalyze_design_rejects_other_owner(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    owner = await create_owner(db_session)
    other_owner = await create_owner(db_session)
    shop = await create_shop(db_session, owner)
    design = await create_design(db_session, shop)

    response = await api_client.post(
        f"/api/v1/shops/me/designs/{design.id}/reanalyze",
        headers=auth_headers(owner_token(other_owner), f"reanalyze-forbidden-{uuid4()}"),
    )

    assert response.status_code == 403, response.text
    assert response.json()["error"]["code"] == "FORBIDDEN"
    persisted = await db_session.get(Design, design.id)
    assert persisted is not None
    assert persisted.ai_analysis_status == AiAnalysisStatus.DONE
