from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from reelshelf.api.dependencies import get_auth_service
from reelshelf.domain.tokens import TokenPair
from reelshelf.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPairResponse,
    UserResponse,
)
from reelshelf.schemas.errors import ErrorResponse
from reelshelf.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def token_response(pair: TokenPair, response: Response) -> TokenPairResponse:
    # Both login and refresh return credentials.
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return TokenPairResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
    )


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
    responses={409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def register_user(
    body: RegisterRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    user = await service.register(
        username=body.username,
        password=body.password.get_secret_value(),
    )
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenPairResponse,
    responses={401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def login_user(
    body: LoginRequest,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenPairResponse:
    pair = await service.login(
        username=body.username,
        password=body.password.get_secret_value(),
    )
    return token_response(pair, response)


@router.post(
    "/refresh",
    response_model=TokenPairResponse,
    responses={401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def refresh_tokens(
    body: RefreshRequest,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenPairResponse:
    pair = await service.refresh(body.refresh_token.get_secret_value())
    return token_response(pair, response)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def logout_user(
    body: RefreshRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> Response:
    await service.logout(body.refresh_token.get_secret_value())
    return Response(status_code=status.HTTP_204_NO_CONTENT)
