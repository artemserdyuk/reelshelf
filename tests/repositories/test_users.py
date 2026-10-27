from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from reelshelf.domain.entities import User
from reelshelf.domain.errors import ConflictError
from reelshelf.repositories.memory import InMemoryUserRepository


@pytest.fixture
def user() -> User:
    return User(
        id=uuid4(),
        username="viewer",
        password_hash="test-hash",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


async def test_add_and_find_user(user: User) -> None:
    repository = InMemoryUserRepository()

    await repository.add(user)

    by_id = await repository.get_by_id(user.id)
    by_username = await repository.get_by_username(user.username)

    assert by_id == user
    assert by_username == user

    # Equal values, different instances.
    assert by_id is not user


async def test_missing_user_returns_none() -> None:
    repository = InMemoryUserRepository()

    assert await repository.get_by_id(uuid4()) is None
    assert await repository.get_by_username("missing") is None


async def test_duplicate_username_is_rejected(user: User) -> None:
    repository = InMemoryUserRepository()
    await repository.add(user)

    duplicate = replace(user, id=uuid4())

    with pytest.raises(ConflictError, match="Username"):
        await repository.add(duplicate)

    # A failed operation must not partially save the duplicate.
    assert await repository.get_by_id(duplicate.id) is None
    assert await repository.get_by_username(user.username) == user


async def test_duplicate_id_is_rejected(user: User) -> None:
    repository = InMemoryUserRepository()
    await repository.add(user)

    duplicate = replace(user, username="another-viewer")

    with pytest.raises(ConflictError, match="User ID"):
        await repository.add(duplicate)

    assert await repository.get_by_username("another-viewer") is None


async def test_repository_instances_are_isolated(user: User) -> None:
    first = InMemoryUserRepository()
    second = InMemoryUserRepository()

    await first.add(user)

    assert await first.get_by_id(user.id) == user
    assert await second.get_by_id(user.id) is None
