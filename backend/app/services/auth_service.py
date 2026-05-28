import re
import secrets
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from http import HTTPStatus
from typing import cast
from uuid import UUID, uuid4

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import AppError
from app.core import security
from app.core.config import get_settings
from app.models.accounts import (
    Owner,
    PasswordResetToken,
    TermsAcceptance,
    User,
    UserOAuthIdentity,
)
from app.models.enums import ActorType
from app.schemas.auth import OwnerLoginRequest, OwnerSignupRequest, TokenPair

PASSWORD_POLICY = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$")
OWNER_LOCK_THRESHOLD = 5
OWNER_LOCK_MINUTES = 15
PASSWORD_RESET_EXPIRE_HOURS = 1

logger = structlog.get_logger()


def _now() -> datetime:
    return datetime.now(UTC)


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _validate_password_policy(password: str) -> None:
    if PASSWORD_POLICY.fullmatch(password) is None:
        raise AppError(
            "INVALID_PASSWORD_POLICY",
            "비밀번호는 8자 이상이며 대소문자와 숫자를 포함해야 합니다.",
            HTTPStatus.BAD_REQUEST,
        )


def _issue_token_pair(actor_type: ActorType, actor_id: UUID) -> TokenPair:
    settings = get_settings()
    now = _now()
    return TokenPair(
        access_token=security.issue_access_token(actor_type, actor_id),
        refresh_token=security.issue_refresh_token(actor_type, actor_id),
        access_expires_at=now + timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MIN),
        refresh_expires_at=now + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS),
    )


def _nickname_candidate(base: str, attempt: int) -> str:
    if attempt == 0:
        return base[:40]
    suffix = secrets.token_hex(2)
    base_len = max(1, 40 - len(suffix) - 1)
    return f"{base[:base_len]}_{suffix}"


async def _build_unique_nickname(session: AsyncSession, nickname_hint: str | None) -> str:
    base = (nickname_hint or "").strip() or f"user_{secrets.token_hex(3)}"
    for attempt in range(3):
        candidate = _nickname_candidate(base, attempt)
        existing = await session.scalar(select(User.id).where(User.nickname == candidate))
        if existing is None:
            return candidate
    raise AppError(
        "NICKNAME_TAKEN",
        "이미 사용 중인 닉네임입니다.",
        HTTPStatus.CONFLICT,
    )


async def _record_terms_acceptances(
    session: AsyncSession,
    actor_type: ActorType,
    actor_id: UUID,
    accepted_terms_version: str,
    accepted_privacy_version: str,
    ip_address: str | None,
    user_agent: str | None,
) -> None:
    accepted_at = _now()
    session.add_all(
        [
            TermsAcceptance(
                id=uuid4(),
                actor_type=actor_type.value,
                actor_id=actor_id,
                policy_type="terms_of_service",
                version=accepted_terms_version,
                accepted_at=accepted_at,
                ip_address=ip_address,
                user_agent=user_agent,
            ),
            TermsAcceptance(
                id=uuid4(),
                actor_type=actor_type.value,
                actor_id=actor_id,
                policy_type="privacy_policy",
                version=accepted_privacy_version,
                accepted_at=accepted_at,
                ip_address=ip_address,
                user_agent=user_agent,
            ),
        ]
    )
    await session.flush()


