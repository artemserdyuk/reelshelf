from datetime import UTC, datetime
from typing import cast
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from reelshelf.bootstrap import build_container
from reelshelf.core.config import Settings
from reelshelf.domain.entities import User
from reelshelf.domain.errors import ConflictError
from reelshelf.domain.security import PasswordHasher
from reelshelf.repositories.memory import InMemoryUserRepository
from reelshelf.services.auth import AuthService


async def test_register_saves_hashed_password(settings: Settings) -> None:
    users = InMemoryUserRepository()

    hasher_mock = AsyncMock(spec=PasswordHasher)
    hasher_mock.hash.return_value = "encoded-test-hash"

    container = build_container(settings)

    service = AuthService(
        users=users,
        password_hasher=cast(PasswordHasher, hasher_mock),
        tokens=container.tokens,
        refresh_tokens=container.refresh_tokens,
        sessions=container.refresh_sessions,
        refresh_lifetime=container.refresh_lifetime,
    )

    user = await service.register(
        username="viewer",
        password="StrongPassword123!",
    )

    stored = await users.get_by_username("viewer")

    assert stored == user
    assert user.password_hash == "encoded-test-hash"
    assert user.created_at.tzinfo is not None

    hasher_mock.hash.assert_awaited_once_with("StrongPassword123!")


async def test_register_rejects_existing_username_before_hashing(
    settings: Settings,
) -> None:
    users = InMemoryUserRepository()

    existing = User(
        id=uuid4(),
        username="viewer",
        password_hash="existing-hash",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    await users.add(existing)

    hasher_mock = AsyncMock(spec=PasswordHasher)

    container = build_container(settings)
    service = AuthService(
        users=users,
        password_hasher=cast(PasswordHasher, hasher_mock),
        tokens=container.tokens,
        refresh_tokens=container.refresh_tokens,
        sessions=container.refresh_sessions,
        refresh_lifetime=container.refresh_lifetime,
    )

    with pytest.raises(ConflictError, match="Username is already taken"):
        await service.register(
            username="viewer",
            password="StrongPassword123!",
        )

    hasher_mock.hash.assert_not_awaited()
    assert await users.get_by_username("viewer") == existing
