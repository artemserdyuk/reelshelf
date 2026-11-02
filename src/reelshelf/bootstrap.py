from dataclasses import dataclass

from reelshelf.domain.repositories import (
    EntryRepository,
    RefreshSessionRepository,
    UserRepository,
)
from reelshelf.domain.security import PasswordHasher
from reelshelf.repositories.memory import (
    InMemoryEntryRepository,
    InMemoryRefreshSessionRepository,
    InMemoryUserRepository,
)
from reelshelf.security.passwords import Argon2PasswordHasher


@dataclass(frozen=True, slots=True, kw_only=True)
class Container:
    # Type fields by contracts, not concrete storage classes.
    users: UserRepository
    entries: EntryRepository
    refresh_sessions: RefreshSessionRepository
    password_hasher: PasswordHasher


def build_container() -> Container:
    # Select concrete implementations in one place.
    return Container(
        users=InMemoryUserRepository(),
        entries=InMemoryEntryRepository(),
        refresh_sessions=InMemoryRefreshSessionRepository(),
        password_hasher=Argon2PasswordHasher(),
    )