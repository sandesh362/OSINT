"""Request and response models for network reconnaissance."""

from datetime import datetime

from pydantic import BaseModel, Field, IPvAnyAddress, field_validator


class HostQuery(BaseModel):
    """Validated host lookup parameters."""

    ip: IPvAnyAddress


class SearchQuery(BaseModel):
    """Validated Shodan search parameters."""

    query: str = Field(min_length=1, max_length=200)
    page: int = Field(default=1, ge=1, le=100)

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("query must not be blank")
        return value.strip()


class Location(BaseModel):
    country_name: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class ServiceBanner(BaseModel):
    port: int | None = None
    transport: str | None = None
    product: str | None = None
    version: str | None = None
    banner: str | None = None


class HostData(BaseModel):
    ip: str
    open_ports: list[int] = Field(default_factory=list)
    services: list[ServiceBanner] = Field(default_factory=list)
    org: str | None = None
    isp: str | None = None
    location: Location = Field(default_factory=Location)
    os_guess: str | None = None
    last_updated: datetime | None = None


class SearchHost(BaseModel):
    ip: str
    port: int | None = None
    org: str | None = None
    location: Location = Field(default_factory=Location)


class SearchData(BaseModel):
    total: int
    page: int
    results: list[SearchHost] = Field(default_factory=list)
