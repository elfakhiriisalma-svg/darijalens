"""Configuration de l'application, lue depuis les variables d'environnement."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Paramètres de l'API. Les valeurs viennent du fichier .env ou de l'environnement."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "DarijaLens API"
    app_version: str = "0.1.0"
    database_url: str = "postgresql+psycopg://darijalens:change-me@db:5432/darijalens"
    offensive_model_path: str = "models/offensive.joblib"
    sentiment_model_path: str = "models/sentiment.joblib"


@lru_cache
def get_settings() -> Settings:
    """Retourne une seule instance des paramètres (mise en cache)."""
    return Settings()
