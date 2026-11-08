from datetime import UTC, datetime
from uuid import UUID, uuid4

from reelshelf.domain.entities import WatchlistEntry
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
