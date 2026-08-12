"""Request validation and safe response models for breach checks."""

import re

from pydantic import BaseModel, Field, field_validator


EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$")


class EmailQuery(BaseModel):
    """A bounded, syntactically valid email address for the provider request."""

    value: str = Field(min_length=3, max_length=254)

    @field_validator("value")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("value must be a well-formed email address")
        return normalized


class BreachSummary(BaseModel):
    """Public breach metadata only; credentials and raw leaked records are excluded."""

    name: str
    breach_date: str | None = None
    data_classes: list[str] = Field(default_factory=list)
    description: str


class BreachCheckData(BaseModel):
    value: str
    breached: bool
    breaches: list[BreachSummary] = Field(default_factory=list)
