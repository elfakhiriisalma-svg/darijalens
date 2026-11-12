"""Route de détection de langage offensant."""

from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import get_settings
from app.schemas import AnalyzeRequest, ExplanationItem, OffensiveResponse
from darijalens_nlp.offensive import OffensiveClassifier

router = APIRouter(tags=["analyse"])


@lru_cache
def _load_classifier(path: str) -> OffensiveClassifier:
    return OffensiveClassifier.load(Path(path))


def get_classifier() -> OffensiveClassifier:
    """Charge le modèle une seule fois. Répond 503 s'il n'a pas encore été entraîné."""
    path = get_settings().offensive_model_path
    if not Path(path).is_file():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modèle indisponible : lancez d'abord `python ml/train_offensive.py`.",
        )
    return _load_classifier(path)


@router.post("/offensive", response_model=OffensiveResponse)
def detect_offensive(
    request: AnalyzeRequest,
    classifier: OffensiveClassifier = Depends(get_classifier),  # noqa: B008
) -> OffensiveResponse:
    """Dit si un texte est offensant, avec un score et les éléments qui ont pesé."""
    prediction = classifier.predict(request.text)
    explanation = [
        ExplanationItem(feature=feature, weight=weight)
        for feature, weight in classifier.explain(request.text)
    ]
    return OffensiveResponse(
        label=prediction.label,
        name=prediction.name,
        score=prediction.score,
        explanation=explanation,
    )
