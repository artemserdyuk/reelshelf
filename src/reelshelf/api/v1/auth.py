from typing import Annotated

from fastapi import APIRouter, Depends, status

from reelshelf.api.dependencies import get_auth_service
from reelshelf.schemas.auth import RegisterRequest, UserResponse
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