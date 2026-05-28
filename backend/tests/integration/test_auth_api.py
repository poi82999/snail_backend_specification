from uuid import UUID, uuid4

import pytest
from app.core.security import issue_refresh_token
from app.models.accounts import TermsAcceptance, UserOAuthIdentity
from app.models.enums import ActorType
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.community_factories import auth_headers, create_user


def _owner_signup_payload(email: str) -> dict[str, str]:
    return {
        "email": email,
        "password": "Strong123",
        "representative_name": "대표",
        "phone_number": "010-0000-0000",
        "accepted_terms_version": "1.0",
        "accepted_privacy_version": "1.0",
    }


@pytest.mark.asyncio
async def test_post_auth_apple_happy_path(
    api_client: AsyncClient,
    db_session: AsyncSession,
    mock_apple_signin: object,
) -> None:
    response = await api_client.post(
        "/api/v1/auth/apple",
        json={
            "id_token": "id-token",
            "nonce": "nonce",
            "accepted_terms_version": "1.0",
            "accepted_privacy_version": "1.0",
        },
        headers={"Idempotency-Key": f"apple-{uuid4()}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["tokens"]["access_token"]
    assert body["tokens"]["refresh_token"]
    assert body["user"]["email"] == "apple@example.com"

    oauth_identity = await db_session.scalar(
        select(UserOAuthIdentity).where(
            UserOAuthIdentity.provider == "apple",
            UserOAuthIdentity.provider_sub == "apple-test-sub",
        )
    )
    assert oauth_identity is not None


@pytest.mark.asyncio
async def test_apple_sign_in_creates_terms_acceptance(
    api_client: AsyncClient,
    db_session: AsyncSession,
    mock_apple_signin: object,
) -> None:
    response = await api_client.post(
        "/api/v1/auth/apple",
        json={
            "id_token": "id-token",
            "accepted_terms_version": "1.0",
            "accepted_privacy_version": "1.1",
        },
        headers={
            "Idempotency-Key": f"apple-terms-{uuid4()}",
            "User-Agent": "pytest-agent",
        },
    )

    assert response.status_code == 200
    user_id = UUID(response.json()["user"]["id"])
    terms = (
        await db_session.scalars(
            select(TermsAcceptance).where(
                TermsAcceptance.actor_type == "user",
                TermsAcceptance.actor_id == user_id,
            )
        )
    ).all()

    assert {(term.policy_type, term.version) for term in terms} == {
        ("privacy_policy", "1.1"),
        ("terms_of_service", "1.0"),
    }
    assert len(terms) == 2
    assert all(term.user_agent == "pytest-agent" for term in terms)


@pytest.mark.asyncio
async def test_owner_signup_creates_terms_acceptance(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    response = await api_client.post(
        "/api/v1/auth/owner/signup",
        json=_owner_signup_payload(f"{uuid4().hex}@example.com"),
        headers={
            "Idempotency-Key": f"signup-terms-{uuid4()}",
            "User-Agent": "pytest-agent",
        },
    )

    assert response.status_code == 201
    owner_id = UUID(response.json()["id"])
    terms = (
        await db_session.scalars(
            select(TermsAcceptance).where(
                TermsAcceptance.actor_type == "owner",
                TermsAcceptance.actor_id == owner_id,
            )
        )
    ).all()

    assert {(term.policy_type, term.version) for term in terms} == {
        ("privacy_policy", "1.0"),
        ("terms_of_service", "1.0"),
    }
    assert len(terms) == 2


@pytest.mark.asyncio
async def test_apple_sign_in_missing_terms_version_returns_422(
    api_client: AsyncClient,
) -> None:
    response = await api_client.post(
        "/api/v1/auth/apple",
        json={
            "id_token": "id-token",
            "accepted_privacy_version": "1.0",
        },
        headers={"Idempotency-Key": f"apple-missing-terms-{uuid4()}"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_owner_signup_login_refresh_flow(api_client: AsyncClient) -> None:
    email = f"{uuid4().hex}@example.com"
    signup_response = await api_client.post(
        "/api/v1/auth/owner/signup",
        json=_owner_signup_payload(email),
        headers={"Idempotency-Key": f"signup-{uuid4()}"},
    )
    assert signup_response.status_code == 201

    login_response = await api_client.post(
        "/api/v1/auth/owner/login",
        json={"email": email, "password": "Strong123"},
        headers={"Idempotency-Key": f"login-{uuid4()}"},
    )
    assert login_response.status_code == 200
    login_body = login_response.json()

    refresh_response = await api_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login_body["refresh_token"]},
        headers={"Idempotency-Key": f"refresh-{uuid4()}"},
    )
    assert refresh_response.status_code == 200
    refresh_body = refresh_response.json()
    assert refresh_body["access_token"]
    assert refresh_body["refresh_token"] != login_body["refresh_token"]


@pytest.mark.asyncio
async def test_login_without_idempotency_key_succeeds(api_client: AsyncClient) -> None:
    email = f"{uuid4().hex}@example.com"
    signup_response = await api_client.post(
        "/api/v1/auth/owner/signup",
        json=_owner_signup_payload(email),
        headers={"Idempotency-Key": f"login-no-idem-signup-{uuid4()}"},
    )
    assert signup_response.status_code == 201

    response = await api_client.post(
        "/api/v1/auth/owner/login",
        json={"email": email, "password": "Strong123"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"]


@pytest.mark.asyncio
async def test_refresh_without_idempotency_key_succeeds(api_client: AsyncClient) -> None:
    email = f"{uuid4().hex}@example.com"
    signup_response = await api_client.post(
        "/api/v1/auth/owner/signup",
        json=_owner_signup_payload(email),
        headers={"Idempotency-Key": f"refresh-no-idem-signup-{uuid4()}"},
    )
    assert signup_response.status_code == 201
    login_response = await api_client.post(
        "/api/v1/auth/owner/login",
        json={"email": email, "password": "Strong123"},
    )
    assert login_response.status_code == 200

    response = await api_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login_response.json()["refresh_token"]},
    )

    assert response.status_code == 200
    assert response.json()["access_token"]


@pytest.mark.asyncio
async def test_signup_without_idempotency_key_returns_400(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/api/v1/auth/owner/signup",
        json=_owner_signup_payload(f"{uuid4().hex}@example.com"),
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "IDEMPOTENCY_KEY_REQUIRED"


@pytest.mark.asyncio
async def test_idempotency_key_missing_returns_400(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/api/v1/auth/apple",
        json={
            "id_token": "id-token",
            "accepted_terms_version": "1.0",
            "accepted_privacy_version": "1.0",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "IDEMPOTENCY_KEY_REQUIRED"


@pytest.mark.asyncio
async def test_same_idempotency_key_returns_same_response(api_client: AsyncClient) -> None:
    key = f"same-{uuid4()}"
    payload = _owner_signup_payload(f"{uuid4().hex}@example.com")

    first = await api_client.post(
        "/api/v1/auth/owner/signup",
        json=payload,
        headers={"Idempotency-Key": key},
    )
    second = await api_client.post(
        "/api/v1/auth/owner/signup",
        json=payload,
        headers={"Idempotency-Key": key},
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json() == first.json()


@pytest.mark.asyncio
async def test_refresh_token_cannot_call_me(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user(db_session)
    refresh_token = issue_refresh_token(ActorType.USER, user.id)

    response = await api_client.get("/api/v1/me", headers=auth_headers(refresh_token))

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN_TYPE"
