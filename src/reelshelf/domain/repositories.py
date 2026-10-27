from datetime import datetime
from typing import Protocol
from uuid import UUID

from reelshelf.domain.entities import (
    EntryPage,
    EntryStatus,
    RefreshSession,
    User,
    WatchlistEntry,
)


class UserRepository(Protocol):
    async def add(self, user: User) -> None:
        """Raise ConflictError for a duplicate ID or username."""
        ...

    async def get_by_id(self, user_id: UUID) -> User | None: ...

    async def get_by_username(self, username: str) -> User | None:
        """Receive an already normalized username."""
        ...


class EntryRepository(Protocol):
    async def add(self, entry: WatchlistEntry) -> None: ...

    async def get_for_user(
        self, entry_id: UUID, user_id: UUID
    ) -> WatchlistEntry | None: ...

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        status: EntryStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> EntryPage: ...

    async def update(self, entry: WatchlistEntry) -> None:
        """Update an existing entry without changing its owner."""
        ...

    async def delete_for_user(self, entry_id: UUID, user_id: UUID) -> bool: ...


class RefreshSessionRepository(Protocol):
    async def add(self, session: RefreshSession) -> None: ...

    async def get_by_jti(self, jti: UUID) -> RefreshSession | None: ...

    async def consume(self, jti: UUID, *, now: datetime) -> bool:
        """Atomically mark an active, unexpired session as used."""
        ...

    async def revoke_family(self, family_id: UUID, *, now: datetime) -> None: ...
