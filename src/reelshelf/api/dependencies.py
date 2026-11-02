from typing import Annotated, cast

from fastapi import Depends, Request

from reelshelf.bootstrap import Container
from reelshelf.services.auth import AuthService


async def get_container(request: Request) -> Container:
    # Reuse the container created by create_app().
    return cast(Container, request.app.state.container)


async def get_auth_service(
    container: Annotated[Container, Depends(get_container)],
) -> AuthService:
    # This service uses the existing application-wide repositories.
    return AuthService(
        users=container.users,
        password_hasher=container.password_hasher,
    )