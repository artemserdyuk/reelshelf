from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient

from reelshelf.core.config import Settings
from reelshelf.schemas.auth import TokenPairResponse

AUTH = "/api/v1/auth"
ME = "/api/v1/users/me"
CREDENTIALS = {"username": "viewer", "password": "StrongPassword123!"}


@pytest.fixture
def registered(client: TestClient) -> TestClient:
    response = client.post(f"{AUTH}/register", json=CREDENTIALS)
    assert response.status_code == 201
    return client


def login(client: TestClient) -> TokenPairResponse:
    response = client.post(f"{AUTH}/login", json=CREDENTIALS)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    return TokenPairResponse.model_validate(response.json())


def test_rotation_replay_and_independent_login(registered: TestClient) -> None:
    laptop = login(registered)
    phone = login(registered)

    response = registered.post(
        f"{AUTH}/refresh",
        json={"refresh_token": laptop.refresh_token},
    )
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    rotated = TokenPairResponse.model_validate(response.json())

    assert rotated.access_token != laptop.access_token
    assert rotated.refresh_token != laptop.refresh_token

    me = registered.get(ME, headers={"Authorization": f"Bearer {rotated.access_token}"})
    assert me.status_code == 200
    assert me.json()["username"] == "viewer"

    # Replaying the old refresh token revokes the entire laptop family.
    for token in (laptop.refresh_token, rotated.refresh_token):
        denied = registered.post(f"{AUTH}/refresh", json={"refresh_token": token})
        assert denied.status_code == 401
        assert denied.json()["error"]["code"] == "UNAUTHORIZED"

    # The phone is a separate login even though it belongs to the same user.
    phone_refresh = registered.post(
        f"{AUTH}/refresh", json={"refresh_token": phone.refresh_token}
    )
    assert phone_refresh.status_code == 200


def test_logout_revokes_refresh_but_access_lives_until_expiry(
    registered: TestClient,
) -> None:
    pair = login(registered)
    body = {"refresh_token": pair.refresh_token}

    logout = registered.post(f"{AUTH}/logout", json=body)
    assert logout.status_code == 204
    assert logout.content == b""

    assert registered.post(f"{AUTH}/refresh", json=body).status_code == 401
    assert registered.post(f"{AUTH}/logout", json=body).status_code == 401

    me = registered.get(ME, headers={"Authorization": f"Bearer {pair.access_token}"})
    assert me.status_code == 200


def test_token_types_cannot_be_swapped(registered: TestClient) -> None:
    pair = login(registered)

    for path in ("refresh", "logout"):
        response = registered.post(
            f"{AUTH}/{path}", json={"refresh_token": pair.access_token}
        )
        assert response.status_code == 401

    me = registered.get(ME, headers={"Authorization": f"Bearer {pair.refresh_token}"})
    assert me.status_code == 401


@pytest.mark.parametrize("path", ["refresh", "logout"])
def test_missing_and_malformed_refresh_tokens(client: TestClient, path: str) -> None:
    assert client.post(f"{AUTH}/{path}", json={}).status_code == 422
    invalid = client.post(f"{AUTH}/{path}", json={"refresh_token": "not-a-jwt"})
    assert invalid.status_code == 401


@pytest.mark.parametrize("case", ["expired", "wrong-key", "wrong-type", "unknown-jti"])
def test_invalid_refresh_cannot_spend_a_valid_session(
    registered: TestClient,
    settings: Settings,
    case: str,
) -> None:
    pair = login(registered)
    secret = settings.jwt_secret.get_secret_value()
    audience = f"{settings.jwt_audience}:refresh"
    claims = jwt.decode(
        pair.refresh_token,
        secret,
        algorithms=["HS256"],
        issuer=settings.jwt_issuer,
        audience=audience,
    )
    signing_key = secret
    now = datetime.now(UTC)

    if case == "expired":
        claims["iat"] = int((now - timedelta(days=2)).timestamp())
        claims["exp"] = int((now - timedelta(days=1)).timestamp())
    elif case == "wrong-key":
        signing_key = "another-test-key-" + "x" * 48
    elif case == "wrong-type":
        claims["token_type"] = "access"
    else:
        claims["jti"] = str(uuid4())

    modified = jwt.encode(claims, signing_key, algorithm="HS256")
    denied = registered.post(f"{AUTH}/refresh", json={"refresh_token": modified})
    assert denied.status_code == 401

    # Invalid credentials must not revoke or consume the real active session.
    valid = registered.post(
        f"{AUTH}/refresh", json={"refresh_token": pair.refresh_token}
    )
    assert valid.status_code == 200
