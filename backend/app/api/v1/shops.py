from decimal import Decimal, InvalidOperation
from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_owner_id, db_session
from app.api.errors import AppError
from app.api.v1._idempotency import (
    cached_response,
    request_hash_for,
    required_idempotency_key,
    response_body,
)
from app.models.enums import ActorType
from app.schemas.shops import (
    BusinessHoursSet,
    ShopCreate,
    ShopImageCreate,
    ShopImagePublic,
    ShopMe,
    ShopPublic,
    ShopUpdate,
)
from app.services import shop_service
from app.utils.idempotency import with_idempotency

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(db_session)]
OwnerIdDep = Annotated[UUID, Depends(current_owner_id)]
IdempotencyKeyDep = Annotated[str, Depends(required_idempotency_key)]


@router.post(
    "/shops/me",
    response_model=ShopMe,
    status_code=HTTPStatus.CREATED,
    summary="내 샵 생성",
)
async def create_my_shop(
    request: Request,
    payload: ShopCreate,
    owner_id: OwnerIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> ShopMe | Response:
    request_hash = await request_hash_for(request)
    response: ShopMe
    async with with_idempotency(
        session, ActorType.OWNER, owner_id, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        shop = await shop_service.create_shop(session, owner_id, payload)
        response = ShopMe.from_shop(shop, shop.owner.verification_status)
        idem.set_response(HTTPStatus.CREATED, response_body(response))
    await session.commit()
    return response


@router.get(
    "/shops/me",
    response_model=ShopMe,
    summary="내 샵 조회",
)
async def get_my_shop(owner_id: OwnerIdDep, session: SessionDep) -> ShopMe:
    shop = await shop_service.get_my_shop(session, owner_id)
    if shop is None:
        raise AppError("SHOP_NOT_FOUND", "샵을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)
    return ShopMe.from_shop(shop, shop.owner.verification_status)


@router.patch(
    "/shops/me",
    response_model=ShopMe,
    summary="내 샵 수정",
)
async def update_my_shop(
    request: Request,
    payload: ShopUpdate,
    owner_id: OwnerIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> ShopMe | Response:
    request_hash = await request_hash_for(request)
    response: ShopMe
    async with with_idempotency(
        session, ActorType.OWNER, owner_id, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        shop = await shop_service.update_shop(session, owner_id, payload)
        response = ShopMe.from_shop(shop, shop.owner.verification_status)
        idem.set_response(HTTPStatus.OK, response_body(response))
    await session.commit()
    return response


@router.put(
    "/shops/me/business-hours",
    status_code=HTTPStatus.NO_CONTENT,
    summary="내 샵 영업시간 설정",
)
async def set_my_shop_business_hours(
    request: Request,
    payload: BusinessHoursSet,
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
        await shop_service.set_business_hours(session, owner_id, payload.entries)
        idem.set_response(HTTPStatus.NO_CONTENT, None)
    await session.commit()
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.post(
    "/shops/me/images",
    response_model=ShopImagePublic,
    status_code=HTTPStatus.CREATED,
    summary="내 샵 이미지 추가",
)
async def add_my_shop_image(
    request: Request,
    payload: ShopImageCreate,
    owner_id: OwnerIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> ShopImagePublic | Response:
    request_hash = await request_hash_for(request)
    response: ShopImagePublic
    async with with_idempotency(
        session, ActorType.OWNER, owner_id, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        image = await shop_service.add_shop_image(session, owner_id, payload)
        response = ShopImagePublic.model_validate(image)
        idem.set_response(HTTPStatus.CREATED, response_body(response))
    await session.commit()
    return response


@router.delete(
    "/shops/me/images/{image_id}",
    status_code=HTTPStatus.NO_CONTENT,
    summary="내 샵 이미지 삭제",
)
async def delete_my_shop_image(
    request: Request,
    image_id: UUID,
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
        await shop_service.delete_shop_image(session, owner_id, image_id)
        idem.set_response(HTTPStatus.NO_CONTENT, None)
    await session.commit()
    return Response(status_code=HTTPStatus.NO_CONTENT)


def _parse_bbox(bbox: str | None) -> tuple[Decimal, Decimal, Decimal, Decimal] | None:
    if bbox is None:
        return None
    parts = bbox.split(",")
    if len(parts) != 4:
        raise AppError(
            "INVALID_BBOX",
            "bbox는 'minLng,minLat,maxLng,maxLat' 형식이어야 합니다.",
            HTTPStatus.BAD_REQUEST,
        )
    try:
        min_lng, min_lat, max_lng, max_lat = (Decimal(p.strip()) for p in parts)
    except (InvalidOperation, ValueError) as exc:
        raise AppError(
            "INVALID_BBOX",
            "bbox 좌표를 해석할 수 없습니다.",
            HTTPStatus.BAD_REQUEST,
        ) from exc
    if min_lng > max_lng or min_lat > max_lat:
        raise AppError(
            "INVALID_BBOX",
            "bbox의 최소 좌표는 최대 좌표보다 작아야 합니다.",
            HTTPStatus.BAD_REQUEST,
        )
    return min_lng, min_lat, max_lng, max_lat


@router.get(
    "/shops",
    response_model=list[ShopPublic],
    summary="공개 샵 목록 조회",
)
async def list_public_shops(
    session: SessionDep,
    bbox: Annotated[str | None, Query()] = None,
    location_tag: Annotated[str | None, Query()] = None,
) -> list[ShopPublic]:
    shops = await shop_service.list_public_shops(
        session,
        bbox=_parse_bbox(bbox),
        location_tag=location_tag,
    )
    return [ShopPublic.from_shop(shop) for shop in shops]


@router.get(
    "/shops/{shop_id}",
    response_model=ShopPublic,
    summary="공개 샵 상세 조회",
)
async def get_public_shop(shop_id: UUID, session: SessionDep) -> ShopPublic:
    shop = await shop_service.get_public_shop(session, shop_id)
    return ShopPublic.from_shop(shop)
