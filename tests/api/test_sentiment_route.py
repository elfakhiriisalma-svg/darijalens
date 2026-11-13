"""Tests de la route /sentiment (avec un petit modèle fabriqué, sans fichier sur disque)."""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import MAX_TEXT_LENGTH
from app.sentiment import get_sentiment_classifier
from darijalens_nlp.offensive import Example, build_pipeline
from darijalens_nlp.sentiment import SentimentClassifier


@pytest.fixture
def toy_classifier() -> SentimentClassifier:
    positive = [Example(f"zwin bzaf bravo numero{i}", 1, "latin") for i in range(30)]
    negative = [Example(f"khayb machi mezyan numero{i}", 0, "latin") for i in range(30)]
    data = positive + negative
    model = build_pipeline().fit([e.text for e in data], [e.label for e in data])
    return SentimentClassifier(model)


@pytest.fixture
def client(toy_classifier: SentimentClassifier):
    app.dependency_overrides[get_sentiment_classifier] = lambda: toy_classifier
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_positive_text(client: TestClient) -> None:
    body = client.post("/sentiment", json={"text": "zwin bzaf bravo"}).json()
    assert body["label"] == 1
    assert body["name"] == "positive"
    assert body["score"] > 0.5
    assert 1 <= len(body["explanation"]) <= 5


def test_negative_text(client: TestClient) -> None:
    body = client.post("/sentiment", json={"text": "khayb machi mezyan"}).json()
    assert body["label"] == 0
    assert body["name"] == "negative"
    assert body["score"] < 0.5


def test_score_in_hesitation_zone_gives_uncertain(client: TestClient, monkeypatch) -> None:
    wide = SimpleNamespace(sentiment_uncertain_low=0.0, sentiment_uncertain_high=1.0)
    monkeypatch.setattr("app.sentiment.get_settings", lambda: wide)
    body = client.post("/sentiment", json={"text": "zwin bzaf bravo"}).json()
    assert body["label"] == 2
    assert body["name"] == "uncertain"


@pytest.mark.parametrize("payload", [{}, {"text": ""}, {"text": "a" * (MAX_TEXT_LENGTH + 1)}])
def test_sentiment_rejects_invalid_input(client: TestClient, payload: dict) -> None:
    assert client.post("/sentiment", json=payload).status_code == 422


def test_sentiment_returns_503_when_model_is_missing(monkeypatch) -> None:
    missing = SimpleNamespace(sentiment_model_path="/inexistant/sentiment.joblib")
    monkeypatch.setattr("app.sentiment.get_settings", lambda: missing)
    response = TestClient(app).post("/sentiment", json={"text": "zwin"})
    assert response.status_code == 503
    assert "python ml/train_sentiment.py" in response.json()["detail"]
