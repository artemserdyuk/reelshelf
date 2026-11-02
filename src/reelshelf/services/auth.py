from datetime import UTC, datetime
from uuid import uuid4

from reelshelf.domain.entities import User
from reelshelf.domain.errors import ConflictError
from reelshelf.domain.repositories import UserRepository
from reelshelf.domain.security import PasswordHasher


class AuthService:
    def __init__(
        self,
        users: UserRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        # Dependencies are supplied by the composition layer.
        self._users = users
        self._password_hasher = password_hasher

    async def register(
        self,
        *,
        username: str,
        password: str,
    ) -> User:
        """Register a user from validated, normalized input."""
        existing_user = await self._users.get_by_username(username)

        if existing_user is not None:
            raise ConflictError("Username is already taken.")

        password_hash = await self._password_hasher.hash(password)

        user = User(
            id=uuid4(),
            username=username,
            password_hash=password_hash,
            created_at=datetime.now(UTC),
        )

        # The repository also enforces uniqueness.
        await self._users.add(user)

        return user
