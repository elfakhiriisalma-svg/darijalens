"""Route d'analyse d'un texte en darija."""

from fastapi import APIRouter

from app.schemas import AnalyzeRequest, AnalyzeResponse
from darijalens_nlp import detect_script, normalize_text, transliterate_arabizi

router = APIRouter(tags=["analyse"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    """Détecte l'écriture, nettoie le texte et transcrit l'arabizi en arabe."""
    script = detect_script(request.text)
    normalized = normalize_text(request.text)
    return AnalyzeResponse(
        script=script.script.value,
        arabic_letters=script.arabic_letters,
        latin_letters=script.latin_letters,
        normalized_text=normalized,
        arabic_text=transliterate_arabizi(normalized),
    )
