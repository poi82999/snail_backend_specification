"""PostgreSQL 기반 디자인/샵/리뷰 검색 서비스."""

from __future__ import annotations

from http import HTTPStatus
from typing import Any, cast
from uuid import UUID

from sqlalchemy import case, desc, func, literal, or_, select, tuple_
from sqlalchemy.dialects.postgresql import array as pg_array
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.errors import AppError
from app.models.accounts import Owner
from app.models.community import FavoriteDesign, Review
from app.models.design import Design
from app.models.enums import AiAnalysisStatus, VerificationStatus, Visibility
from app.models.shop import Shop
from app.schemas.search import SearchQuery, SearchResult
from app.schemas.shops import ShopPublic
from app.services import design_service, review_service
from app.utils.pagination import decode_cursor, encode_cursor

SEARCH_SYNONYMS = {
    "여리여리한": ["러블리", "내추럴", "심플"],
    "여리여리": ["러블리", "내추럴", "심플"],
    "프랜치": ["프렌치"],
    "불란서": ["프렌치"],
}
STOPWORDS = {"네일", "아트", "디자인", "샵"}


def _array_literal(values: list[str]) -> Any:
    return pg_array(values)  # type: ignore[no-untyped-call]


def _normalized_text(value: str | None) -> str:
    return " ".join((value or "").strip().split())


def _query_tokens(value: str | None) -> list[str]:
    normalized = _normalized_text(value)
    tokens: list[str] = []
    for raw_token in normalized.replace(",", " ").split():
        token = raw_token.strip().lower()
        if not token or token in STOPWORDS:
            continue
        tokens.append(token)
        tokens.extend(SEARCH_SYNONYMS.get(token, []))
    return list(dict.fromkeys(tokens))


def _expanded_query(value: str | None) -> str:
    normalized = _normalized_text(value)
    tokens = _query_tokens(normalized)
    if not tokens:
        return normalized
    return " ".join(tokens)


def _public_design_filters() -> tuple[Any, ...]:
    return (
        Design.deleted_at.is_(None),
        Design.visibility == Visibility.ACTIVE,
        Design.ai_analysis_status == AiAnalysisStatus.DONE,
        Shop.visibility == Visibility.ACTIVE,
        Owner.verification_status == VerificationStatus.APPROVED,
        Owner.is_active.is_(True),
    )


def _apply_design_filters(statement: Any, query: SearchQuery) -> Any:
    if query.region is not None:
        statement = statement.where(Shop.region == query.region)
    if query.colors:
        statement = statement.where(Design.color_palette.op("@>")(_array_literal(query.colors)))
    if query.moods:
        statement = statement.where(Design.ai_tags.op("@>")(_array_literal(query.moods)))
    if query.price_min is not None:
        statement = statement.where(Design.base_price >= query.price_min)
    if query.price_max is not None:
        statement = statement.where(Design.base_price <= query.price_max)
    if query.duration_max is not None:
        statement = statement.where(Design.duration_minutes <= query.duration_max)
    return statement


def _apply_created_cursor(statement: Any, cursor: str | None) -> Any:
    if cursor is None:
        return statement
    cursor_created_at, cursor_id = decode_cursor(cursor)
    return statement.where(
        tuple_(Design.created_at, Design.id)
        < tuple_(literal(cursor_created_at), literal(cursor_id))
    )


def _score_expression(query_text: str, tokens: list[str]) -> Any:
    token_array: Any = _array_literal(tokens)
    tags_match = or_(
        Design.ai_tags.op("&&")(token_array),
        Design.owner_tags.op("&&")(token_array),
    )
    tags_score = case((tags_match, 1.0), else_=0.0)
    trgm_score = func.greatest(
        func.similarity(Design.title, query_text),
        func.similarity(func.coalesce(Design.description, ""), query_text),
    )
    # TODO(A6): OpenAI embedding이 준비되면 query embedding과 designs.embedding 코사인 거리 점수 추가.
    return (0.5 * tags_score) + (0.5 * trgm_score)


def _favorite_counts_subquery() -> Any:
    return (
        select(FavoriteDesign.design_id, func.count(FavoriteDesign.id).label("favorite_count"))
        .group_by(FavoriteDesign.design_id)
        .subquery()
    )


def _ratings_subquery() -> Any:
    return (
        select(Review.design_id, func.avg(Review.rating).label("average_rating"))
        .where(Review.deleted_at.is_(None))
        .group_by(Review.design_id)
        .subquery()
    )


async def _recommendations(
    session: AsyncSession,
    viewer_user_id: UUID | None,
    region: str | None,
) -> list[Any]:
    statement = (
        select(Design.id)
        .join(Shop, Shop.id == Design.shop_id)
        .join(Owner, Owner.id == Shop.owner_id)
        .where(*_public_design_filters())
        .order_by(Design.created_at.desc(), Design.id.desc())
        .limit(5)
    )
    if region is not None:
        statement = statement.where(Shop.region == region)
    design_ids = list((await session.scalars(statement)).all())
    return await design_service.public_design_rows(session, viewer_user_id, design_ids)


