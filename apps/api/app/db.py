"""Accès à la base de données (PostgreSQL en production, SQLite possible en local)."""

from collections.abc import Iterator
from datetime import UTC, datetime
from functools import lru_cache

from fastapi import HTTPException, status
from sqlalchemy import DateTime, Engine, Float, Integer, String, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from app.config import get_settings

MAX_STORED_TEXT = 300


class Base(DeclarativeBase):
    """Classe de base des tables."""


class Analysis(Base):
    """Une analyse affichée par l'interface (le texte est tronqué à 300 caractères)."""

    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    text: Mapped[str] = mapped_column(String(MAX_STORED_TEXT))
    script: Mapped[str] = mapped_column(String(16))
    sentiment: Mapped[str | None] = mapped_column(String(16), nullable=True)
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    offensive: Mapped[str | None] = mapped_column(String(16), nullable=True)
    offensive_score: Mapped[float | None] = mapped_column(Float, nullable=True)


@lru_cache
def get_engine() -> Engine:
    """Crée le moteur de connexion. pool_pre_ping évite d'utiliser une connexion morte."""
    url = get_settings().database_url
    options = {"connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else {}
    return create_engine(url, pool_pre_ping=True, **options)


def check_database(engine: Engine | None = None) -> bool:
    """Retourne True si la base répond à une requête simple, False sinon."""
    try:
        with (engine or get_engine()).connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001 - toute panne de connexion signifie "pas prête"
        return False


_tables_ready: set[str] = set()


def ensure_tables(engine: Engine) -> None:
    """Crée les tables si elles n'existent pas (une seule fois par base)."""
    key = str(engine.url)
    if key not in _tables_ready:
        Base.metadata.create_all(engine)
        _tables_ready.add(key)


def get_session() -> Iterator[Session]:
    """Ouvre une session. Répond 503 avec une explication si la base est injoignable."""
    try:
        engine = get_engine()
        ensure_tables(engine)
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Base de données injoignable. Lancez `docker compose up -d db`, "
                "ou utilisez SQLite en local avec DATABASE_URL=sqlite:///darijalens.db."
            ),
        ) from error
    with Session(engine) as session:
        yield session
