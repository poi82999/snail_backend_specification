from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from app.api.errors import AppError
from app.core.security import hash_password, issue_refresh_token
from app.models.accounts import Owner, TermsAcceptance, User, UserOAuthIdentity
from app.models.enums import ActorType
from app.schemas.auth import OwnerLoginRequest, OwnerSignupRequest
from app.services import auth_service
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_apple_sign_in_creates_user_and_oauth_identity(
    db_session: AsyncSession, mock_apple_signin: object
) -> None:
    user, tokens = await auth_service.apple_sign_in(
        db_session,
        "id-token",
        "tester",
        "1.0",
        "1.0",
    )

    oauth_identity = await db_session.scalar(
        select(UserOAuthIdentity).where(UserOAuthIdentity.user_id == user.id)
    )

    assert user.nickname == "tester"
    assert user.apple_sub is None
    assert oauth_identity is not None
    assert oauth_identity.provider == "apple"
    assert tokens.access_token
    assert tokens.refresh_token


@pytest.mark.asyncio
async def test_apple_sign_in_creates_terms_acceptance_for_new_user(
    db_session: AsyncSession, mock_apple_signin: object
) -> None:
    user, _ = await auth_service.apple_sign_in(
        db_session,
        "id-token",
        "tester",
        "1.0",
        "1.1",
        "203.0.113.10",
        "pytest-agent",
    )

    terms = (
        await db_session.scalars(
            select(TermsAcceptance).where(
                TermsAcceptance.actor_type == "user",
                TermsAcceptance.actor_id == user.id,
            )
        )
    ).all()

    assert {(term.policy_type, term.version) for term in terms} == {
        ("privacy_policy", "1.1"),
        ("terms_of_service", "1.0"),
    }
    assert len(terms) == 2
    assert all(term.ip_address == "203.0.113.10" for term in terms)
    assert all(term.user_agent == "pytest-agent" for term in terms)


@pytest.mark.asyncio
async def test_apple_sign_in_existing_user_returns_same_user(
    db_session: AsyncSession, mock_apple_signin: object
) -> None:
    user = User(
        id=uuid4(),
        email="apple@example.com",
        nickname="existing",
    )
    db_session.add(user)
    await db_session.flush()
    db_session.add(
        UserOAuthIdentity(
            id=uuid4(),
            user_id=user.id,
            provider="apple",
            provider_sub="apple-test-sub",
            email=user.email,
        )
    )
    await db_session.flush()

    returned_user, _ = await auth_service.apple_sign_in(
        db_session,
        "id-token",
        "other",
        "1.0",
        "1.0",
    )

    assert returned_user.id == user.id
    assert returned_user.nickname == "existing"


@pytest.mark.asyncio
async def test_apple_sign_in_existing_user_does_not_create_terms_acceptance(
    db_session: AsyncSession, mock_apple_signin: object
) -> None:
    user = User(
        id=uuid4(),
        email="apple@example.com",
        nickname="existing",
    )
    db_session.add(user)
    await db_session.flush()
    db_session.add(
        UserOAuthIdentity(
            id=uuid4(),
            user_id=user.id,
            provider="apple",
            provider_sub="apple-test-sub",
            email=user.email,
        )
    )
    await db_session.flush()

    await auth_service.apple_sign_in(
        db_session,
        "id-token",
        "other",
        "1.0",
        "1.0",
        "203.0.113.10",
        "pytest-agent",
    )

    terms = (
        await db_session.scalars(
            select(TermsAcceptance).where(
                TermsAcceptance.actor_type == "user",
                TermsAcceptance.actor_id == user.id,
            )
        )
    ).all()

    assert terms == []


@pytest.mark.asyncio
async def test_apple_sign_in_adds_suffix_on_nickname_collision(
    db_session: AsyncSession, mock_apple_signin: object
) -> None:
    db_session.add(
        User(
            id=uuid4(),
            apple_sub="legacy-sub",
            email="legacy@example.com",
            nickname="taken",
        )
    )
    await db_session.flush()

    user, _ = await auth_service.apple_sign_in(
        db_session,
        "id-token",
        "taken",
        "1.0",
        "1.0",
    )

    assert user.nickname != "taken"
    assert user.nickname.startswith("taken_")


