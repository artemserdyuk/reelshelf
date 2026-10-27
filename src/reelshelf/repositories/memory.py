import asyncio
from dataclasses import replace
from datetime import datetime
from uuid import UUID

from reelshelf.domain.entities import (
    EntryPage,
    EntryStatus,
    RefreshSession,
    User,
    WatchlistEntry,
)
from reelshelf.domain.errors import ConflictError, NotFoundError


class InMemoryUserRepository:
    def __init__(self) -> None:
        # Instance attributes: repositories do not share these dictionaries.
        self._users: dict[UUID, User] = {}
        self._username_index: dict[str, UUID] = {}

    async def add(self, user: User) -> None:
        # Validate both constraints before changing either dictionary.
        if user.id in self._users:
            raise ConflictError("User ID already exists.")

        if user.username in self._username_index:
            raise ConflictError("Username is already taken.")

        self._users[user.id] = replace(user)
        self._username_index[user.username] = user.id

    async def get_by_id(self, user_id: UUID) -> User | None:
        user = self._users.get(user_id)

        if user is None:
            return None

        # Return a separate value, not the stored instance.
        return replace(user)

    async def get_by_username(self, username: str) -> User | None:
        user_id = self._username_index.get(username)

        if user_id is None:
            return None

        return await self.get_by_id(user_id)


class InMemoryEntryRepository:
    def __init__(self) -> None:
        self._entries: dict[UUID, WatchlistEntry] = {}

    async def add(self, entry: WatchlistEntry) -> None:
        if entry.id in self._entries:
            raise ConflictError("Entry ID already exists.")

        self._entries[entry.id] = replace(entry)

    async def get_for_user(
        self,
        entry_id: UUID,
        user_id: UUID,
    ) -> WatchlistEntry | None:
        entry = self._entries.get(entry_id)

        # Do not reveal whether a foreign entry exists.
        if entry is None or entry.user_id != user_id:
            return None

        return replace(entry)

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        status: EntryStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> EntryPage:
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100.")

        if offset < 0:
            raise ValueError("offset must be non-negative.")

        # First apply owner and status filters.
        matching = [
            entry
            for entry in self._entries.values()
            if entry.user_id == user_id and (status is None or entry.status == status)
        ]

        # A stable tie-breaker makes pagination predictable.
        matching.sort(
            key=lambda entry: (entry.created_at, entry.id),
            reverse=True,
        )

        # Count before taking the requested page.
        total = len(matching)
        selected = matching[offset : offset + limit]

        return EntryPage(
            items=tuple(replace(entry) for entry in selected),
            total=total,
        )

    async def update(self, entry: WatchlistEntry) -> None:
        current = self._entries.get(entry.id)

        if current is None or current.user_id != entry.user_id:
            raise NotFoundError("Watchlist entry not found.")

        self._entries[entry.id] = replace(entry)

    async def delete_for_user(
        self,
        entry_id: UUID,
        user_id: UUID,
    ) -> bool:
        current = self._entries.get(entry_id)

        if current is None or current.user_id != user_id:
            return False

        del self._entries[entry_id]
        return True


class InMemoryRefreshSessionRepository:
    def __init__(self) -> None:
        self._sessions: dict[UUID, RefreshSession] = {}
        self._lock: asyncio.Lock = asyncio.Lock()

    async def add(self, session: RefreshSession) -> None:
        async with self._lock:
            if session.jti in self._sessions:
                raise ConflictError("Refresh session already exists.")

            self._sessions[session.jti] = replace(session)

    async def get_by_jti(self, jti: UUID) -> RefreshSession | None:
        async with self._lock:
            session = self._sessions.get(jti)

            if session is None:
                return None

            return replace(session)

    async def consume(
        self,
        jti: UUID,
        *,
        now: datetime,
    ) -> bool:
        # Checking and changing the session form one protected operation.
        async with self._lock:
            session = self._sessions.get(jti)

            if session is None:
                return False

            if (
                session.used_at is not None
                or session.revoked_at is not None
                or session.expires_at <= now
            ):
                return False

            self._sessions[jti] = replace(session, used_at=now)
            return True

    async def revoke_family(
        self,
        family_id: UUID,
        *,
        now: datetime,
    ) -> None:
        async with self._lock:
            for jti, session in self._sessions.items():
                if session.family_id == family_id and session.revoked_at is None:
                    self._sessions[jti] = replace(
                        session,
                        revoked_at=now,
                    )
