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
    headers = login(client, "patch-owner")
    response = client.post(
        "/api/v1/entries",
        headers=headers,
        json={"title": "Arrival", "release_year": 2016},
    )
    assert response.status_code == 201, response.text
    body: dict[str, object] = response.json()
    return f"/api/v1/entries/{body['id']}", headers, body


def test_partial_update_and_noop(
    client: TestClient,
    entry: tuple[str, dict[str, str], dict[str, object]],
) -> None:
    url, headers, original = entry

    response = client.patch(url, headers=headers, json={"title": "  Dune  "})
    assert response.status_code == 200, response.text
    updated = response.json()

    assert updated["title"] == "Dune"
    for field in ("id", "user_id", "created_at", "release_year", "status", "rating"):
        assert updated[field] == original[field]

    original_time = original["updated_at"]
    assert isinstance(original_time, str)
    assert updated["updated_at"] >= original_time
    assert client.get(url, headers=headers).json() == updated

    repeated = client.patch(url, headers=headers, json={"title": "Dune"})
    assert repeated.status_code == 200
    assert repeated.json() == updated


def test_status_rating_and_explicit_null(
    client: TestClient,
    entry: tuple[str, dict[str, str], dict[str, object]],
) -> None:
    url, headers, _ = entry

    response = client.patch(
        url, headers=headers, json={"status": "watched", "rating": 9}
    )
    assert response.status_code == 200, response.text
    watched = response.json()
    assert watched["status"] == "watched"
    assert watched["rating"] == 9

    rejected = client.patch(url, headers=headers, json={"status": "planned"})
    assert rejected.status_code == 422
    assert client.get(url, headers=headers).json() == watched

    response = client.patch(
        url,
        headers=headers,
        json={"status": "planned", "rating": None, "release_year": None},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "planned"
    assert body["rating"] is None
    assert body["release_year"] is None
    assert client.get(url, headers=headers).json() == body


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": None},
        {"title": "   "},
        {"title": "x" * 201},
        {"status": None},
        {"status": "unknown"},
        {"rating": 0},
        {"rating": 11},
        {"rating": True},
        {"rating": "9"},
        {"rating": 9},
        {"release_year": 1887},
        {"release_year": 2101},
        {"release_year": "2016"},
        {"user_id": str(uuid4())},
        {"id": str(uuid4())},
        {"created_at": "2026-01-01T00:00:00Z"},
    ],
)
def test_invalid_patch_does_not_change_entry(
    client: TestClient,
    entry: tuple[str, dict[str, str], dict[str, object]],
    payload: dict[str, object],
) -> None:
    url, headers, original = entry

    response = client.patch(url, headers=headers, json=payload)

    assert response.status_code == 422, response.text
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert client.get(url, headers=headers).json() == original


def test_foreign_and_missing_entries(
    client: TestClient,
    entry: tuple[str, dict[str, str], dict[str, object]],
) -> None:
    url, owner_headers, original = entry
    other_headers = login(client, "patch-other")

    foreign = client.patch(url, headers=other_headers, json={"title": "Changed"})
    missing = client.patch(
        f"/api/v1/entries/{uuid4()}",
        headers=other_headers,
        json={"title": "Changed"},
    )

    assert foreign.status_code == missing.status_code == 404
    assert foreign.json() == missing.json()
    assert client.get(url, headers=owner_headers).json() == original


def test_authentication_and_path_validation(
    client: TestClient,
    entry: tuple[str, dict[str, str], dict[str, object]],
) -> None:
    url, headers, original = entry

    response = client.patch(url, json={"title": "Changed"})
    assert response.status_code == 401

    response = client.patch(
        "/api/v1/entries/not-a-uuid",
        headers=headers,
        json={"title": "Changed"},
    )
    assert response.status_code == 422
    assert client.get(url, headers=headers).json() == original
