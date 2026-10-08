from fastapi.testclient import TestClient

from reelshelf.main import create_app


def test_health() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
