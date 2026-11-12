"""Tests de la route /offensive (avec un petit modèle fabriqué, sans fichier sur disque)."""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.offensive import get_classifier
from app.schemas import MAX_TEXT_LENGTH
from darijalens_nlp.offensive import Example, OffensiveClassifier, build_pipeline


@pytest.fixture
def toy_classifier() -> OffensiveClassifier:
    gentle = [Example(f"merci beaucoup bonne journee numero{i}", 0, "latin") for i in range(30)]
    rude = [Example(f"tu es nul et stupide numero{i}", 1, "latin") for i in range(30)]
    data = gentle + rude
    model = build_pipeline().fit([e.text for e in data], [e.label for e in data])
    return OffensiveClassifier(model)


@pytest.fixture
def client(toy_classifier: OffensiveClassifier):
    app.dependency_overrides[get_classifier] = lambda: toy_classifier
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_offensive_text(client: TestClient) -> None:
    response = client.post("/offensive", json={"text": "tu es nul et stupide"})
    assert response.status_code == 200
    body = response.json()
    assert body["label"] == 1
    assert body["name"] == "offensive"
    assert body["score"] > 0.5
    assert 1 <= len(body["explanation"]) <= 5
    assert set(body["explanation"][0]) == {"feature", "weight"}


def test_non_offensive_text(client: TestClient) -> None:
    body = client.post("/offensive", json={"text": "merci beaucoup"}).json()
    assert body["label"] == 0
    assert body["score"] < 0.5


@pytest.mark.parametrize("payload", [{}, {"text": ""}, {"text": "a" * (MAX_TEXT_LENGTH + 1)}])
def test_offensive_rejects_invalid_input(client: TestClient, payload: dict) -> None:
    assert client.post("/offensive", json=payload).status_code == 422


def test_offensive_returns_503_when_model_is_missing(monkeypatch) -> None:
    missing = SimpleNamespace(offensive_model_path="/inexistant/offensive.joblib")
    monkeypatch.setattr("app.offensive.get_settings", lambda: missing)
    response = TestClient(app).post("/offensive", json={"text": "wach nta mzyan"})
    assert response.status_code == 503
    assert "python ml/train_offensive.py" in response.json()["detail"]
