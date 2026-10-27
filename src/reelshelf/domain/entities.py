from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class EntryStatus(StrEnum):
    PLANNED = "planned"
    WATCHED = "watched"


@dataclass(frozen=True, slots=True, kw_only=True)
class User:
    id: UUID
    username: str
    # Keep the hash out of the generated object representation.
    password_hash: str = field(repr=False)
    created_at: datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class WatchlistEntry:
    id: UUID
    user_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    release_year: int | None = None
    status: EntryStatus = EntryStatus.PLANNED
    rating: int | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class RefreshSession:
    jti: UUID
    # Identifies a login session and its rotated tokens.
    family_id: UUID
    user_id: UUID
    expires_at: datetime
    used_at: datetime | None = None
    revoked_at: datetime | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class EntryPage:
    items: tuple[WatchlistEntry, ...]
    total: int
