from uuid import uuid4

import pytest
from app.api.errors import AppError
from app.models.accounts import TermsAcceptance, User, UserOAuthIdentity
from app.services import auth_service
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_google_sign_in_creates_user_and_oauth_identity(
    db_session: AsyncSession, mock_google_signin: object
) -> None:
    user, tokens = await auth_service.google_sign_in(
        db_session,
        "id-token",
        None,
        "1.0",
        "1.0",
    )

    oauth_identity = await db_session.scalar(
        select(UserOAuthIdentity).where(UserOAuthIdentity.user_id == user.id)
    )

    assert user.email == "google@example.com"
    assert oauth_identity is not None
    assert oauth_identity.provider == "google"
    assert oauth_identity.provider_sub == "google-test-sub"
    assert tokens.access_token
    assert tokens.refresh_token


@pytest.mark.asyncio
async def test_google_sign_in_uses_name_as_nickname_hint(
    db_session: AsyncSession, mock_google_signin: object
) -> None:
    user, _ = await auth_service.google_sign_in(
        db_session,
        "id-token",
        None,
        "1.0",
        "1.0",
    )

    # Google identity의 name 필드("테스트유저")가 nickname_hint로 사용된다.
    assert "테스트유저" in user.nickname


@pytest.mark.asyncio
async def test_google_sign_in_creates_terms_acceptance_for_new_user(
    db_session: AsyncSession, mock_google_signin: object
) -> None:
    user, _ = await auth_service.google_sign_in(
        db_session,
        "id-token",
        None,
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
async def test_google_sign_in_existing_user_returns_same_user(
    db_session: AsyncSession, mock_google_signin: object
) -> None:
    user = User(
        id=uuid4(),
        email="google@example.com",
        nickname="existing",
    )
    db_session.add(user)
    await db_session.flush()
    db_session.add(
        UserOAuthIdentity(
            id=uuid4(),
            user_id=user.id,
            provider="google",
            provider_sub="google-test-sub",
            email=user.email,
        )
    )
    await db_session.flush()

    returned_user, _ = await auth_service.google_sign_in(
        db_session,
        "id-token",
        None,
        "1.0",
        "1.0",
    )

    assert returned_user.id == user.id
    assert returned_user.nickname == "existing"


@pytest.mark.asyncio
async def test_google_sign_in_existing_user_does_not_create_terms_acceptance(
    db_session: AsyncSession, mock_google_signin: object
) -> None:
    user = User(
        id=uuid4(),
        email="google@example.com",
        nickname="existing",
    )
    db_session.add(user)
    await db_session.flush()
    db_session.add(
        UserOAuthIdentity(
            id=uuid4(),
            user_id=user.id,
            provider="google",
            provider_sub="google-test-sub",
            email=user.email,
        )
    )
    await db_session.flush()

    await auth_service.google_sign_in(
        db_session,
        "id-token",
        None,
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
async def test_google_sign_in_adds_suffix_on_nickname_collision(
    db_session: AsyncSession, mock_google_signin: object
) -> None:
    # "테스트유저" 닉네임을 미리 차지해 둔다.
    db_session.add(
        User(
            id=uuid4(),
            email="other@example.com",
            nickname="테스트유저",
        )
    )
    await db_session.flush()

    user, _ = await auth_service.google_sign_in(
        db_session,
        "id-token",
        None,
        "1.0",
        "1.0",
    )

    assert user.nickname != "테스트유저"
    assert user.nickname.startswith("테스트유저_")


@pytest.mark.asyncio
async def test_google_sign_in_disabled_user_raises_error(
    db_session: AsyncSession, mock_google_signin: object
) -> None:
    user = User(
        id=uuid4(),
        email="google@example.com",
        nickname="disabled",
        is_active=False,
    )
    db_session.add(user)
    await db_session.flush()
    db_session.add(
        UserOAuthIdentity(
            id=uuid4(),
            user_id=user.id,
            provider="google",
            provider_sub="google-test-sub",
            email=user.email,
        )
    )
    await db_session.flush()

    with pytest.raises(AppError) as exc_info:
        await auth_service.google_sign_in(
            db_session,
            "id-token",
            None,
            "1.0",
            "1.0",
        )

    assert exc_info.value.code == "USER_DISABLED"
    assert exc_info.value.status_code == 403
