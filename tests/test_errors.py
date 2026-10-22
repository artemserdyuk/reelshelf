import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from reelshelf.domain.errors import (
    BusinessRuleError,
    ConflictError,
    DomainError,
    NotFoundError,
    UnauthorizedError,
)


class ProbeRequest(BaseModel):
    quantity: int = Field(gt=0, strict=True)


def test_unknown_route_returns_error_schema(client: TestClient) -> None:
    response = client.get("/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "NOT_FOUND",
            "message": "Not Found.",
        }
    }


def test_wrong_method_preserves_allow_header(client: TestClient) -> None:
    response = client.post("/health/live")

    assert response.status_code == 405
    assert response.json()["error"]["code"] == "METHOD_NOT_ALLOWED"
    assert "GET" in response.headers["allow"]


@pytest.mark.parametrize(
    "quantity",
    [0, -1, "2", True],
)
def test_invalid_request_returns_error_schema(
    app: FastAPI,
    quantity: object,
) -> None:
    @app.post("/_test/validation")
    async def validation_probe(body: ProbeRequest) -> ProbeRequest:
        return body

    with TestClient(app) as client:
        response = client.post(
            "/_test/validation",
            json={"quantity": quantity},
        )

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed.",
        }
    }


@pytest.mark.parametrize(
    ("error_type", "status_code", "code"),
    [
        (NotFoundError, 404, "NOT_FOUND"),
        (ConflictError, 409, "CONFLICT"),
        (UnauthorizedError, 401, "UNAUTHORIZED"),
        (BusinessRuleError, 422, "VALIDATION_ERROR"),
    ],
)
def test_domain_errors_are_mapped_to_http(
    app: FastAPI,
    error_type: type[DomainError],
    status_code: int,
    code: str,
) -> None:
    @app.get("/_test/domain")
    async def domain_probe() -> None:
        raise error_type("Expected business error.")

    with TestClient(app) as client:
        response = client.get("/_test/domain")

    assert response.status_code == status_code
    assert response.json() == {
        "error": {
            "code": code,
            "message": "Expected business error.",
        }
    }

    if status_code == 401:
        assert response.headers["www-authenticate"] == "Bearer"


def test_http_error_preserves_authentication_header(app: FastAPI) -> None:
    @app.get("/_test/http")
    async def http_probe() -> None:
        raise HTTPException(
            status_code=401,
            detail="Internal authentication detail.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    with TestClient(app) as client:
        response = client.get("/_test/http")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {
        "error": {
            "code": "UNAUTHORIZED",
            "message": "Unauthorized.",
        }
    }


def test_unexpected_error_hides_internal_details(app: FastAPI) -> None:
    @app.get("/_test/crash")
    async def crash_probe() -> None:
        raise RuntimeError("Private implementation details.")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/_test/crash")

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred.",
        }
    }
    assert "Private implementation details." not in response.text
