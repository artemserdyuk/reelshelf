from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from reelshelf.domain.entities import RefreshSession, User
from reelshelf.domain.errors import ConflictError, UnauthorizedError
from reelshelf.domain.repositories import RefreshSessionRepository, UserRepository
from reelshelf.domain.security import (
    AccessTokenCodec,
    PasswordHasher,
    RefreshTokenCodec,
)
from reelshelf.domain.tokens import RefreshClaims, TokenPair


class AuthService:
    def __init__(
        self,
        users: UserRepository,
        password_hasher: PasswordHasher,
        tokens: AccessTokenCodec,
        refresh_tokens: RefreshTokenCodec,
        sessions: RefreshSessionRepository,
        refresh_lifetime: timedelta,
    ) -> None:
        self._users = users
        self._password_hasher = password_hasher
        self._tokens = tokens
        self._refresh_tokens = refresh_tokens
        self._sessions = sessions
        self._refresh_lifetime = refresh_lifetime

    async def register(self, *, username: str, password: str) -> User:
        if await self._users.get_by_username(username) is not None:
            raise ConflictError("Username is already taken.")

        password_hash = await self._password_hasher.hash(password)
        user = User(
            id=uuid4(),
            username=username,
            password_hash=password_hash,
            created_at=datetime.now(UTC),
        )
        await self._users.add(user)
        return user

    def _prepare_pair(
        self,
        *,
        user_id: UUID,
        refresh_jti: UUID,
        expires_at: datetime,
    ) -> TokenPair:
        # Prepare both strings before committing any session changes.
        claims = RefreshClaims(
            user_id=user_id,
            jti=refresh_jti,
            expires_at=expires_at,
        )
        return TokenPair(
            access_token=self._tokens.create(user_id),
            refresh_token=self._refresh_tokens.create(claims),
        )

    async def login(self, *, username: str, password: str) -> TokenPair:
        user = await self._users.get_by_username(username)
        if user is None:
            raise UnauthorizedError("Invalid credentials.")

        if not await self._password_hasher.verify(password, user.password_hash):
            raise UnauthorizedError("Invalid credentials.")

        # JWT timestamps use seconds. Keep storage and JWT expiry identical.
        now = datetime.now(UTC).replace(microsecond=0)
        session = RefreshSession(
            jti=uuid4(),
            family_id=uuid4(),
            user_id=user.id,
            expires_at=now + self._refresh_lifetime,
        )
        pair = self._prepare_pair(
            user_id=user.id,
            refresh_jti=session.jti,
            expires_at=session.expires_at,
        )
        await self._sessions.add(session)
        return pair

    async def refresh(self, token: str) -> TokenPair:
        claims = self._refresh_tokens.decode(token)

        if await self._users.get_by_id(claims.user_id) is None:
            raise UnauthorizedError("Invalid or expired refresh token.")

        new_jti = uuid4()
        pair = self._prepare_pair(
            user_id=claims.user_id,
            refresh_jti=new_jti,
            expires_at=claims.expires_at,
        )

        rotated = await self._sessions.rotate(
            claims.jti,
            user_id=claims.user_id,
            new_jti=new_jti,
            now=datetime.now(UTC),
        )
        if not rotated:
            raise UnauthorizedError("Invalid or expired refresh token.")

        return pair

    async def logout(self, token: str) -> None:
        claims = self._refresh_tokens.decode(token)
        revoked = await self._sessions.logout(
            claims.jti,
            user_id=claims.user_id,
            now=datetime.now(UTC),
        )
        if not revoked:
            raise UnauthorizedError("Invalid or expired refresh token.")

    async def get_current_user(self, token: str) -> User:
        user_id = self._tokens.decode(token)
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError("Invalid or expired access token.")
        return user
