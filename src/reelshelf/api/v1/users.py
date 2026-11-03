from typing import Annotated

from fastapi import APIRouter, Depends

from reelshelf.api.dependencies import get_current_user
from reelshelf.domain.entities import User
from reelshelf.schemas.auth import UserResponse
from reelshelf.schemas.errors import ErrorResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserResponse,
    responses={
        401: {"model": ErrorResponse},
    },
)
async def read_current_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    return UserResponse.model_validate(current_user)
