"""Request and response models for the domain intelligence API."""

from datetime import datetime
import re

from pydantic import BaseModel, Field, field_validator


DOMAIN_PATTERN = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$",
    re.IGNORECASE,
)


class DomainQuery(BaseModel):
    """Validated domain query parameters."""

    domain: str = Field(description="Fully qualified domain name, e.g. example.com")

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, value: str) -> str:
        normalized = value.strip().lower().rstrip(".")
        if not DOMAIN_PATTERN.fullmatch(normalized):
            raise ValueError("domain must be a valid public domain name")
        return normalized


class WhoisData(BaseModel):
    registrar: str | None = None
    creation_date: datetime | None = None
    expiration_date: datetime | None = None
    name_servers: list[str] = Field(default_factory=list)
    registrant_org: str | None = None


class DnsData(BaseModel):
    a: list[str] = Field(default_factory=list)
    aaaa: list[str] = Field(default_factory=list)
    mx: list[str] = Field(default_factory=list)
    ns: list[str] = Field(default_factory=list)
    txt: list[str] = Field(default_factory=list)
