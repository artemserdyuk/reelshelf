from datetime import datetime
from typing import Annotated, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from reelshelf.domain.commands import EntryChanges
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


class UpdateEntryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: EntryTitle | None = None
    release_year: int | None = Field(default=None, ge=1888, le=2100, strict=True)
    status: EntryStatus | None = None
    rating: int | None = Field(default=None, ge=1, le=10, strict=True)

    @model_validator(mode="after")
    def validate_patch(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one field is required.")

        for name in ("title", "status"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"{name} must not be null.")

        return self

    def to_changes(self) -> EntryChanges:
        changes: EntryChanges = {}

        if self.title is not None:
            changes["title"] = self.title

        if self.status is not None:
            changes["status"] = self.status

        if "release_year" in self.model_fields_set:
            changes["release_year"] = self.release_year

        if "rating" in self.model_fields_set:
            changes["rating"] = self.rating

        return changes


class EntrySummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total: int = Field(ge=0)
    planned: int = Field(ge=0)
    watched: int = Field(ge=0)
    average_rating: float | None = Field(ge=1, le=10)
