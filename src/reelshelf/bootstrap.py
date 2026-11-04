from dataclasses import dataclass
from datetime import timedelta

from reelshelf.core.config import Settings
from reelshelf.domain.repositories import (
    EntryRepository,
    RefreshSessionRepository,
    UserRepository,
)
from reelshelf.domain.security import (
    AccessTokenCodec,
    PasswordHasher,
    RefreshTokenCodec,
)
from reelshelf.repositories.memory import (
    InMemoryEntryRepository,
    InMemoryRefreshSessionRepository,
    InMemoryUserRepository,
)
from reelshelf.security.passwords import Argon2PasswordHasher
from reelshelf.security.refresh_tokens import JWTRefreshTokenCodec
from reelshelf.security.tokens import JWTAccessTokenCodec


@dataclass(frozen=True, slots=True, kw_only=True)
class Container:
    users: UserRepository
    entries: EntryRepository
    refresh_sessions: RefreshSessionRepository
    password_hasher: PasswordHasher
    tokens: AccessTokenCodec
    refresh_tokens: RefreshTokenCodec
    refresh_lifetime: timedelta


def build_container(settings: Settings) -> Container:
    secret = settings.jwt_secret.get_secret_value()

    return Container(
        users=InMemoryUserRepository(),
        entries=InMemoryEntryRepository(),
        refresh_sessions=InMemoryRefreshSessionRepository(),
        password_hasher=Argon2PasswordHasher(),
        tokens=JWTAccessTokenCodec(
            secret=secret,
            access_token_minutes=settings.access_token_minutes,
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
        ),
        refresh_tokens=JWTRefreshTokenCodec(
            secret=secret,
            issuer=settings.jwt_issuer,
            audience=f"{settings.jwt_audience}:refresh",
        ),
        refresh_lifetime=timedelta(days=settings.refresh_token_days),
    )
