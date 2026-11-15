"""Formats des données échangées avec l'API."""

from typing import Literal

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

    label: int = Field(description="1 si positif, 0 si négatif, 2 si le modèle hésite.")
    name: str = Field(description="positive, negative ou uncertain (score proche de 0,5).")
    score: float = Field(ge=0, le=1, description="Probabilité estimée d'être positif.")
    explanation: list[ExplanationItem] = Field(description="Éléments qui ont le plus pesé.")


class TranslateRequest(BaseModel):
    """Texte à traduire."""

    text: str = Field(
        min_length=1,
        max_length=MAX_TEXT_LENGTH,
        description="Texte en darija (arabe, arabizi ou mélange).",
        examples=["شحال هاد الطوموبيل؟"],
    )
    targets: list[Literal["fr", "en", "ar", "msa"]] = Field(
        default=["fr", "en", "ar"],
        min_length=1,
        description=(
            "Cibles : fr, en, ar (la darija en lettres arabes, sans traduction) et msa "
            "(traduction en arabe standard). Par défaut : fr, en et ar."
        ),
    )


class TranslateResponse(BaseModel):
    """Résultat de la traduction."""

    translations: dict[str, str] = Field(description="Traduction pour chaque langue demandée.")
    source_used: str = Field(description="Texte réellement envoyé au modèle (nettoyé).")
    transliterated: bool = Field(description="Vrai si de l'arabizi a été transcrit en arabe.")


class HistoryEntry(BaseModel):
    """Ce que l'interface a affiché pour un texte, à garder dans l'historique."""

    text: str = Field(min_length=1, max_length=MAX_TEXT_LENGTH)
    script: Literal["arabic", "latin", "mixed", "unknown"]
    sentiment: Literal["positive", "negative", "uncertain"] | None = None
    sentiment_score: float | None = Field(default=None, ge=0, le=1)
    offensive: Literal["offensive", "non_offensive"] | None = None
    offensive_score: float | None = Field(default=None, ge=0, le=1)


class HistoryCreated(BaseModel):
    """Confirmation d'enregistrement."""

    id: int


class DailyCount(BaseModel):
    """Nombre d'analyses un jour donné."""

    date: str = Field(description="Jour au format AAAA-MM-JJ (UTC).")
    count: int


class RecentAnalysis(BaseModel):
    """Une analyse récente."""

    id: int
    created_at: str
    text: str
    script: str
    sentiment: str | None
    offensive: str | None


class StatsResponse(BaseModel):
    """Statistiques sur les analyses enregistrées."""

    total: int
    sentiment: dict[str, int] = Field(description="positive, negative, uncertain.")
    offensive: dict[str, int] = Field(description="offensive, non_offensive.")
    scripts: dict[str, int] = Field(description="arabic, latin, mixed, unknown.")
    daily: list[DailyCount]
    recent: list[RecentAnalysis]
