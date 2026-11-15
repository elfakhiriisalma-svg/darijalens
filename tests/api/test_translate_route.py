"""Tests de la route /translate (avec un faux traducteur : le vrai modèle n'est pas chargé)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import MAX_TEXT_LENGTH
from app.translate import get_translator
from darijalens_nlp.translate import Translation


class FakeTranslator:
    def translate(self, text: str, targets) -> Translation:
        texts = {target: f"[{target}] {text}" for target in targets}
        return Translation(texts=texts, source=text, transliterated=False)


@pytest.fixture
def client():
    app.dependency_overrides[get_translator] = lambda: FakeTranslator()
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_translate_returns_all_targets_by_default(client: TestClient) -> None:
    body = client.post("/translate", json={"text": "الطقس زوين"}).json()
    assert body["translations"] == {
        "fr": "[fr] الطقس زوين",
        "en": "[en] الطقس زوين",
        "ar": "[ar] الطقس زوين",
    }
    assert body["transliterated"] is False


@pytest.mark.parametrize("target", ["fr", "en", "ar", "msa"])
def test_translate_can_ask_for_one_language(client: TestClient, target: str) -> None:
    body = client.post("/translate", json={"text": "الطقس زوين", "targets": [target]}).json()
    assert list(body["translations"]) == [target]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"text": ""},
        {"text": "salam", "targets": []},
        {"text": "salam", "targets": ["de"]},
        {"text": "a" * (MAX_TEXT_LENGTH + 1)},
    ],
)
def test_translate_rejects_invalid_input(client: TestClient, payload: dict) -> None:
    assert client.post("/translate", json=payload).status_code == 422


def test_translate_returns_503_when_libraries_are_missing(monkeypatch) -> None:
    def missing(_model_name: str):
        raise ImportError("No module named 'torch'")

    monkeypatch.setattr("app.translate._load_translator", missing)
    response = TestClient(app).post("/translate", json={"text": "salam"})
    assert response.status_code == 503
    assert "requirements-translation.txt" in response.json()["detail"]
