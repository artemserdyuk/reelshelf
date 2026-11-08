from typing import cast
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from reelshelf.bootstrap import Container


@pytest.fixture
def logged_in_user(client: TestClient) -> tuple[str, dict[str, str]]:
    credentials = {"username": "movie-viewer", "password": "StrongPassword123!"}
    registered = client.post("/api/v1/auth/register", json=credentials)
    assert registered.status_code == 201, registered.text
    user_id = registered.json()["id"]
    assert isinstance(user_id, str)

    login = client.post("/api/v1/auth/login", json=credentials)
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    assert isinstance(token, str)
    return user_id, {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize("release_year", [None, 2016])
async def test_create_entry_is_saved_for_current_user(
    client: TestClient,
    app: FastAPI,
    logged_in_user: tuple[str, dict[str, str]],
    release_year: int | None,
) -> None:
    user_id, headers = logged_in_user
    payload: dict[str, object] = {"title": "  Arrival  "}
    if release_year is not None:
        payload["release_year"] = release_year

    response = client.post("/api/v1/entries", json=payload, headers=headers)

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["title"] == "Arrival"
    assert body["user_id"] == user_id
    assert body["release_year"] == release_year
    assert body["status"] == "planned"
    assert body["rating"] is None
    assert body["created_at"] == body["updated_at"]

    container = cast(Container, app.state.container)
    entry_id = UUID(body["id"])
    saved = await container.entries.get_for_user(entry_id, UUID(user_id))
    assert saved is not None
    assert saved.title == "Arrival"
    assert saved.release_year == release_year
    assert saved.created_at.tzinfo is not None
    assert await container.entries.get_for_user(entry_id, uuid4()) is None


def test_create_entry_requires_login(client: TestClient) -> None:
    response = client.post("/api/v1/entries", json={"title": "Arrival"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": ""},
        {"title": "   "},
        {"title": "x" * 201},
        {"title": "Arrival", "release_year": 1887},
        {"title": "Arrival", "release_year": 2101},
        {"title": "Arrival", "release_year": "2016"},
        {"title": "Arrival", "release_year": True},
        {"title": "Arrival", "user_id": str(uuid4())},
        {"title": "Arrival", "status": "watched"},
        {"title": "Arrival", "rating": 9},
    ],
)
async def test_invalid_entry_is_not_saved(
    client: TestClient,
    app: FastAPI,
    logged_in_user: tuple[str, dict[str, str]],
    payload: dict[str, object],
) -> None:
    user_id, headers = logged_in_user
    response = client.post("/api/v1/entries", json=payload, headers=headers)

    assert response.status_code == 422, response.text
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    container = cast(Container, app.state.container)
    page = await container.entries.list_for_user(UUID(user_id))
    assert page.total == 0
