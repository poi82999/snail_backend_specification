import asyncio
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from typing import Any, cast
from uuid import UUID, uuid4

import httpx
import jwt
from passlib.context import CryptContext  # type: ignore[import-untyped]
from pydantic import BaseModel

from app.api.errors import AppError
from app.core.config import get_settings
from app.models.enums import ActorType

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

APPLE_JWKS_URL = "https://appleid.apple.com/auth/keys"
APPLE_JWKS_CACHE_SECONDS = 60 * 60

_apple_jwks_cache: dict[str, object] = {}
_apple_jwks_lock = asyncio.Lock()


class AppleIdentity(BaseModel):
    sub: str
    email: str | None = None
    email_verified: bool = False
    is_private_email: bool = False


def hash_password(password: str) -> str:
    return cast(str, password_context.hash(password))


def verify_password(plain_password: str, password_hash: str) -> bool:
    return cast(bool, password_context.verify(plain_password, password_hash))


def _issue_token(
    token_type: str,
    actor_type: ActorType,
    sub: UUID,
    expires_at: datetime,
    extra: dict[str, Any] | None = None,
) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = dict(extra or {})
    payload.update(
        {
            "sub": str(sub),
            "actor_type": actor_type.value,
            "type": token_type,
            "iat": now,
            "exp": expires_at,
            "jti": uuid4().hex,
        }
    )
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def issue_access_token(
    actor_type: ActorType, sub: UUID, extra: dict[str, Any] | None = None
) -> str:
    settings = get_settings()
    return _issue_token(
        "access",
        actor_type,
        sub,
        datetime.now(UTC) + timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MIN),
        extra,
    )


def issue_refresh_token(actor_type: ActorType, sub: UUID) -> str:
    settings = get_settings()
    return _issue_token(
        "refresh",
        actor_type,
        sub,
        datetime.now(UTC) + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS),
    )


def create_access_token(subject: str, actor_type: str, extra: dict[str, Any] | None = None) -> str:
    return issue_access_token(ActorType(actor_type), UUID(subject), extra)


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    decoded = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    if not isinstance(decoded, dict):
        raise ValueError("JWT payload must be an object")
    return decoded


async def _get_apple_jwks() -> dict[str, Any]:
    now = datetime.now(UTC)
    cached_keys = _apple_jwks_cache.get("keys")
    cached_expires_at = _apple_jwks_cache.get("expires_at")
    if isinstance(cached_keys, dict) and isinstance(cached_expires_at, datetime):
        if cached_expires_at > now:
            return cached_keys

    async with _apple_jwks_lock:
        cached_keys = _apple_jwks_cache.get("keys")
        cached_expires_at = _apple_jwks_cache.get("expires_at")
        if isinstance(cached_keys, dict) and isinstance(cached_expires_at, datetime):
            if cached_expires_at > now:
                return cached_keys

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(APPLE_JWKS_URL)
                response.raise_for_status()
                jwks = response.json()
        except Exception as exc:
            raise AppError(
                "APPLE_VERIFY_FAILED",
                "Apple 인증에 실패했습니다.",
                HTTPStatus.UNAUTHORIZED,
            ) from exc

        if not isinstance(jwks, dict) or not isinstance(jwks.get("keys"), list):
            raise AppError(
                "APPLE_VERIFY_FAILED",
                "Apple 인증에 실패했습니다.",
                HTTPStatus.UNAUTHORIZED,
            )

        _apple_jwks_cache["keys"] = jwks
        _apple_jwks_cache["expires_at"] = now + timedelta(seconds=APPLE_JWKS_CACHE_SECONDS)
        return jwks


def _bool_claim(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    return False


async def verify_apple_id_token(id_token: str) -> AppleIdentity:
    settings = get_settings()
    try:
        header = jwt.get_unverified_header(id_token)
        kid = header.get("kid")
        if not isinstance(kid, str):
            raise ValueError("Apple token header must contain kid")

        jwks = await _get_apple_jwks()
        keys = jwks.get("keys")
        if not isinstance(keys, list):
            raise ValueError("Apple JWKS keys must be a list")

        jwk = next((key for key in keys if isinstance(key, dict) and key.get("kid") == kid), None)
        if jwk is None:
            raise ValueError("Apple signing key not found")

        signing_key = jwt.PyJWK.from_dict(jwk).key
        payload = jwt.decode(
            id_token,
            signing_key,
            algorithms=["RS256"],
            audience=settings.APPLE_CLIENT_ID,
            issuer="https://appleid.apple.com",
        )
        if not isinstance(payload, dict):
            raise ValueError("Apple token payload must be an object")

        return AppleIdentity(
            sub=str(payload["sub"]),
            email=cast(str | None, payload.get("email")),
            email_verified=_bool_claim(payload.get("email_verified")),
            is_private_email=_bool_claim(payload.get("is_private_email")),
        )
    except AppError:
        raise
    except Exception as exc:
        raise AppError(
            "APPLE_VERIFY_FAILED",
            "Apple 인증에 실패했습니다.",
            HTTPStatus.UNAUTHORIZED,
        ) from exc
