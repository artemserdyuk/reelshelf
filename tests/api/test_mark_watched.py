from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


def register_and_login(client: TestClient, username: str) -> dict[str, str]:
    credentials = {"username": username, "password": "StrongPassword123!"}
    response = client.post("/api/v1/auth/register", json=credentials)
    assert response.status_code == 201, response.text

    response = client.post("/api/v1/auth/login", json=credentials)
    assert response.status_code == 200, response.text

    token = response.json()["access_token"]
    assert isinstance(token, str)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def owner_headers(client: TestClient) -> dict[str, str]:
    return register_and_login(client, "watched-owner")


@pytest.fixture
def created_entry(
    client: TestClient,
    owner_headers: dict[str, str],
) -> dict[str, object]:
    response = client.post(
        "/api/v1/entries",
        headers=owner_headers,
        json={"title": "Arrival", "release_year": 2016},
    )
    assert response.status_code == 201, response.text
    body: dict[str, object] = response.json()
    return body


def test_owner_can_mark_entry_watched(
    client: TestClient,
    owner_headers: dict[str, str],
    created_entry: dict[str, object],
) -> None:
    path = f"/api/v1/entries/{created_entry['id']}"

    response = client.post(f"{path}/watched", headers=owner_headers)
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["status"] == "watched"
    assert body["rating"] is None

    for field in ("id", "user_id", "title", "release_year", "created_at"):
        assert body[field] == created_entry[field]

    stored = client.get(path, headers=owner_headers)
    assert stored.status_code == 200, stored.text
    assert stored.json() == body


@pytest.mark.parametrize("rating", [None, 9])
def test_marking_watched_again_preserves_entry(
    client: TestClient,
    owner_headers: dict[str, str],
    created_entry: dict[str, object],
    rating: int | None,
) -> None:
    path = f"/api/v1/entries/{created_entry['id']}"

    prepared = client.patch(
        path,
        headers=owner_headers,
        json={"status": "watched", "rating": rating},
    )
    assert prepared.status_code == 200, prepared.text
    before = prepared.json()

    for _ in range(2):
        response = client.post(f"{path}/watched", headers=owner_headers)
        assert response.status_code == 200, response.text
        # Includes rating and updated_at: a repeated action changes neither.
        assert response.json() == before

    stored = client.get(path, headers=owner_headers)
    assert stored.status_code == 200, stored.text
    assert stored.json() == before


def test_foreign_and_missing_entries_return_same_error(
    client: TestClient,
    owner_headers: dict[str, str],
    created_entry: dict[str, object],
) -> None:
    other_headers = register_and_login(client, "watched-other")

    for entry_id in (created_entry["id"], str(uuid4())):
        response = client.post(
            f"/api/v1/entries/{entry_id}/watched",
            headers=other_headers,
        )
        assert response.status_code == 404, response.text
        assert response.json() == {
            "error": {
                "code": "NOT_FOUND",
                "message": "Watchlist entry not found.",
            }
        }

    stored = client.get(
        f"/api/v1/entries/{created_entry['id']}",
        headers=owner_headers,
    )
    assert stored.status_code == 200, stored.text
    assert stored.json() == created_entry


def test_invalid_id_returns_422(
    client: TestClient,
    owner_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/entries/not-a-uuid/watched",
        headers=owner_headers,
    )
    assert response.status_code == 422, response.text
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize(
    "headers",
    [{}, {"Authorization": "Bearer not-a-jwt"}],
)
def test_mark_watched_requires_authentication(
    client: TestClient,
    created_entry: dict[str, object],
    headers: dict[str, str],
) -> None:
    response = client.post(
        f"/api/v1/entries/{created_entry['id']}/watched",
        headers=headers,
    )
    assert response.status_code == 401, response.text
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
    assert response.headers["www-authenticate"] == "Bearer"
