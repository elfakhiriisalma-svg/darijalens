"""Route de traduction darija vers français ou anglais."""

from functools import lru_cache
from typing import Protocol

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import get_settings
from app.schemas import TranslateRequest, TranslateResponse
from darijalens_nlp.translate import Translation

router = APIRouter(tags=["traduction"])


class Translator(Protocol):
    """Ce que la route attend d'un traducteur (permet de le remplacer dans les tests)."""

    def translate(self, text: str, target: str) -> Translation: ...


@lru_cache
def _load_translator(model_name: str) -> Translator:
    from darijalens_nlp.translate import NllbTranslator

    return NllbTranslator(model_name)


def get_translator() -> Translator:
    """Charge le modèle une seule fois. Répond 503 si les bibliothèques manquent."""
    try:
        return _load_translator(get_settings().translation_model)
    except ImportError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Traduction indisponible : installez les bibliothèques avec "
                "`pip install -r apps/api/requirements-translation.txt`."
            ),
        ) from error


@router.post("/translate", response_model=TranslateResponse)
def translate(
    request: TranslateRequest,
    translator: Translator = Depends(get_translator),  # noqa: B008
) -> TranslateResponse:
    """Traduit un texte en darija (arabe ou arabizi) vers le français ou l'anglais."""
    result = translator.translate(request.text, request.target)
    return TranslateResponse(
        target=request.target,
        translation=result.text,
        source_used=result.source,
        transliterated=result.transliterated,
    )
