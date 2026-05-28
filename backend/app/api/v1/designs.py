from datetime import UTC, datetime
from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_owner_id, db_session, optional_user_id
from app.api.v1._idempotency import (
    cached_response,
    request_hash_for,
    required_idempotency_key,
    response_body,
)
from app.models.enums import ActorType
from app.schemas.designs import (
    DesignCreate,
    DesignMe,
    DesignPublic,
    DesignReanalyzeQueued,
    DesignUpdate,
    DesignVisibilityUpdate,
)
from app.schemas.search import SearchQuery, SearchResult, SearchSort
from app.services import design_service, search_service
from app.utils.idempotency import with_idempotency
from app.utils.pagination import CursorParams

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(db_session)]
OwnerIdDep = Annotated[UUID, Depends(current_owner_id)]
IdempotencyKeyDep = Annotated[str, Depends(required_idempotency_key)]


def design_search_query(
    q: str | None = None,
    region: str | None = None,
    colors: Annotated[list[str] | None, Query()] = None,
    moods: Annotated[list[str] | None, Query()] = None,
    price_min: int | None = Query(default=None, ge=0),
    price_max: int | None = Query(default=None, ge=0),
    duration_max: int | None = Query(default=None, ge=1),
    sort: SearchSort | None = None,
    cursor: str | None = None,
    limit: int = Query(default=20, ge=1, le=50),
) -> SearchQuery:
    return SearchQuery(
        q=q,
        scope="designs",
        region=region,
        colors=colors,
        moods=moods,
        price_min=price_min,
        price_max=price_max,
        duration_max=duration_max,
        sort=sort,
        cursor=cursor,
        limit=limit,
    )


@router.post("/shops/me/designs", response_model=DesignMe, status_code=HTTPStatus.CREATED)
async def create_design(
    request: Request,
    payload: DesignCreate,
    owner_id: OwnerIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> DesignMe | Response:
    request_hash = await request_hash_for(request)
    response: DesignMe
    async with with_idempotency(
        session, ActorType.OWNER, owner_id, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        response = await design_service.create_design(session, owner_id, payload)
        idem.set_response(HTTPStatus.CREATED, response_body(response))
    await session.commit()
    return response


@router.get("/shops/me/designs", response_model=list[DesignMe])
async def list_my_designs(
    owner_id: OwnerIdDep,
    session: SessionDep,
    params: Annotated[CursorParams, Depends()],
) -> list[DesignMe]:
    return await design_service.list_my_designs(session, owner_id, params)


@router.get("/shops/me/designs/{design_id}", response_model=DesignMe)
async def get_my_design(
    design_id: UUID,
    owner_id: OwnerIdDep,
    session: SessionDep,
) -> DesignMe:
    return await design_service.get_my_design(session, owner_id, design_id)


@router.patch("/shops/me/designs/{design_id}", response_model=DesignMe)
async def update_design(
    request: Request,
    design_id: UUID,
    payload: DesignUpdate,
    owner_id: OwnerIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> DesignMe | Response:
    request_hash = await request_hash_for(request)
    response: DesignMe
    async with with_idempotency(
        session, ActorType.OWNER, owner_id, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        response = await design_service.update_design(session, owner_id, design_id, payload)
        idem.set_response(HTTPStatus.OK, response_body(response))
    await session.commit()
    return response


@router.delete("/shops/me/designs/{design_id}", status_code=HTTPStatus.NO_CONTENT)
async def delete_design(
    request: Request,
    design_id: UUID,
    owner_id: OwnerIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> Response:
    request_hash = await request_hash_for(request)
    async with with_idempotency(
        session, ActorType.OWNER, owner_id, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        await design_service.soft_delete_design(session, owner_id, design_id)
        idem.set_response(HTTPStatus.NO_CONTENT, None)
    await session.commit()
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.post(
    "/shops/me/designs/{design_id}/reanalyze",
    response_model=DesignReanalyzeQueued,
    status_code=HTTPStatus.ACCEPTED,
)
async def request_reanalyze(
    request: Request,
    design_id: UUID,
    owner_id: OwnerIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> DesignReanalyzeQueued | Response:
    request_hash = await request_hash_for(request)
    response: DesignReanalyzeQueued
    async with with_idempotency(
        session, ActorType.OWNER, owner_id, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        queued = await design_service.request_reanalyze(session, owner_id, design_id)
        response = DesignReanalyzeQueued(design_id=queued.id, queued_at=datetime.now(UTC))
        idem.set_response(HTTPStatus.ACCEPTED, response_body(response))
    await session.commit()
    return response


@router.post("/shops/me/designs/{design_id}/visibility", response_model=DesignMe)
async def change_visibility(
    request: Request,
    design_id: UUID,
    payload: DesignVisibilityUpdate,
    owner_id: OwnerIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> DesignMe | Response:
    request_hash = await request_hash_for(request)
    response: DesignMe
    async with with_idempotency(
        session, ActorType.OWNER, owner_id, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        response = await design_service.toggle_hide(
            session,
            owner_id,
            design_id,
            payload.visibility,
        )
        idem.set_response(HTTPStatus.OK, response_body(response))
    await session.commit()
    return response


@router.get("/designs/{design_id}", response_model=DesignPublic)
async def get_public_design(
    design_id: UUID,
    viewer_user_id: Annotated[UUID | None, Depends(optional_user_id)],
    session: SessionDep,
) -> DesignPublic:
    return await design_service.get_public_design(session, viewer_user_id, design_id)


@router.get("/designs", response_model=SearchResult)
async def search_designs(
    query: Annotated[SearchQuery, Depends(design_search_query)],
    viewer_user_id: Annotated[UUID | None, Depends(optional_user_id)],
    session: SessionDep,
) -> SearchResult:
    return await search_service.search_designs(session, viewer_user_id, query)
