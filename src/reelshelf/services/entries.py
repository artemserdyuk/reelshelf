from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from reelshelf.domain.commands import EntryChanges
from reelshelf.domain.entities import EntryPage, EntryStatus, WatchlistEntry
from reelshelf.domain.errors import BusinessRuleError, NotFoundError
from reelshelf.domain.repositories import EntryRepository


class EntryService:
    def __init__(self, *, entries: EntryRepository) -> None:
        self._entries = entries

    async def create(
        self,
        *,
        user_id: UUID,
        title: str,
        release_year: int | None,
    ) -> WatchlistEntry:
        now = datetime.now(UTC)
        entry = WatchlistEntry(
            id=uuid4(),
            user_id=user_id,
            title=title,
            release_year=release_year,
            created_at=now,
            updated_at=now,
        )
        await self._entries.add(entry)
        return entry

    async def list_for_user(
        self,
        *,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
        status: EntryStatus | None = None,
    ) -> EntryPage:
        return await self._entries.list_for_user(
            user_id, limit=limit, offset=offset, status=status
        )

    async def get_for_user(
        self,
        *,
        entry_id: UUID,
        user_id: UUID,
    ) -> WatchlistEntry:
        entry = await self._entries.get_for_user(user_id=user_id, entry_id=entry_id)

        if entry is None:
            raise NotFoundError("Watchlist entry not found.")

        return entry

    async def update(
        self,
        *,
        entry_id: UUID,
        user_id: UUID,
        changes: EntryChanges,
    ) -> WatchlistEntry:
        current = await self.get_for_user(entry_id=entry_id, user_id=user_id)

        if not changes:
            raise BusinessRuleError("At least one field is required.")

        candidate = replace(current, **changes)

        if candidate.rating is not None and candidate.status != EntryStatus.WATCHED:
            raise BusinessRuleError("Only watched entries can have a rating.")

        if candidate == current:
            return current

        updated = replace(candidate, updated_at=datetime.now(UTC))
        await self._entries.update(updated)
        return updated