async def apple_sign_in(
    session: AsyncSession,
    id_token: str,
    nickname_hint: str | None,
    accepted_terms_version: str,
    accepted_privacy_version: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> tuple[User, TokenPair]:
    identity = await security.verify_apple_id_token(id_token)
    oauth_identity = await session.scalar(
        select(UserOAuthIdentity).where(
            UserOAuthIdentity.provider == "apple",
            UserOAuthIdentity.provider_sub == identity.sub,
        )
    )

    if oauth_identity is not None:
        user = await session.get(User, oauth_identity.user_id)
        if user is None or not user.is_active:
            raise AppError("USER_DISABLED", "사용할 수 없는 계정입니다.", HTTPStatus.FORBIDDEN)
        return user, _issue_token_pair(ActorType.USER, user.id)

    nickname = await _build_unique_nickname(session, nickname_hint)
    user = User(
        id=uuid4(),
        email=identity.email,
        nickname=nickname,
    )
    session.add(user)
    await session.flush()

    session.add(
        UserOAuthIdentity(
            id=uuid4(),
            user_id=user.id,
            provider="apple",
            provider_sub=identity.sub,
            email=identity.email,
            raw_payload=cast(dict[str, object], identity.model_dump(mode="json")),
        )
    )
    await _record_terms_acceptances(
        session,
        ActorType.USER,
        user.id,
        accepted_terms_version,
        accepted_privacy_version,
        ip_address,
        user_agent,
    )
    await session.flush()
    await session.refresh(user)
    return user, _issue_token_pair(ActorType.USER, user.id)


async def google_sign_in(
    session: AsyncSession,
    id_token: str,
    nickname_hint: str | None,
    accepted_terms_version: str,
    accepted_privacy_version: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> tuple[User, TokenPair]:
    identity = await security.verify_google_id_token(id_token)
    oauth_identity = await session.scalar(
        select(UserOAuthIdentity).where(
            UserOAuthIdentity.provider == "google",
            UserOAuthIdentity.provider_sub == identity.sub,
        )
    )

    if oauth_identity is not None:
        user = await session.get(User, oauth_identity.user_id)
        if user is None or not user.is_active:
            raise AppError("USER_DISABLED", "사용할 수 없는 계정입니다.", HTTPStatus.FORBIDDEN)
        return user, _issue_token_pair(ActorType.USER, user.id)

    hint = nickname_hint or identity.name
    nickname = await _build_unique_nickname(session, hint)
    user = User(
        id=uuid4(),
        email=identity.email,
        nickname=nickname,
    )
    session.add(user)
    await session.flush()

    session.add(
        UserOAuthIdentity(
            id=uuid4(),
            user_id=user.id,
            provider="google",
            provider_sub=identity.sub,
            email=identity.email,
            raw_payload=cast(dict[str, object], identity.model_dump(mode="json")),
        )
    )
    await _record_terms_acceptances(
        session,
        ActorType.USER,
        user.id,
        accepted_terms_version,
        accepted_privacy_version,
        ip_address,
        user_agent,
    )
    await session.flush()
    await session.refresh(user)
    return user, _issue_token_pair(ActorType.USER, user.id)


async def owner_signup(
    session: AsyncSession,
    req: OwnerSignupRequest,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Owner:
    email = _normalize_email(req.email)
    existing = await session.scalar(select(Owner.id).where(Owner.email == email))
    if existing is not None:
        raise AppError("EMAIL_TAKEN", "이미 가입된 이메일입니다.", HTTPStatus.CONFLICT)

    _validate_password_policy(req.password)
    owner = Owner(
        id=uuid4(),
        email=email,
        password_hash=security.hash_password(req.password),
        representative_name=req.representative_name,
        phone_number=req.phone_number,
    )
    session.add(owner)
    await session.flush()
    await _record_terms_acceptances(
        session,
        ActorType.OWNER,
        owner.id,
        req.accepted_terms_version,
        req.accepted_privacy_version,
        ip_address,
        user_agent,
    )
    await session.refresh(owner)
    return owner


async def owner_login(session: AsyncSession, req: OwnerLoginRequest) -> tuple[Owner, TokenPair]:
    email = _normalize_email(req.email)
    owner = await session.scalar(select(Owner).where(Owner.email == email))
    if owner is None or not owner.is_active:
        raise AppError(
            "INVALID_CREDENTIALS",
            "이메일 또는 비밀번호를 확인해주세요.",
            HTTPStatus.UNAUTHORIZED,
        )

    now = _now()
    if owner.locked_until is not None and _aware_utc(owner.locked_until) > now:
        raise AppError("ACCOUNT_LOCKED", "잠시 후 다시 시도해주세요.", HTTPStatus.LOCKED)

    if not security.verify_password(req.password, owner.password_hash):
        owner.login_failed_count += 1
        if owner.login_failed_count >= OWNER_LOCK_THRESHOLD:
            owner.locked_until = now + timedelta(minutes=OWNER_LOCK_MINUTES)
        await session.flush()
        raise AppError(
            "INVALID_CREDENTIALS",
            "이메일 또는 비밀번호를 확인해주세요.",
            HTTPStatus.UNAUTHORIZED,
        )

    owner.login_failed_count = 0
    owner.locked_until = None
    await session.flush()
    return owner, _issue_token_pair(ActorType.OWNER, owner.id)


async def refresh_tokens(session: AsyncSession, refresh_token: str) -> TokenPair:
    try:
        payload = security.decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("Token type is not refresh")
        actor_type = ActorType(str(payload.get("actor_type")))
        actor_id = UUID(str(payload.get("sub")))
    except Exception as exc:
        raise AppError(
            "INVALID_REFRESH_TOKEN", "다시 로그인해주세요.", HTTPStatus.UNAUTHORIZED
        ) from exc

    if actor_type == ActorType.USER:
        user = await session.get(User, actor_id)
        if user is None or not user.is_active:
            raise AppError(
                "INVALID_REFRESH_TOKEN",
                "다시 로그인해주세요.",
                HTTPStatus.UNAUTHORIZED,
            )
    elif actor_type == ActorType.OWNER:
        owner = await session.get(Owner, actor_id)
        if owner is None or not owner.is_active:
            raise AppError(
                "INVALID_REFRESH_TOKEN",
                "다시 로그인해주세요.",
                HTTPStatus.UNAUTHORIZED,
            )
    else:
        raise AppError("INVALID_REFRESH_TOKEN", "다시 로그인해주세요.", HTTPStatus.UNAUTHORIZED)

    return _issue_token_pair(actor_type, actor_id)


def _password_reset_token_hash(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


async def request_password_reset(session: AsyncSession, email: str) -> None:
    owner = await session.scalar(select(Owner).where(Owner.email == _normalize_email(email)))
    if owner is None or not owner.is_active:
        return

    token = secrets.token_urlsafe(32)
    session.add(
        PasswordResetToken(
            id=uuid4(),
            owner_id=owner.id,
            token_hash=_password_reset_token_hash(token),
            expires_at=_now() + timedelta(hours=PASSWORD_RESET_EXPIRE_HOURS),
        )
    )
    await session.flush()
    # TODO: Notification Agent 연동 후 실제 알림 발송으로 교체한다.
    logger.info("password_reset.token", owner_id=str(owner.id), token=token)


async def confirm_password_reset(session: AsyncSession, token: str, new_password: str) -> None:
    _validate_password_policy(new_password)
    now = _now()
    reset_token = await session.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == _password_reset_token_hash(token),
            PasswordResetToken.expires_at > now,
            PasswordResetToken.used_at.is_(None),
        )
    )
    if reset_token is None:
        raise AppError(
            "INVALID_RESET_TOKEN",
            "비밀번호 재설정 링크가 올바르지 않습니다.",
            HTTPStatus.BAD_REQUEST,
        )

    owner = await session.get(Owner, reset_token.owner_id)
    if owner is None or not owner.is_active:
        raise AppError(
            "INVALID_RESET_TOKEN",
            "비밀번호 재설정 링크가 올바르지 않습니다.",
            HTTPStatus.BAD_REQUEST,
        )

    owner.password_hash = security.hash_password(new_password)
    owner.login_failed_count = 0
    owner.locked_until = None
    reset_token.used_at = now
    await session.flush()
