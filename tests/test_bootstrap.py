from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from reelshelf.bootstrap import Container
from reelshelf.core.config import Settings
from reelshelf.domain.entities import User
from reelshelf.main import create_app


async def test_app_instances_have_independent_storage(
    settings: Settings,
) -> None:
    first_app = create_app(settings=settings)
    second_app = create_app(settings=settings)

    # app.state is dynamic; tell mypy the expected stored type.
    first = cast(Container, first_app.state.container)
    second = cast(Container, second_app.state.container)

    user = User(
        id=uuid4(),
        username="viewer",
        password_hash="test-hash",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    await first.users.add(user)

    assert first is not second
    assert await first.users.get_by_id(user.id) == user
    assert await second.users.get_by_id(user.id) is None
