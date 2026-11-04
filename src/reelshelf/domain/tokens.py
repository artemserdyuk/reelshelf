from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True, kw_only=True)
class RefreshClaims:
    user_id: UUID
    jti: UUID
    expires_at: datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class TokenPair:
    # Avoid printing credentials in the generated repr.
    access_token: str = field(repr=False)
    refresh_token: str = field(repr=False)
