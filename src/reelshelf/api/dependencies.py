from typing import Annotated, cast

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from reelshelf.bootstrap import Container
from reelshelf.domain.entities import User
from reelshelf.domain.errors import UnauthorizedError
from reelshelf.services.auth import AuthService

bearer_scheme = HTTPBearer(auto_error=False)


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
        tokens=container.tokens,
    )


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    if credentials is None:
        raise UnauthorizedError("Authentication required.")

    return await service.get_current_user(credentials.credentials)
