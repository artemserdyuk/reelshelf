from typing import Annotated

from fastapi import APIRouter, Depends, status

from reelshelf.api.dependencies import get_current_user, get_entry_service
from reelshelf.domain.entities import User
from reelshelf.schemas.entries import CreateEntryRequest, EntryResponse
from reelshelf.schemas.errors import ErrorResponse
from reelshelf.services.entries import EntryService

router = APIRouter(prefix="/entries", tags=["entries"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=EntryResponse,
    responses={
        401: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def create_entry(
    body: CreateEntryRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[EntryService, Depends(get_entry_service)],
) -> EntryResponse:
    entry = await service.create(
        user_id=current_user.id,
        title=body.title,
        release_year=body.release_year,
    )
    return EntryResponse.model_validate(entry)
