from http import HTTPStatus
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_owner_id, db_session
from app.api.errors import AppError, request_id_from
from app.api.v1._idempotency import (
    cached_response,
    request_hash_for,
    required_idempotency_key,
    response_body,
)
from app.models.enums import ActorType
from app.models.notification import OwnerNotification
from app.schemas.common import DataResponse, PageMeta
from app.schemas.notifications import (
    OwnerNotificationListResponse,
    OwnerNotificationPublic,
)
from app.services.notifications import owner_inbox
from app.utils.idempotency import with_idempotency
from app.utils.pagination import CursorParams

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(db_session)]
OwnerIdDep = Annotated[UUID, Depends(current_owner_id)]
IdempotencyKeyDep = Annotated[str, Depends(required_idempotency_key)]


def _notification_public(notification: OwnerNotification) -> OwnerNotificationPublic:
    return OwnerNotificationPublic(
        id=notification.id,
        type=notification.type,
        title=notification.title,
        body=notification.body,
        resource_type=notification.resource_type,
        resource_id=notification.resource_id,
        deeplink=notification.deeplink,
        metadata=notification.metadata_,
        read_at=notification.read_at,
        created_at=notification.created_at,
    )


async def _list_owner_notifications_response(
    request: Request,
    owner_id: UUID,
    session: AsyncSession,
    params: CursorParams,
    *,
    unread_only: bool,
) -> OwnerNotificationListResponse:
    notifications, next_cursor = await owner_inbox.list_inbox(
        session,
        owner_id,
        params,
        unread_only=unread_only,
    )
    return OwnerNotificationListResponse(
        data=[_notification_public(notification) for notification in notifications],
        page=PageMeta(next_cursor=next_cursor, has_next=next_cursor is not None),
        unread_count=await owner_inbox.unread_count(session, owner_id),
        request_id=request_id_from(request),
    )


@router.get(
    "/shops/me/notifications",
    response_model=OwnerNotificationListResponse,
    summary="샵 알림 목록 조회",
)
async def list_shop_notifications(
    request: Request,
    owner_id: OwnerIdDep,
    session: SessionDep,
    params: Annotated[CursorParams, Depends()],
    unread_only: bool = False,
) -> OwnerNotificationListResponse:
    return await _list_owner_notifications_response(
        request,
        owner_id,
        session,
        params,
        unread_only=unread_only,
    )


@router.get(
    "/owners/me/notifications",
    response_model=OwnerNotificationListResponse,
    summary="사장님 알림 목록 조회",
)
async def list_owner_notifications(
    request: Request,
    owner_id: OwnerIdDep,
    session: SessionDep,
    params: Annotated[CursorParams, Depends()],
    status: Literal["unread", "all"] = "unread",
) -> OwnerNotificationListResponse:
    return await _list_owner_notifications_response(
        request,
        owner_id,
        session,
        params,
        unread_only=status == "unread",
    )


async def _mark_notification_read_response(
    request: Request,
    notification_id: UUID,
    owner_id: UUID,
    idempotency_key: str,
    session: AsyncSession,
) -> DataResponse[OwnerNotificationPublic] | Response:
    request_hash = await request_hash_for(request)
    response: DataResponse[OwnerNotificationPublic]
    async with with_idempotency(
        session,
        ActorType.OWNER,
        owner_id,
        idempotency_key,
        request_hash,
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        notification = await owner_inbox.mark_read(session, owner_id, notification_id)
        if notification is None:
            raise AppError(
                "NOTIFICATION_NOT_FOUND", "알림을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND
            )
        response = DataResponse[OwnerNotificationPublic](
            data=_notification_public(notification),
            request_id=request_id_from(request),
        )
        idem.set_response(HTTPStatus.OK, response_body(response))
    await session.commit()
    return response


@router.patch(
    "/shops/me/notifications/{notification_id}/read",
    response_model=DataResponse[OwnerNotificationPublic],
    summary="샵 알림 읽음 처리",
)
async def mark_shop_notification_read(
    request: Request,
    notification_id: UUID,
    owner_id: OwnerIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> DataResponse[OwnerNotificationPublic] | Response:
    return await _mark_notification_read_response(
        request,
        notification_id,
        owner_id,
        idempotency_key,
        session,
    )


@router.post(
    "/owners/me/notifications/{notification_id}/read",
    response_model=DataResponse[OwnerNotificationPublic],
    summary="사장님 알림 읽음 처리",
)
async def mark_owner_notification_read(
    request: Request,
    notification_id: UUID,
    owner_id: OwnerIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> DataResponse[OwnerNotificationPublic] | Response:
    return await _mark_notification_read_response(
        request,
        notification_id,
        owner_id,
        idempotency_key,
        session,
    )


@router.post(
    "/owners/me/notifications/read-all",
    response_model=DataResponse[dict[str, int]],
    summary="사장님 알림 전체 읽음 처리",
)
async def mark_all_owner_notifications_read(
    request: Request,
    owner_id: OwnerIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> DataResponse[dict[str, int]] | Response:
    request_hash = await request_hash_for(request)
    response: DataResponse[dict[str, int]]
    async with with_idempotency(
        session,
        ActorType.OWNER,
        owner_id,
        idempotency_key,
        request_hash,
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        updated_count = await owner_inbox.mark_all_read(session, owner_id)
        response = DataResponse[dict[str, int]](
            data={"updated_count": updated_count},
            request_id=request_id_from(request),
        )
        idem.set_response(HTTPStatus.OK, response_body(response))
    await session.commit()
    return response
