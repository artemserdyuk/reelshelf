from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from reelshelf.api.dependencies import get_auth_service
from reelshelf.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)
from reelshelf.schemas.errors import ErrorResponse
from reelshelf.services.auth import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
    responses={
        409: {
            "model": ErrorResponse,
            "description": "Username is already taken.",
        },
        422: {
            "model": ErrorResponse,
            "description": "Request validation failed.",
        },
    },
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
    response_model=AccessTokenResponse,
    responses={
        401: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def login_user(
    body: LoginRequest,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> AccessTokenResponse:
    token = await service.login(
        username=body.username,
        password=body.password.get_secret_value(),
    )

    # Responses containing credentials should not be cached.
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"

    return AccessTokenResponse(access_token=token)
