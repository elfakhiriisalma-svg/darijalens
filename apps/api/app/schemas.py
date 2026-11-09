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
