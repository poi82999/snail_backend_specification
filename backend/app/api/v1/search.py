from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session, optional_user_id
from app.schemas.search import SearchQuery, SearchResult, SearchScope, SearchSort
from app.services import search_service

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(db_session)]


def search_query(
    q: str | None = None,
    scope: SearchScope = "designs",
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
        scope=scope,
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


@router.get("/search", response_model=SearchResult)
async def search(
    query: Annotated[SearchQuery, Depends(search_query)],
    viewer_user_id: Annotated[UUID | None, Depends(optional_user_id)],
    session: SessionDep,
) -> SearchResult:
    return await search_service.search(session, viewer_user_id, query)
