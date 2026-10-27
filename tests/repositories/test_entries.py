from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from reelshelf.domain.entities import EntryStatus, WatchlistEntry
from reelshelf.domain.errors import ConflictError, NotFoundError
from reelshelf.repositories.memory import InMemoryEntryRepository


@pytest.fixture
def entry() -> WatchlistEntry:
    now = datetime(2026, 1, 1, tzinfo=UTC)

    return WatchlistEntry(
        id=UUID(int=1),
        user_id=uuid4(),
        title="Arrival",
        release_year=2016,
        created_at=now,
        updated_at=now,
    )


async def test_add_and_find_entry(entry: WatchlistEntry) -> None:
    repository = InMemoryEntryRepository()
    await repository.add(entry)

    result = await repository.get_for_user(entry.id, entry.user_id)

    assert result == entry
    assert result is not entry


async def test_missing_or_foreign_entry_returns_none(
    entry: WatchlistEntry,
) -> None:
    repository = InMemoryEntryRepository()
    await repository.add(entry)

    assert await repository.get_for_user(uuid4(), entry.user_id) is None
    assert await repository.get_for_user(entry.id, uuid4()) is None


async def test_duplicate_entry_id_is_rejected(
    entry: WatchlistEntry,
) -> None:
    repository = InMemoryEntryRepository()
    await repository.add(entry)

    with pytest.raises(ConflictError):
        await repository.add(entry)


async def test_list_filters_before_pagination(
    entry: WatchlistEntry,
) -> None:
    repository = InMemoryEntryRepository()

    older_watched = replace(entry, status=EntryStatus.WATCHED)

    newer_watched = replace(
        entry,
        id=UUID(int=2),
        title="Interstellar",
        status=EntryStatus.WATCHED,
        created_at=entry.created_at + timedelta(days=1),
    )

    planned = replace(entry, id=UUID(int=3))

    foreign = replace(
        entry,
        id=UUID(int=4),
        user_id=uuid4(),
        status=EntryStatus.WATCHED,
    )

    for item in (older_watched, newer_watched, planned, foreign):
        await repository.add(item)

    page = await repository.list_for_user(
        entry.user_id,
        status=EntryStatus.WATCHED,
        limit=1,
        offset=1,
    )

    # Only two entries match the owner and status.
    assert page.total == 2

    # The newest matching entry was skipped by offset=1.
    assert page.items == (older_watched,)


async def test_list_uses_id_as_sort_tie_breaker(
    entry: WatchlistEntry,
) -> None:
    repository = InMemoryEntryRepository()
    second = replace(entry, id=UUID(int=2))

    await repository.add(entry)
    await repository.add(second)

    page = await repository.list_for_user(entry.user_id)

    assert page.total == 2
    assert page.items == (second, entry)


async def test_offset_beyond_last_item_preserves_total(
    entry: WatchlistEntry,
) -> None:
    repository = InMemoryEntryRepository()
    await repository.add(entry)

    page = await repository.list_for_user(entry.user_id, offset=100)

    assert page.items == ()
    assert page.total == 1


@pytest.mark.parametrize(
    ("limit", "offset"),
    [(0, 0), (101, 0), (20, -1)],
)
async def test_invalid_pagination_is_rejected(
    limit: int,
    offset: int,
) -> None:
    repository = InMemoryEntryRepository()

    with pytest.raises(ValueError):
        await repository.list_for_user(
            uuid4(),
            limit=limit,
            offset=offset,
        )


async def test_changes_require_explicit_update(
    entry: WatchlistEntry,
) -> None:
    repository = InMemoryEntryRepository()
    await repository.add(entry)

    loaded = await repository.get_for_user(entry.id, entry.user_id)
    assert loaded is not None

    updated = replace(loaded, title="Updated title")

    # Creating a modified copy does not update storage.
    assert await repository.get_for_user(entry.id, entry.user_id) == entry

    await repository.update(updated)

    assert await repository.get_for_user(entry.id, entry.user_id) == updated


async def test_update_cannot_change_owner(
    entry: WatchlistEntry,
) -> None:
    repository = InMemoryEntryRepository()
    await repository.add(entry)

    foreign_update = replace(entry, user_id=uuid4())

    with pytest.raises(NotFoundError):
        await repository.update(foreign_update)

    assert await repository.get_for_user(entry.id, entry.user_id) == entry


async def test_update_missing_entry_is_rejected(
    entry: WatchlistEntry,
) -> None:
    repository = InMemoryEntryRepository()

    with pytest.raises(NotFoundError):
        await repository.update(entry)


async def test_delete_checks_owner(entry: WatchlistEntry) -> None:
    repository = InMemoryEntryRepository()
    await repository.add(entry)

    assert await repository.delete_for_user(entry.id, uuid4()) is False
    assert await repository.get_for_user(entry.id, entry.user_id) == entry

    assert await repository.delete_for_user(entry.id, entry.user_id) is True
    assert await repository.get_for_user(entry.id, entry.user_id) is None

    assert await repository.delete_for_user(entry.id, entry.user_id) is False
