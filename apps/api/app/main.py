"""Point d'entrée de l'API DarijaLens."""

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.db import check_database

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Analyse et traduction de la darija écrite.",
)


@app.get("/health", tags=["monitoring"])
def health() -> dict[str, str]:
    """Indique que le serveur tourne (ne vérifie pas la base)."""
    return {"status": "ok", "version": settings.app_version}


@app.get("/ready", tags=["monitoring"])
def ready() -> JSONResponse:
    """Indique que le serveur ET la base de données sont utilisables."""
    if check_database():
        return JSONResponse({"status": "ready", "database": "ok"})
    return JSONResponse(
        {"status": "not ready", "database": "unreachable"},
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    )
