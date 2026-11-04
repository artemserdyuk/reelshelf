import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from reelshelf.domain.entities import RefreshSession
from reelshelf.repositories.memory import InMemoryRefreshSessionRepository


async def test_two_refreshes_have_one_winner_and_revoke_its_successor() -> None:
    repo = InMemoryRefreshSessionRepository()
    now = datetime(2026, 1, 1, tzinfo=UTC)
    original = RefreshSession(
        jti=uuid4(),
        family_id=uuid4(),
        user_id=uuid4(),
        expires_at=now + timedelta(days=7),
    )
    await repo.add(original)

    first_id, second_id = uuid4(), uuid4()
    results = await asyncio.gather(
        repo.rotate(original.jti, user_id=original.user_id, new_jti=first_id, now=now),
        repo.rotate(original.jti, user_id=original.user_id, new_jti=second_id, now=now),
    )

    assert results.count(True) == 1
    assert results.count(False) == 1

    candidates = [
        await repo.get_by_jti(first_id),
        await repo.get_by_jti(second_id),
    ]
    created = [item for item in candidates if item is not None]

    # Only one successor was stored. Replay revoked even that successor.
    assert len(created) == 1
    assert created[0].family_id == original.family_id
    assert created[0].expires_at == original.expires_at
    assert created[0].revoked_at == now
