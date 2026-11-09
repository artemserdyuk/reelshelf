from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from reelshelf.api.dependencies import get_current_user, get_entry_service
from reelshelf.domain.entities import User
from reelshelf.schemas.entries import (
    CreateEntryRequest,
    EntryListQuery,
    EntryPageResponse,
    EntryResponse,
    UpdateEntryRequest,
)
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


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=EntryPageResponse,
    responses={
        401: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def get_list_entries(
    query: Annotated[EntryListQuery, Query()],
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[EntryService, Depends(get_entry_service)],
) -> EntryPageResponse:
    page = await service.list_for_user(
        user_id=current_user.id,
        status=query.status,
        limit=query.limit,
        offset=query.offset,
    )
    return EntryPageResponse(
        items=[EntryResponse.model_validate(entry) for entry in page.items],
        total=page.total,
        limit=query.limit,
        offset=query.offset,
    )


@router.get(
    "/{entry_id}",
    status_code=status.HTTP_200_OK,
    response_model=EntryResponse,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def get_entry(
    entry_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[EntryService, Depends(get_entry_service)],
) -> EntryResponse:
    entry = await service.get_for_user(
        entry_id=entry_id,
        user_id=current_user.id,
    )
    return EntryResponse.model_validate(entry)


@router.patch(
    "/{entry_id}",
    response_model=EntryResponse,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def update_entry(
    entry_id: UUID,
    body: UpdateEntryRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[EntryService, Depends(get_entry_service)],
) -> EntryResponse:
    entry = await service.update(
        entry_id=entry_id,
        user_id=current_user.id,
        changes=body.to_changes(),
    )
    return EntryResponse.model_validate(entry)


@router.delete(
    "/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def delete_entry(
    entry_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[EntryService, Depends(get_entry_service)],
) -> Response:
    await service.delete_for_user(
        entry_id=entry_id,
        user_id=current_user.id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
