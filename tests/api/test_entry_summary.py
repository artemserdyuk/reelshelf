from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from reelshelf.bootstrap import Container
from reelshelf.domain.entities import EntryStatus, WatchlistEntry


@pytest.mark.parametrize(
    ("planned", "ratings", "average"),
    [
        (0, [], None),
        (2, [None], None),
        (1, [8, 9, None], 8.5),
        (101, [10], 10.0),
    ],
)
async def test_summary_counts_all_owned_entries(
    app: FastAPI,
    client: TestClient,
    planned: int,
    ratings: list[int | None],
    average: float | None,
) -> None:
    credentials = {"username": "summary-viewer", "password": "StrongPassword123!"}
    registered = client.post("/api/v1/auth/register", json=credentials)
    assert registered.status_code == 201, registered.text
    owner_id = UUID(registered.json()["id"])

    logged_in = client.post("/api/v1/auth/login", json=credentials)
    assert logged_in.status_code == 200, logged_in.text
    headers = {"Authorization": f"Bearer {logged_in.json()['access_token']}"}

    container = cast(Container, app.state.container)
    now = datetime.now(UTC)

    entries: list[tuple[UUID, EntryStatus, int | None]] = [
        (owner_id, EntryStatus.PLANNED, None) for _ in range(planned)
    ]
    entries.extend((owner_id, EntryStatus.WATCHED, rating) for rating in ratings)

    # Foreign data must not affect counts or the average.
    entries.append((uuid4(), EntryStatus.WATCHED, 1))

    for user_id, status, rating in entries:
        await container.entries.add(
            WatchlistEntry(
                id=uuid4(),
                user_id=user_id,
                title="Summary test movie",
                status=status,
                rating=rating,
                created_at=now,
                updated_at=now,
            )
        )

    response = client.get("/api/v1/entries/summary", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json() == {
        "total": planned + len(ratings),
        "planned": planned,
        "watched": len(ratings),
        "average_rating": average,
    }


def test_summary_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/entries/summary")

    assert response.status_code == 401, response.text
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
    assert response.headers["www-authenticate"] == "Bearer"
