from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


def login(client: TestClient, username: str) -> dict[str, str]:
    credentials = {"username": username, "password": "StrongPassword123!"}
    response = client.post("/api/v1/auth/register", json=credentials)
    assert response.status_code == 201, response.text

    response = client.post("/api/v1/auth/login", json=credentials)
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    assert isinstance(token, str)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def entry(
    client: TestClient,
) -> tuple[str, dict[str, str], dict[str, object]]:
    headers = login(client, "delete-owner")
    response = client.post(
        "/api/v1/entries",
        headers=headers,
        json={"title": "Arrival", "release_year": 2016},
    )
    assert response.status_code == 201, response.text
    body: dict[str, object] = response.json()
    return f"/api/v1/entries/{body['id']}", headers, body


def test_owner_deletes_only_requested_entry(
    client: TestClient,
    entry: tuple[str, dict[str, str], dict[str, object]],
) -> None:
    url, headers, _ = entry

    second = client.post("/api/v1/entries", headers=headers, json={"title": "Dune"})
    assert second.status_code == 201
    second_body = second.json()

    response = client.delete(url, headers=headers)
    assert response.status_code == 204, response.text
    assert response.content == b""

    missing = client.get(url, headers=headers)
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "NOT_FOUND"

    page = client.get("/api/v1/entries", headers=headers)
    assert page.status_code == 200
    assert page.json()["total"] == 1
    assert page.json()["items"] == [second_body]


def test_repeated_delete_returns_404(
    client: TestClient,
    entry: tuple[str, dict[str, str], dict[str, object]],
) -> None:
    url, headers, _ = entry

    assert client.delete(url, headers=headers).status_code == 204

    repeated = client.delete(url, headers=headers)
    assert repeated.status_code == 404
    assert repeated.json() == {
        "error": {"code": "NOT_FOUND", "message": "Watchlist entry not found."}
    }


def test_foreign_and_missing_entries_are_indistinguishable(
    client: TestClient,
    entry: tuple[str, dict[str, str], dict[str, object]],
) -> None:
    url, owner_headers, original = entry
    other_headers = login(client, "delete-other")

    foreign = client.delete(url, headers=other_headers)
    missing = client.delete(f"/api/v1/entries/{uuid4()}", headers=other_headers)

    assert foreign.status_code == missing.status_code == 404
    assert foreign.json() == missing.json()

    saved = client.get(url, headers=owner_headers)
    assert saved.status_code == 200
    assert saved.json() == original


@pytest.mark.parametrize("entry_id", ["not-a-uuid", "123"])
def test_invalid_id_returns_422(
    client: TestClient,
    entry: tuple[str, dict[str, str], dict[str, object]],
    entry_id: str,
) -> None:
    url, headers, original = entry

    response = client.delete(f"/api/v1/entries/{entry_id}", headers=headers)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert client.get(url, headers=headers).json() == original


@pytest.mark.parametrize(
    "headers",
    [{}, {"Authorization": "Bearer not-a-jwt"}],
)
def test_delete_requires_authentication(
    client: TestClient,
    entry: tuple[str, dict[str, str], dict[str, object]],
    headers: dict[str, str],
) -> None:
    url, owner_headers, original = entry

    response = client.delete(url, headers=headers)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
    assert response.headers["www-authenticate"] == "Bearer"
    assert client.get(url, headers=owner_headers).json() == original
