from datetime import UTC, datetime
from uuid import uuid4

from reelshelf.domain.entities import User
from reelshelf.domain.errors import ConflictError, UnauthorizedError
from reelshelf.domain.repositories import UserRepository
from reelshelf.domain.security import AccessTokenCodec, PasswordHasher

DUMMY_PASSWORD = "dummy-password-not-used-for-login"


class AuthService:
    def __init__(
        self,
        users: UserRepository,
        password_hasher: PasswordHasher,
        tokens: AccessTokenCodec,
    ) -> None:
        # Dependencies are supplied by the composition layer.
        self._users = users
        self._password_hasher = password_hasher
        self._tokens = tokens

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

    async def login(
        self,
        *,
        username: str,
        password: str,
    ) -> str:
        user = await self._users.get_by_username(username)

        if user is None:
            raise UnauthorizedError("Invalid credentials.")

        password_matches = await self._password_hasher.verify(
            password,
            user.password_hash,
        )

        if not password_matches:
            raise UnauthorizedError("Invalid credentials.")

        return self._tokens.create(user.id)

    async def get_current_user(self, token: str) -> User:
        user_id = self._tokens.decode(token)

        user = await self._users.get_by_id(user_id)

        if user is None:
            raise UnauthorizedError("Invalid or expired access token.")

        return user
