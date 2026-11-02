import pytest
from fastapi.testclient import TestClient


def test_registration_returns_public_user_data(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "  MovieFan  ",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["username"] == "moviefan"
    assert set(body) == {"id", "username", "created_at"}
    assert body["id"]
    assert body["created_at"]


def test_registration_rejects_normalized_duplicate(
    client: TestClient,
) -> None:
    first = client.post(
        "/api/v1/auth/register",
        json={
            "username": "MovieFan",
            "password": "StrongPassword123!",
        },
    )
    second = client.post(
        "/api/v1/auth/register",
        json={
            "username": "  MOVIEFAN  ",
            "password": "AnotherPassword123!",
        },
    )

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json() == {
        "error": {
            "code": "CONFLICT",
            "message": "Username is already taken.",
        }
    }


@pytest.mark.parametrize(
    "payload",
    [
        {"username": "  ab  ", "password": "StrongPassword123!"},
        {"username": "x" * 31, "password": "StrongPassword123!"},
        {"username": 123, "password": "StrongPassword123!"},
        {"username": "viewer", "password": "short"},
        {"username": "viewer", "password": "x" * 129},
        {"username": "viewer"},
        {
            "username": "viewer",
            "password": "StrongPassword123!",
            "is_admin": True,
        },
    ],
)
def test_registration_rejects_invalid_input(
    client: TestClient,
    payload: dict[str, object],
) -> None:
    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed.",
        }
    }


def test_openapi_documents_registration_responses(
    client: TestClient,
) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200

    operation = response.json()["paths"]["/api/v1/auth/register"]["post"]

    assert operation["responses"]["201"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/UserResponse")

    assert operation["responses"]["422"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/ErrorResponse")
