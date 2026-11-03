from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient

from reelshelf.core.config import Settings


def register_user(client: TestClient, username: str = "viewer") -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "password": "StrongPassword123!",
        },
    )
    assert response.status_code == 201

    user_id = response.json()["id"]
    assert isinstance(user_id, str)
    return user_id


def login_user(client: TestClient, username: str = "viewer") -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": username,
            "password": "StrongPassword123!",
        },
    )
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.headers["cache-control"] == "no-store"

    token = response.json()["access_token"]
    assert isinstance(token, str)
    return token


def test_login_and_me_return_registered_user(client: TestClient) -> None:
    user_id = register_user(client)
    token = login_user(client, "  VIEWER  ")

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == user_id
    assert response.json()["username"] == "viewer"
    assert set(response.json()) == {"id", "username", "created_at"}


@pytest.mark.parametrize(
    ("username", "password"),
    [
        ("viewer", "WrongPassword123!"),
        ("missing", "StrongPassword123!"),
    ],
)
def test_invalid_credentials_return_401(
    client: TestClient,
    username: str,
    password: str,
) -> None:
    register_user(client)

    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )

    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "UNAUTHORIZED",
            "message": "Invalid credentials.",
        }
    }


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Authorization": "Basic abc"},
        {"Authorization": "Bearer"},
        {"Authorization": "Bearer not-a-jwt"},
    ],
)
def test_me_rejects_missing_or_invalid_credentials(
    client: TestClient,
    headers: dict[str, str],
) -> None:
    response = client.get("/api/v1/users/me", headers=headers)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
    assert response.headers["www-authenticate"] == "Bearer"


def test_each_token_identifies_its_own_user(client: TestClient) -> None:
    first_id = register_user(client, "first-user")
    second_id = register_user(client, "second-user")

    first_token = login_user(client, "first-user")
    second_token = login_user(client, "second-user")

    first = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {first_token}"},
    )
    second = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {second_token}"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == first_id
    assert second.json()["id"] == second_id


@pytest.mark.parametrize("case", ["expired", "wrong-signature", "missing-user"])
def test_me_rejects_unusable_signed_tokens(
    client: TestClient,
    settings: Settings,
    case: str,
) -> None:
    user_id = register_user(client)
    now = datetime.now(UTC)

    payload = {
        "sub": str(uuid4()) if case == "missing-user" else user_id,
        "jti": str(uuid4()),
        "iat": int((now - timedelta(minutes=2)).timestamp()),
        "exp": int(
            (
                now - timedelta(minutes=1)
                if case == "expired"
                else now + timedelta(minutes=15)
            ).timestamp()
        ),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "token_type": "access",
    }

    secret = (
        "wrong-secret-" + "z" * 48
        if case == "wrong-signature"
        else settings.jwt_secret.get_secret_value()
    )

    token = jwt.encode(payload, secret, algorithm="HS256")

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
