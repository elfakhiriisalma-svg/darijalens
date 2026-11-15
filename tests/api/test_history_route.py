"""Tests de l'historique et des statistiques (base SQLite en mémoire, sans PostgreSQL)."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db import Analysis, Base, get_session
from app.main import app


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def client(engine):
    def override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override
    yield TestClient(app)
    app.dependency_overrides.clear()


def entry(**changes) -> dict:
    base = {
        "text": "3jebni had lfilm bzaf",
        "script": "latin",
        "sentiment": "positive",
        "sentiment_score": 0.9,
        "offensive": "non_offensive",
        "offensive_score": 0.1,
    }
    return {**base, **changes}


def test_stats_of_an_empty_history(client: TestClient) -> None:
    body = client.get("/stats").json()
    assert body["total"] == 0
    assert body["sentiment"] == {"positive": 0, "negative": 0, "uncertain": 0}
    assert body["offensive"] == {"offensive": 0, "non_offensive": 0}
    assert body["scripts"] == {"arabic": 0, "latin": 0, "mixed": 0, "unknown": 0}
    assert len(body["daily"]) == 14
    assert sum(day["count"] for day in body["daily"]) == 0
    assert body["recent"] == []


def test_added_analyses_are_counted(client: TestClient) -> None:
    client.post("/history", json=entry())
    client.post("/history", json=entry(sentiment="negative", sentiment_score=0.1))
    client.post(
        "/history",
        json=entry(text="خايب", script="arabic", sentiment="uncertain", offensive="offensive"),
    )
    body = client.get("/stats").json()
    assert body["total"] == 3
    assert body["sentiment"] == {"positive": 1, "negative": 1, "uncertain": 1}
    assert body["offensive"] == {"offensive": 1, "non_offensive": 2}
    assert body["scripts"]["latin"] == 2
    assert body["scripts"]["arabic"] == 1
    assert body["daily"][-1]["count"] == 3  # tout a été ajouté aujourd'hui
    assert body["recent"][0]["text"] == "خايب"  # la plus récente d'abord


def test_a_model_that_was_unavailable_is_stored_as_missing(client: TestClient) -> None:
    response = client.post("/history", json={"text": "salam", "script": "latin"})
    assert response.status_code == 201
    row = client.get("/stats").json()["recent"][0]
    assert row["sentiment"] is None
    assert row["offensive"] is None


def test_long_text_is_truncated_before_storage(client: TestClient) -> None:
    client.post("/history", json=entry(text="a" * 1000))
    assert len(client.get("/stats").json()["recent"][0]["text"]) == 300


def test_recent_list_is_limited_to_ten(client: TestClient) -> None:
    for index in range(12):
        client.post("/history", json=entry(text=f"texte {index}"))
    recent = client.get("/stats").json()["recent"]
    assert len(recent) == 10
    assert recent[0]["text"] == "texte 11"


def test_old_analyses_fall_outside_the_chart_but_stay_in_totals(client: TestClient, engine) -> None:
    with Session(engine) as session:
        old = datetime.now(UTC) - timedelta(days=40)
        session.add(Analysis(text="ancien", script="latin", created_at=old))
        session.commit()
    body = client.get("/stats?days=7").json()
    assert body["total"] == 1
    assert len(body["daily"]) == 7
    assert sum(day["count"] for day in body["daily"]) == 0


def test_clear_history(client: TestClient) -> None:
    client.post("/history", json=entry())
    assert client.delete("/history").status_code == 204
    assert client.get("/stats").json()["total"] == 0


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"text": "", "script": "latin"},
        {"text": "salam", "script": "klingon"},
        {"text": "salam", "script": "latin", "sentiment": "joyful"},
        {"text": "salam", "script": "latin", "sentiment_score": 1.5},
    ],
)
def test_history_rejects_invalid_entries(client: TestClient, payload: dict) -> None:
    assert client.post("/history", json=payload).status_code == 422


@pytest.mark.parametrize("days", [0, 91])
def test_stats_rejects_a_silly_number_of_days(client: TestClient, days: int) -> None:
    assert client.get(f"/stats?days={days}").status_code == 422


def test_unreachable_database_gives_a_clear_503(monkeypatch) -> None:
    def broken():
        raise OperationalError("SELECT 1", {}, Exception("connexion refusée"))

    monkeypatch.setattr("app.db.get_engine", broken)
    response = TestClient(app).get("/stats")
    assert response.status_code == 503
    assert "docker compose up -d db" in response.json()["detail"]