@pytest.mark.asyncio
async def test_owner_signup_rejects_password_policy_violation(
    db_session: AsyncSession,
) -> None:
    request = OwnerSignupRequest(
        email="owner@example.com",
        password="lowercase1",
        representative_name="대표",
        phone_number="010-0000-0000",
        accepted_terms_version="1.0",
        accepted_privacy_version="1.0",
    )

    with pytest.raises(AppError) as exc_info:
        await auth_service.owner_signup(db_session, request)

    assert exc_info.value.code == "INVALID_PASSWORD_POLICY"
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_owner_signup_rejects_duplicate_email(db_session: AsyncSession) -> None:
    db_session.add(
        Owner(
            id=uuid4(),
            email="owner@example.com",
            password_hash=hash_password("Strong123"),
            representative_name="기존 대표",
            phone_number="010-0000-0000",
        )
    )
    await db_session.flush()
    request = OwnerSignupRequest(
        email="OWNER@example.com",
        password="Strong123",
        representative_name="대표",
        phone_number="010-1111-1111",
        accepted_terms_version="1.0",
        accepted_privacy_version="1.0",
    )

    with pytest.raises(AppError) as exc_info:
        await auth_service.owner_signup(db_session, request)

    assert exc_info.value.code == "EMAIL_TAKEN"
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_owner_signup_creates_terms_acceptance(db_session: AsyncSession) -> None:
    request = OwnerSignupRequest(
        email="owner@example.com",
        password="Strong123",
        representative_name="대표",
        phone_number="010-0000-0000",
        accepted_terms_version="1.0",
        accepted_privacy_version="1.1",
    )

    owner = await auth_service.owner_signup(db_session, request, "2001:db8::1", "pytest-agent")
    terms = (
        await db_session.scalars(
            select(TermsAcceptance).where(
                TermsAcceptance.actor_type == "owner",
                TermsAcceptance.actor_id == owner.id,
            )
        )
    ).all()

    assert {(term.policy_type, term.version) for term in terms} == {
        ("privacy_policy", "1.1"),
        ("terms_of_service", "1.0"),
    }
    assert len(terms) == 2
    assert all(term.ip_address == "2001:db8::1" for term in terms)
    assert all(term.user_agent == "pytest-agent" for term in terms)


@pytest.mark.asyncio
async def test_owner_login_sets_locked_until_after_five_failures(
    db_session: AsyncSession,
) -> None:
    owner = Owner(
        id=uuid4(),
        email="owner@example.com",
        password_hash=hash_password("Strong123"),
        representative_name="대표",
        phone_number="010-0000-0000",
    )
    db_session.add(owner)
    await db_session.flush()
    request = OwnerLoginRequest(email=owner.email, password="Wrong123")

    for _ in range(5):
        with pytest.raises(AppError):
            await auth_service.owner_login(db_session, request)

    assert owner.login_failed_count == 5
    assert owner.locked_until is not None


@pytest.mark.asyncio
async def test_owner_login_rejects_locked_account(db_session: AsyncSession) -> None:
    owner = Owner(
        id=uuid4(),
        email="owner@example.com",
        password_hash=hash_password("Strong123"),
        representative_name="대표",
        phone_number="010-0000-0000",
        locked_until=datetime.now(UTC) + timedelta(minutes=15),
    )
    db_session.add(owner)
    await db_session.flush()

    with pytest.raises(AppError) as exc_info:
        await auth_service.owner_login(
            db_session,
            OwnerLoginRequest(email=owner.email, password="Strong123"),
        )

    assert exc_info.value.code == "ACCOUNT_LOCKED"
    assert exc_info.value.status_code == 423


@pytest.mark.asyncio
async def test_refresh_tokens_rotates_access_and_refresh(db_session: AsyncSession) -> None:
    owner = Owner(
        id=uuid4(),
        email="owner@example.com",
        password_hash=hash_password("Strong123"),
        representative_name="대표",
        phone_number="010-0000-0000",
    )
    db_session.add(owner)
    await db_session.flush()
    refresh_token = issue_refresh_token(ActorType.OWNER, owner.id)

    tokens = await auth_service.refresh_tokens(db_session, refresh_token)

    assert tokens.access_token
    assert tokens.refresh_token
    assert tokens.refresh_token != refresh_token
