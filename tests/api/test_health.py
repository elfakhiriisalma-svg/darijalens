"""Tests des routes de surveillance de l'API."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_ready_returns_503_when_database_is_down(monkeypatch) -> None:
    monkeypatch.setattr("app.main.check_database", lambda: False)
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["database"] == "unreachable"


def test_ready_returns_200_when_database_is_up(monkeypatch) -> None:
    monkeypatch.setattr("app.main.check_database", lambda: True)
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_cors_allows_the_local_web_interface() -> None:
    response = client.options(
        "/analyze",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_refuses_other_websites() -> None:
    response = client.options(
        "/analyze",
        headers={"Origin": "https://example.org", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in response.headers
