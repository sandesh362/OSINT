"""Request validation and response models for public username checks."""

from datetime import datetime
import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator


USERNAME_PATTERN = r"^[A-Za-z0-9_.-]{1,39}$"


class UsernameQuery(BaseModel):
    """A safe, bounded username accepted by public profile URL templates."""

    value: str = Field(pattern=USERNAME_PATTERN, min_length=1, max_length=39)

    @field_validator("value")
    @classmethod
    def validate_username(cls, value: str) -> str:
        if not value or not re.fullmatch(USERNAME_PATTERN, value):
            raise ValueError("value must contain only letters, numbers, underscores, hyphens, or dots")
        return value


class PlatformResult(BaseModel):
    """A minimal, source-labelled public-profile observation."""

    platform: str
    url: str
    status: Literal["found", "not_found", "uncertain"]
    checked_at: datetime
    profile_title: str | None = None
    profile_description: str | None = None


class UsernameLookupData(BaseModel):
    username: str
    results: list[PlatformResult] = Field(default_factory=list)
