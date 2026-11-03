from dataclasses import dataclass

from reelshelf.core.config import Settings
from reelshelf.domain.repositories import (
    EntryRepository,
    RefreshSessionRepository,
    UserRepository,
)
from reelshelf.domain.security import AccessTokenCodec, PasswordHasher
from reelshelf.repositories.memory import (
    InMemoryEntryRepository,
    InMemoryRefreshSessionRepository,
    InMemoryUserRepository,
)
from reelshelf.security.passwords import Argon2PasswordHasher
from reelshelf.security.tokens import JWTAccessTokenCodec


@dataclass(frozen=True, slots=True, kw_only=True)
class Container:
    # Type fields by contracts, not concrete storage classes.
    users: UserRepository
    entries: EntryRepository
    refresh_sessions: RefreshSessionRepository
    password_hasher: PasswordHasher
    tokens: AccessTokenCodec


def build_container(settings: Settings) -> Container:
    # Select concrete implementations in one place.
    return Container(
        users=InMemoryUserRepository(),
        entries=InMemoryEntryRepository(),
        refresh_sessions=InMemoryRefreshSessionRepository(),
        password_hasher=Argon2PasswordHasher(),
        tokens=JWTAccessTokenCodec(
            secret=settings.jwt_secret.get_secret_value(),
            access_token_minutes=settings.access_token_minutes,
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
        ),
    )
