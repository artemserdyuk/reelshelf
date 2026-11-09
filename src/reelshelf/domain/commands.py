from typing import TypedDict

from reelshelf.domain.entities import EntryStatus


class EntryChanges(TypedDict, total=False):
    title: str
    release_year: int | None
    status: EntryStatus
    rating: int | None
