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
    return register_and_login(client, "entry-owner")


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


def test_owner_can_read_entry(
    client: TestClient,
    owner_headers: dict[str, str],
    created_entry: dict[str, object],
) -> None:
    response = client.get(
        f"/api/v1/entries/{created_entry['id']}",
        headers=owner_headers,
    )
    assert response.status_code == 200, response.text
    assert response.json() == created_entry


def test_foreign_and_missing_entries_have_same_response(
    client: TestClient,
    created_entry: dict[str, object],
) -> None:
    other_headers = register_and_login(client, "other-reader")
    foreign = client.get(
        f"/api/v1/entries/{created_entry['id']}",
        headers=other_headers,
    )
    missing = client.get(
        f"/api/v1/entries/{uuid4()}",
        headers=other_headers,
    )

    assert foreign.status_code == missing.status_code == 404
    expected = {
        "error": {
            "code": "NOT_FOUND",
            "message": "Watchlist entry not found.",
        }
    }
    assert foreign.json() == expected
    assert missing.json() == expected


@pytest.mark.parametrize("entry_id", ["not-a-uuid", "123"])
def test_invalid_entry_id_returns_422(
    client: TestClient,
    owner_headers: dict[str, str],
    entry_id: str,
) -> None:
    response = client.get(
        f"/api/v1/entries/{entry_id}",
        headers=owner_headers,
    )
    assert response.status_code == 422, response.text
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize(
    "headers",
    [{}, {"Authorization": "Bearer not-a-jwt"}],
)
def test_read_entry_requires_authentication(
    client: TestClient,
    created_entry: dict[str, object],
    headers: dict[str, str],
) -> None:
    response = client.get(
        f"/api/v1/entries/{created_entry['id']}",
        headers=headers,
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
    assert response.headers["www-authenticate"] == "Bearer"
