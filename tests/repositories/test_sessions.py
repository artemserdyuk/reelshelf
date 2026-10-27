import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from reelshelf.domain.entities import RefreshSession
from reelshelf.domain.errors import ConflictError
from reelshelf.repositories.memory import InMemoryRefreshSessionRepository


@pytest.fixture
def now() -> datetime:
    return datetime(2026, 1, 1, tzinfo=UTC)


@pytest.fixture
def session(now: datetime) -> RefreshSession:
    return RefreshSession(
        jti=uuid4(),
        family_id=uuid4(),
        user_id=uuid4(),
        expires_at=now + timedelta(days=7),
    )


async def test_add_and_find_session(session: RefreshSession) -> None:
    repository = InMemoryRefreshSessionRepository()
    await repository.add(session)

    result = await repository.get_by_jti(session.jti)

    assert result == session
    assert result is not session
    assert await repository.get_by_jti(uuid4()) is None


async def test_duplicate_session_is_rejected(
    session: RefreshSession,
) -> None:
    repository = InMemoryRefreshSessionRepository()
    await repository.add(session)

    with pytest.raises(ConflictError):
        await repository.add(session)


async def test_session_can_be_consumed_only_once(
    session: RefreshSession,
    now: datetime,
) -> None:
    repository = InMemoryRefreshSessionRepository()
    await repository.add(session)

    assert await repository.consume(session.jti, now=now) is True
    assert await repository.consume(session.jti, now=now) is False

    stored = await repository.get_by_jti(session.jti)
    assert stored is not None
    assert stored.used_at == now


async def test_concurrent_consumption_has_one_winner(
    session: RefreshSession,
    now: datetime,
) -> None:
    repository = InMemoryRefreshSessionRepository()
    await repository.add(session)

    results = await asyncio.gather(
        repository.consume(session.jti, now=now),
        repository.consume(session.jti, now=now),
    )

    assert results.count(True) == 1
    assert results.count(False) == 1


async def test_expired_session_cannot_be_consumed(
    session: RefreshSession,
    now: datetime,
) -> None:
    repository = InMemoryRefreshSessionRepository()
    expired = replace(session, expires_at=now)

    await repository.add(expired)

    assert await repository.consume(expired.jti, now=now) is False

    stored = await repository.get_by_jti(expired.jti)
    assert stored is not None
    assert stored.used_at is None


async def test_missing_session_cannot_be_consumed(now: datetime) -> None:
    repository = InMemoryRefreshSessionRepository()

    assert await repository.consume(uuid4(), now=now) is False


async def test_revocation_affects_only_selected_family(
    session: RefreshSession,
    now: datetime,
) -> None:
    repository = InMemoryRefreshSessionRepository()

    same_family = replace(session, jti=uuid4())
    other_family = replace(
        session,
        jti=uuid4(),
        family_id=uuid4(),
    )

    for item in (session, same_family, other_family):
        await repository.add(item)

    await repository.revoke_family(session.family_id, now=now)

    assert await repository.consume(session.jti, now=now) is False
    assert await repository.consume(same_family.jti, now=now) is False
    assert await repository.consume(other_family.jti, now=now) is True

    await repository.revoke_family(
        session.family_id,
        now=now + timedelta(minutes=1),
    )

    stored = await repository.get_by_jti(session.jti)
    assert stored is not None

    # Repeated revocation must preserve the original timestamp.
    assert stored.revoked_at == now