async def search_designs(
    session: AsyncSession,
    viewer_user_id: UUID | None,
    query: SearchQuery,
) -> SearchResult:
    if query.sort == "distance":
        raise AppError(
            "DISTANCE_SORT_NOT_SUPPORTED",
            "거리 정렬은 아직 지원하지 않습니다.",
            HTTPStatus.BAD_REQUEST,
        )

    favorite_counts = _favorite_counts_subquery()
    ratings = _ratings_subquery()
    score: Any = literal(None)
    statement = (
        select(Design.id, score.label("score"), Design.created_at)
        .join(Shop, Shop.id == Design.shop_id)
        .join(Owner, Owner.id == Shop.owner_id)
        .outerjoin(favorite_counts, favorite_counts.c.design_id == Design.id)
        .outerjoin(ratings, ratings.c.design_id == Design.id)
        .where(*_public_design_filters())
    )
    statement = _apply_design_filters(statement, query)
    statement = _apply_created_cursor(statement, query.cursor)

    q_text = _expanded_query(query.q)
    tokens = _query_tokens(query.q)
    if q_text and tokens:
        score = _score_expression(q_text, tokens)
        statement = statement.with_only_columns(Design.id, score.label("score"), Design.created_at)
        statement = statement.where(score > 0)
        statement = statement.order_by(desc("score"), Design.created_at.desc(), Design.id.desc())
    else:
        sort = query.sort or "popular"
        if sort == "latest":
            statement = statement.order_by(Design.created_at.desc(), Design.id.desc())
        elif sort == "price_asc":
            statement = statement.order_by(Design.base_price.asc(), Design.created_at.desc())
        elif sort == "price_desc":
            statement = statement.order_by(Design.base_price.desc(), Design.created_at.desc())
        elif sort == "rating":
            statement = statement.order_by(
                desc(func.coalesce(ratings.c.average_rating, 0)),
                Design.created_at.desc(),
                Design.id.desc(),
            )
        else:
            statement = statement.order_by(
                desc(func.coalesce(favorite_counts.c.favorite_count, 0)),
                Design.created_at.desc(),
                Design.id.desc(),
            )

    rows = (await session.execute(statement.limit(query.limit + 1))).all()
    page_rows = rows[: query.limit]
    design_ids = [cast(UUID, row[0]) for row in page_rows]
    scores = {
        cast(UUID, row[0]): (float(row[1]) if row[1] is not None else None) for row in page_rows
    }
    items = await design_service.public_design_rows(session, viewer_user_id, design_ids, scores)
    next_cursor = None
    if len(rows) > query.limit and page_rows:
        last_row = page_rows[-1]
        next_cursor = encode_cursor(cast(Any, last_row[2]), cast(UUID, last_row[0]))
    recommendations = []
    if not items:
        recommendations = await _recommendations(session, viewer_user_id, query.region)
    return SearchResult(items=items, next_cursor=next_cursor, recommendations=recommendations)


async def search_shops(
    session: AsyncSession,
    query: SearchQuery,
) -> SearchResult:
    if query.sort == "distance":
        raise AppError(
            "DISTANCE_SORT_NOT_SUPPORTED",
            "거리 정렬은 아직 지원하지 않습니다.",
            HTTPStatus.BAD_REQUEST,
        )
    q_text = _expanded_query(query.q)
    statement = (
        select(Shop)
        .join(Owner, Owner.id == Shop.owner_id)
        .where(
            Shop.visibility == Visibility.ACTIVE,
            Owner.verification_status == VerificationStatus.APPROVED,
            Owner.is_active.is_(True),
        )
        .options(selectinload(Shop.images), selectinload(Shop.business_hours))
    )
    if query.region is not None:
        statement = statement.where(Shop.region == query.region)
    if q_text:
        statement = statement.where(func.similarity(Shop.name, q_text) > 0.1)
        statement = statement.order_by(desc(func.similarity(Shop.name, q_text)))
    else:
        statement = statement.order_by(Shop.created_at.desc(), Shop.id.desc())
    if query.cursor is not None:
        cursor_created_at, cursor_id = decode_cursor(query.cursor)
        statement = statement.where(
            tuple_(Shop.created_at, Shop.id)
            < tuple_(literal(cursor_created_at), literal(cursor_id))
        )

    shops = list((await session.scalars(statement.limit(query.limit + 1))).all())
    items = [ShopPublic.from_shop(shop) for shop in shops[: query.limit]]
    next_cursor = None
    if len(shops) > query.limit and items:
        last_shop = shops[query.limit - 1]
        next_cursor = encode_cursor(last_shop.created_at, last_shop.id)
    return SearchResult(items=items, next_cursor=next_cursor)


async def search_reviews(
    session: AsyncSession,
    query: SearchQuery,
) -> SearchResult:
    q_text = _expanded_query(query.q)
    statement = select(Review.id, Review.created_at).where(Review.deleted_at.is_(None))
    if q_text:
        statement = statement.where(func.similarity(func.coalesce(Review.body, ""), q_text) > 0.1)
        statement = statement.order_by(
            desc(func.similarity(func.coalesce(Review.body, ""), q_text))
        )
    else:
        statement = statement.order_by(Review.created_at.desc(), Review.id.desc())
    if query.cursor is not None:
        cursor_created_at, cursor_id = decode_cursor(query.cursor)
        statement = statement.where(
            tuple_(Review.created_at, Review.id)
            < tuple_(literal(cursor_created_at), literal(cursor_id))
        )
    rows = (await session.execute(statement.limit(query.limit + 1))).all()
    review_ids = [cast(UUID, row[0]) for row in rows[: query.limit]]
    items = await review_service.get_public_reviews(session, review_ids)
    next_cursor = None
    if len(rows) > query.limit and review_ids:
        last_row = rows[query.limit - 1]
        next_cursor = encode_cursor(cast(Any, last_row[1]), cast(UUID, last_row[0]))
    return SearchResult(items=items, next_cursor=next_cursor)


async def search(
    session: AsyncSession,
    viewer_user_id: UUID | None,
    query: SearchQuery,
) -> SearchResult:
    if query.scope == "shops":
        return await search_shops(session, query)
    if query.scope == "reviews":
        return await search_reviews(session, query)
    return await search_designs(session, viewer_user_id, query)
