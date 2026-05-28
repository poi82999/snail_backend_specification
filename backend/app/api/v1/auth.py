from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session
from app.api.v1._idempotency import (
    SYSTEM_ACTOR_ID,
    cached_response,
    request_hash_for,
    required_idempotency_key,
    response_body,
)
from app.models.enums import ActorType
from app.schemas.auth import (
    AppleSignInRequest,
    AppleSignInResponse,
    OwnerLoginRequest,
    OwnerSignupRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RefreshTokenRequest,
    TokenPair,
)
from app.schemas.owners import OwnerMe
from app.schemas.users import UserMe
from app.services import auth_service
from app.utils.idempotency import with_idempotency

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(db_session)]
IdempotencyKeyDep = Annotated[str, Depends(required_idempotency_key)]


def _client_host(request: Request) -> str | None:
    return request.client.host if request.client is not None else None


@router.post(
    "/apple",
    response_model=AppleSignInResponse,
    summary="애플 로그인",
)
async def apple_sign_in(
    request: Request,
    payload: AppleSignInRequest,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> AppleSignInResponse | Response:
    request_hash = await request_hash_for(request)
    response: AppleSignInResponse
    async with with_idempotency(
        session, ActorType.SYSTEM, SYSTEM_ACTOR_ID, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        user, tokens = await auth_service.apple_sign_in(
            session,
            payload.id_token,
            None,
            payload.accepted_terms_version,
            payload.accepted_privacy_version,
            _client_host(request),
            request.headers.get("User-Agent"),
        )
        response = AppleSignInResponse(tokens=tokens, user=UserMe.model_validate(user))
        idem.set_response(HTTPStatus.OK, response_body(response))
    await session.commit()
    return response


@router.post(
    "/owner/signup",
    response_model=OwnerMe,
    status_code=HTTPStatus.CREATED,
    summary="사장님 회원가입",
)
async def owner_signup(
    request: Request,
    payload: OwnerSignupRequest,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> OwnerMe | Response:
    request_hash = await request_hash_for(request)
    response: OwnerMe
    async with with_idempotency(
        session, ActorType.SYSTEM, SYSTEM_ACTOR_ID, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        owner = await auth_service.owner_signup(
            session,
            payload,
            _client_host(request),
            request.headers.get("User-Agent"),
        )
        response = OwnerMe.model_validate(owner)
        idem.set_response(HTTPStatus.CREATED, response_body(response))
    await session.commit()
    return response


@router.post(
    "/owner/login",
    response_model=TokenPair,
    summary="사장님 로그인",
)
async def owner_login(
    payload: OwnerLoginRequest,
    session: SessionDep,
) -> TokenPair:
    _, response = await auth_service.owner_login(session, payload)
    await session.commit()
    return response


@router.post(
    "/refresh",
    response_model=TokenPair,
    summary="토큰 갱신",
)
async def refresh_tokens(
    payload: RefreshTokenRequest,
    session: SessionDep,
) -> TokenPair:
    response = await auth_service.refresh_tokens(session, payload.refresh_token)
    await session.commit()
    return response


@router.post(
    "/password-reset",
    status_code=HTTPStatus.NO_CONTENT,
    summary="비밀번호 재설정 요청",
)
async def request_password_reset(
    request: Request,
    payload: PasswordResetRequest,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> Response:
    request_hash = await request_hash_for(request)
    async with with_idempotency(
        session, ActorType.SYSTEM, SYSTEM_ACTOR_ID, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        await auth_service.request_password_reset(session, payload.email)
        idem.set_response(HTTPStatus.NO_CONTENT, None)
    await session.commit()
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.post(
    "/password-reset/confirm",
    status_code=HTTPStatus.NO_CONTENT,
    summary="비밀번호 재설정 확정",
)
async def confirm_password_reset(
    request: Request,
    payload: PasswordResetConfirmRequest,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> Response:
    request_hash = await request_hash_for(request)
    async with with_idempotency(
        session, ActorType.SYSTEM, SYSTEM_ACTOR_ID, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        await auth_service.confirm_password_reset(session, payload.token, payload.new_password)
        idem.set_response(HTTPStatus.NO_CONTENT, None)
    await session.commit()
    return Response(status_code=HTTPStatus.NO_CONTENT)
