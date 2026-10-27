from dataclasses import dataclass

from reelshelf.domain.repositories import (
    EntryRepository,
    RefreshSessionRepository,
    UserRepository,
)
from reelshelf.repositories.memory import (
    InMemoryEntryRepository,
    InMemoryRefreshSessionRepository,
    InMemoryUserRepository,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class Container:
    # Type fields by contracts, not concrete storage classes.
    users: UserRepository
    entries: EntryRepository
    refresh_sessions: RefreshSessionRepository


def build_container() -> Container:
    # Select concrete implementations in one place.
    return Container(
        users=InMemoryUserRepository(),
        entries=InMemoryEntryRepository(),
        refresh_sessions=InMemoryRefreshSessionRepository(),
    )
