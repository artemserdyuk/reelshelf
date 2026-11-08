from datetime import UTC, datetime
from typing import cast
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from reelshelf.bootstrap import Container
from reelshelf.domain.entities import EntryStatus, WatchlistEntry


@pytest.fixture
def headers(client: TestClient) -> dict[str, str]:
    credentials = {"username": "list-viewer", "password": "StrongPassword123!"}
    response = client.post("/api/v1/auth/register", json=credentials)
    assert response.status_code == 201, response.text
    response = client.post("/api/v1/auth/login", json=credentials)
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    assert isinstance(token, str)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def seeded_entries(
    app: FastAPI,
    client: TestClient,
    headers: dict[str, str],
) -> None:
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    owner_id = UUID(response.json()["id"])
    foreign = client.post(
        "/api/v1/auth/register",
        json={"username": "other-viewer", "password": "StrongPassword123!"},
    )
    assert foreign.status_code == 201
    foreign_id = UUID(foreign.json()["id"])
    container = cast(Container, app.state.container)
    now = datetime(2026, 1, 1, tzinfo=UTC)

    # Equal timestamps make the ID tie-breaker observable.
    for number, owner, entry_status in [
        (1, owner_id, EntryStatus.PLANNED),
        (2, owner_id, EntryStatus.WATCHED),
        (3, owner_id, EntryStatus.PLANNED),
        (4, foreign_id, EntryStatus.PLANNED),
    ]:
        await container.entries.add(
            WatchlistEntry(
                id=UUID(int=number),
                user_id=owner,
                title=f"Movie {number}",
                status=entry_status,
                created_at=now,
                updated_at=now,
            )
        )


def test_empty_list(client: TestClient, headers: dict[str, str]) -> None:
    response = client.get("/api/v1/entries", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json() == {"items": [], "total": 0, "limit": 20, "offset": 0}


@pytest.mark.usefixtures("seeded_entries")
@pytest.mark.parametrize(
    ("query", "titles", "total", "limit", "offset"),
    [
        ("", ["Movie 3", "Movie 2", "Movie 1"], 3, 20, 0),
        ("?limit=1&offset=1", ["Movie 2"], 3, 1, 1),
        ("?status=planned&limit=1&offset=1", ["Movie 1"], 2, 1, 1),
        ("?status=watched", ["Movie 2"], 1, 20, 0),
        ("?offset=10", [], 3, 20, 10),
        ("?limit=100", ["Movie 3", "Movie 2", "Movie 1"], 3, 100, 0),
    ],
)
def test_list_filters_orders_and_paginates(
    client: TestClient,
    headers: dict[str, str],
    query: str,
    titles: list[str],
    total: int,
    limit: int,
    offset: int,
) -> None:
    response = client.get(f"/api/v1/entries{query}", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert [item["title"] for item in body["items"]] == titles
    assert body["total"] == total
    assert body["limit"] == limit
    assert body["offset"] == offset


@pytest.mark.parametrize(
    "query",
    [
        "?limit=0",
        "?limit=101",
        "?limit=abc",
        "?offset=-1",
        "?offset=abc",
        "?status=unknown",
        "?user_id=someone",
    ],
)
def test_invalid_query(
    client: TestClient,
    headers: dict[str, str],
    query: str,
) -> None:
    response = client.get(f"/api/v1/entries{query}", headers=headers)
    assert response.status_code == 422, response.text
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_list_requires_login(client: TestClient) -> None:
    response = client.get("/api/v1/entries")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
