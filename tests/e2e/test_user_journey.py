import os
from collections.abc import Iterator
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient

from reelshelf.schemas.auth import TokenPairResponse


@pytest.fixture
def journey_client(client: TestClient) -> Iterator[httpx.Client]:
    base_url = os.environ.get("E2E_BASE_URL")

    if base_url:
        with httpx.Client(
            base_url=base_url,
            timeout=10,
            trust_env=False,
        ) as live_client:
            yield live_client
    else:
        yield client


def expect(
    client: httpx.Client,
    method: str,
    path: str,
    expected: int,
    *,
    token: str | None = None,
    body: dict[str, object] | None = None,
) -> httpx.Response:
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    try:
        response = client.request(method, path, headers=headers, json=body)
    except httpx.RequestError as exc:
        pytest.fail(f"{method} {path}: cannot reach API: {exc}")

    assert response.status_code == expected, (
        f"{method} {path}: expected {expected}, "
        f"got {response.status_code}. Body: {response.text}"
    )

    if expected == 204:
        assert response.content == b""
    elif expected >= 400:
        error = response.json()["error"]
        assert isinstance(error["code"], str)
        assert isinstance(error["message"], str)

    print(f"{method} {path} -> {expected}")
    return response


def tokens(response: httpx.Response) -> TokenPairResponse:
    assert response.headers["cache-control"] == "no-store"

    pair = TokenPairResponse.model_validate(response.json())
    assert pair.access_token and pair.refresh_token
    assert pair.access_token != pair.refresh_token

    return pair


def test_complete_user_journey(journey_client: httpx.Client) -> None:
    client = journey_client

    credentials: dict[str, object] = {
        "username": f"journey-{uuid4().hex[:12]}",
        "password": "StrongPassword123!",
    }
    owner = expect(
        client, "POST", "/api/v1/auth/register", 201, body=credentials
    ).json()
    pair = tokens(expect(client, "POST", "/api/v1/auth/login", 200, body=credentials))

    other_credentials: dict[str, object] = {
        "username": f"other-{uuid4().hex[:12]}",
        "password": "StrongPassword123!",
    }
    expect(client, "POST", "/api/v1/auth/register", 201, body=other_credentials)
    other = tokens(
        expect(client, "POST", "/api/v1/auth/login", 200, body=other_credentials)
    )

    expect(client, "GET", "/api/v1/entries", 401)

    first = expect(
        client,
        "POST",
        "/api/v1/entries",
        201,
        token=pair.access_token,
        body={"title": "Arrival", "release_year": 2016},
    ).json()
    second = expect(
        client,
        "POST",
        "/api/v1/entries",
        201,
        token=pair.access_token,
        body={"title": "Dune"},
    ).json()

    assert first["user_id"] == second["user_id"] == owner["id"]
    path = f"/api/v1/entries/{first['id']}"

    assert expect(client, "GET", path, 200, token=pair.access_token).json() == first

    page = expect(
        client,
        "GET",
        "/api/v1/entries?limit=1&offset=1",
        200,
        token=pair.access_token,
    ).json()
    assert page["total"] == 2 and len(page["items"]) == 1
    assert page["limit"] == 1 and page["offset"] == 1

    empty = expect(
        client, "GET", "/api/v1/entries", 200, token=other.access_token
    ).json()
    assert empty["items"] == [] and empty["total"] == 0

    for method in ("GET", "PATCH", "DELETE"):
        denied = expect(
            client,
            method,
            path,
            404,
            token=other.access_token,
            body={"title": "Foreign"} if method == "PATCH" else None,
        )
        assert denied.json()["error"]["code"] == "NOT_FOUND"

    expect(
        client,
        "PATCH",
        path,
        422,
        token=pair.access_token,
        body={"rating": 9},
    )
    assert expect(client, "GET", path, 200, token=pair.access_token).json() == first

    updated = expect(
        client,
        "PATCH",
        path,
        200,
        token=pair.access_token,
        body={"status": "watched", "rating": 9},
    ).json()
    assert updated["status"] == "watched" and updated["rating"] == 9

    watched = expect(
        client,
        "GET",
        "/api/v1/entries?status=watched",
        200,
        token=pair.access_token,
    ).json()
    assert watched["total"] == 1 and watched["items"] == [updated]

    rotated = tokens(
        expect(
            client,
            "POST",
            "/api/v1/auth/refresh",
            200,
            body={"refresh_token": pair.refresh_token},
        )
    )
    assert rotated.refresh_token != pair.refresh_token
    assert rotated.access_token != pair.access_token
    assert (
        expect(client, "GET", path, 200, token=rotated.access_token).json() == updated
    )

    expect(client, "DELETE", path, 204, token=rotated.access_token)
    expect(client, "GET", path, 404, token=rotated.access_token)
    expect(client, "DELETE", path, 404, token=rotated.access_token)

    page = expect(
        client, "GET", "/api/v1/entries", 200, token=rotated.access_token
    ).json()
    assert page["total"] == 1 and page["items"] == [second]

    refresh_body: dict[str, object] = {"refresh_token": rotated.refresh_token}
    expect(client, "POST", "/api/v1/auth/logout", 204, body=refresh_body)
    expect(client, "POST", "/api/v1/auth/refresh", 401, body=refresh_body)

    # Logout revokes refresh, while the issued access token remains valid.
    me = expect(
        client, "GET", "/api/v1/users/me", 200, token=rotated.access_token
    ).json()
    assert me["id"] == owner["id"]

    fresh = tokens(expect(client, "POST", "/api/v1/auth/login", 200, body=credentials))
    second_path = f"/api/v1/entries/{second['id']}"

    assert (
        expect(client, "GET", second_path, 200, token=fresh.access_token).json()
        == second
    )

    expect(client, "DELETE", second_path, 204, token=fresh.access_token)

    final_page = expect(
        client, "GET", "/api/v1/entries", 200, token=fresh.access_token
    ).json()
    assert final_page["items"] == [] and final_page["total"] == 0
