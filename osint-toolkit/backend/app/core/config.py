"""Configuration loaded from environment variables and an optional .env file."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIRECTORY = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    """Runtime configuration for the API."""

    app_name: str = "OSINT Toolkit"
    environment: str = "development"
    log_level: str = "INFO"
    dns_timeout_seconds: float = Field(default=5.0, gt=0)
    dns_lifetime_seconds: float = Field(default=10.0, gt=0)
    whois_timeout_seconds: float = Field(default=10.0, gt=0)
    shodan_api_key: str = ""
    xon_base_url: str = "https://api.xposedornot.com"

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIRECTORY / ".env", env_file_encoding="utf-8-sig"
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()
