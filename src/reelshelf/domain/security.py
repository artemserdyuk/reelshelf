from typing import Protocol
from uuid import UUID

from reelshelf.domain.tokens import RefreshClaims


class PasswordHasher(Protocol):
    async def hash(self, password: str) -> str:
        """Create an encoded password hash."""
        ...

    async def verify(
        self,
        password: str,
        password_hash: str,
    ) -> bool:
        """Check a password against a previously stored hash."""
        ...


class AccessTokenCodec(Protocol):
    def create(self, user_id: UUID) -> str:
        """Create a signed access token."""
        ...

    def decode(self, token: str) -> UUID:
        """Validate a token and return its subject as a UUID."""
        ...


class RefreshTokenCodec(Protocol):
    def create(self, claims: RefreshClaims) -> str:
        """Create a signed refresh token."""
        ...

    def decode(self, token: str) -> RefreshClaims:
        """Validate a token and return its claims as a RefreshClaims instance."""
        ...
