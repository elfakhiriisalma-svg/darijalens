"""Tests de la route /analyze."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import MAX_TEXT_LENGTH

client = TestClient(app)


def test_analyze_arabizi_text() -> None:
    response = client.post("/analyze", json={"text": "Wach NTA mzyaaaan!!!"})
    assert response.status_code == 200
    assert response.json() == {
        "script": "latin",
        "arabic_letters": 0,
        "latin_letters": 15,
        "normalized_text": "wach nta mzyan!",
        "arabic_text": "واش نتا مزيان!",
    }


def test_analyze_mixed_text() -> None:
    response = client.post("/analyze", json={"text": "wach نتا mzyan"})
    assert response.status_code == 200
    body = response.json()
    assert body["script"] == "mixed"
    assert body["arabic_text"] == "واش نتا مزيان"


def test_analyze_text_without_letters() -> None:
    response = client.post("/analyze", json={"text": "123 !!!"})
    assert response.status_code == 200
    assert response.json()["script"] == "unknown"


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"text": ""},
        {"text": 5},
        {"text": "a" * (MAX_TEXT_LENGTH + 1)},
    ],
)
def test_analyze_rejects_invalid_input(payload: dict) -> None:
    assert client.post("/analyze", json=payload).status_code == 422
