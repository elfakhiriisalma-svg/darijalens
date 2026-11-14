"""Tests de la route /translate (avec un faux traducteur : le vrai modèle n'est pas chargé)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import MAX_TEXT_LENGTH
from app.translate import get_translator
from darijalens_nlp.translate import Translation


class FakeTranslator:
    def translate(self, text: str, target: str) -> Translation:
        return Translation(text=f"[{target}] {text}", source=text, transliterated=False)


@pytest.fixture
def client():
    app.dependency_overrides[get_translator] = lambda: FakeTranslator()
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.mark.parametrize("target", ["fr", "en"])
def test_translate_returns_translation(client: TestClient, target: str) -> None:
    body = client.post("/translate", json={"text": "الطقس زوين", "target": target}).json()
    assert body["target"] == target
    assert body["translation"] == f"[{target}] الطقس زوين"
    assert body["transliterated"] is False


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"text": "salam"},
        {"text": "", "target": "fr"},
        {"text": "salam", "target": "de"},
        {"text": "a" * (MAX_TEXT_LENGTH + 1), "target": "fr"},
    ],
)
def test_translate_rejects_invalid_input(client: TestClient, payload: dict) -> None:
    assert client.post("/translate", json=payload).status_code == 422


def test_translate_returns_503_when_libraries_are_missing(monkeypatch) -> None:
    def missing(_model_name: str):
        raise ImportError("No module named 'torch'")

    monkeypatch.setattr("app.translate._load_translator", missing)
    response = TestClient(app).post("/translate", json={"text": "salam", "target": "fr"})
    assert response.status_code == 503
    assert "requirements-translation.txt" in response.json()["detail"]
