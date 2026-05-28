from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
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


@router.post("/shops/me", response_model=ShopMe, status_code=HTTPStatus.CREATED)
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


@router.get("/shops/me", response_model=ShopMe)
async def get_my_shop(owner_id: OwnerIdDep, session: SessionDep) -> ShopMe:
    shop = await shop_service.get_my_shop(session, owner_id)
    if shop is None:
        raise AppError("SHOP_NOT_FOUND", "샵을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)
    return ShopMe.from_shop(shop, shop.owner.verification_status)


@router.patch("/shops/me", response_model=ShopMe)
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


@router.put("/shops/me/business-hours", status_code=HTTPStatus.NO_CONTENT)
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


@router.post("/shops/me/images", response_model=ShopImagePublic, status_code=HTTPStatus.CREATED)
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


@router.delete("/shops/me/images/{image_id}", status_code=HTTPStatus.NO_CONTENT)
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


@router.get("/shops/{shop_id}", response_model=ShopPublic)
async def get_public_shop(shop_id: UUID, session: SessionDep) -> ShopPublic:
    shop = await shop_service.get_public_shop(session, shop_id)
    return ShopPublic.from_shop(shop)
