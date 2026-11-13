"""Formats des données échangées avec l'API."""

from pydantic import BaseModel, Field

MAX_TEXT_LENGTH = 5000


class AnalyzeRequest(BaseModel):
    """Texte à analyser."""

    text: str = Field(
        min_length=1,
        max_length=MAX_TEXT_LENGTH,
        description="Texte en darija (arabe, arabizi ou mélange).",
        examples=["Wach NTA mzyaaaan!!!"],
    )


class AnalyzeResponse(BaseModel):
    """Résultat de l'analyse d'un texte."""

    script: str = Field(description="Écriture détectée : arabic, latin, mixed ou unknown.")
    arabic_letters: int = Field(description="Nombre de lettres arabes.")
    latin_letters: int = Field(description="Nombre de lettres latines.")
    normalized_text: str = Field(description="Texte nettoyé.")
    arabic_text: str = Field(description="Texte nettoyé, avec les mots latins transcrits en arabe.")


class ExplanationItem(BaseModel):
    """Un élément du texte qui a pesé dans la décision."""

    feature: str = Field(description="Mot ou suite de lettres.")
    weight: float = Field(
        description="Positif : pousse vers offensant. Négatif : vers non offensant."
    )


class OffensiveResponse(BaseModel):
    """Résultat de la détection de langage offensant."""

    label: int = Field(description="1 si offensant, 0 sinon.")
    name: str = Field(description="offensive ou non_offensive.")
    score: float = Field(ge=0, le=1, description="Probabilité estimée d'être offensant.")
    explanation: list[ExplanationItem] = Field(description="Éléments qui ont le plus pesé.")


class SentimentResponse(BaseModel):
    """Résultat de l'analyse de sentiment."""

    label: int = Field(description="1 si positif, 0 si négatif.")
    name: str = Field(description="positive ou negative.")
    score: float = Field(ge=0, le=1, description="Probabilité estimée d'être positif.")
    explanation: list[ExplanationItem] = Field(description="Éléments qui ont le plus pesé.")
