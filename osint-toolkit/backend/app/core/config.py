"""Configuration loaded from environment variables and an optional .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the API."""

    app_name: str = "OSINT Toolkit"
    environment: str = "development"
    log_level: str = "INFO"
    dns_timeout_seconds: float = 5.0
    dns_lifetime_seconds: float = 10.0
    shodan_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()
