"""Route d'analyse de sentiment (positif / négatif)."""

from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import get_settings
from app.schemas import AnalyzeRequest, ExplanationItem, SentimentResponse
from darijalens_nlp.sentiment import SentimentClassifier

router = APIRouter(tags=["analyse"])

UNCERTAIN_LABEL = 2
UNCERTAIN_NAME = "uncertain"


@lru_cache
def _load_classifier(path: str) -> SentimentClassifier:
    return SentimentClassifier.load(Path(path))


def get_sentiment_classifier() -> SentimentClassifier:
    """Charge le modèle une seule fois. Répond 503 s'il n'a pas encore été entraîné."""
    path = get_settings().sentiment_model_path
    if not Path(path).is_file():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modèle indisponible : lancez d'abord `python ml/train_sentiment.py`.",
        )
    return _load_classifier(path)


@router.post("/sentiment", response_model=SentimentResponse)
def analyze_sentiment(
    request: AnalyzeRequest,
    classifier: SentimentClassifier = Depends(get_sentiment_classifier),  # noqa: B008
) -> SentimentResponse:
    """Dit si un commentaire est positif, négatif ou incertain, avec un score et les mots clés."""
    prediction = classifier.predict(request.text)
    settings = get_settings()
    label, name = prediction.label, prediction.name
    if settings.sentiment_uncertain_low <= prediction.score <= settings.sentiment_uncertain_high:
        label, name = UNCERTAIN_LABEL, UNCERTAIN_NAME
    explanation = [
        ExplanationItem(feature=feature, weight=weight)
        for feature, weight in classifier.explain(request.text)
    ]
    return SentimentResponse(
        label=label,
        name=name,
        score=prediction.score,
        explanation=explanation,
    )
