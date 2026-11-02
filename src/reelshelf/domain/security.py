from typing import Protocol


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
