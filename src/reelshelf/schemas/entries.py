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
