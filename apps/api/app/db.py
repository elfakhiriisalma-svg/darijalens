"""Accès à la base de données PostgreSQL."""

from sqlalchemy import Engine, create_engine, text

from app.config import get_settings


def get_engine() -> Engine:
    """Crée le moteur de connexion. pool_pre_ping évite d'utiliser une connexion morte."""
    return create_engine(get_settings().database_url, pool_pre_ping=True)


def check_database(engine: Engine | None = None) -> bool:
    """Retourne True si la base répond à une requête simple, False sinon."""
    try:
        with (engine or get_engine()).connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001 - toute panne de connexion signifie "pas prête"
        return False
