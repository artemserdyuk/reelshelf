from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from reelshelf.domain.entities import EntryStatus

EntryTitle = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=200),
]


class CreateEntryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: EntryTitle
    release_year: int | None = Field(default=None, ge=1888, le=2100, strict=True)


class EntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    release_year: int | None
    status: EntryStatus
    rating: int | None
    created_at: datetime
    updated_at: datetime


class EntryListQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: EntryStatus | None = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class EntryPageResponse(BaseModel):
    items: list[EntryResponse]
    total: int
    limit: int
    offset: int
