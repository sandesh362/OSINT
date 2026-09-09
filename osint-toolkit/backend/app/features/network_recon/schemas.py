"""Request and response models for network reconnaissance."""

from datetime import datetime

import ipaddress
import re

from pydantic import BaseModel, Field, field_validator


_HOSTNAME_LABEL = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)$", re.IGNORECASE)


class HostQuery(BaseModel):
    """Validated IP address or DNS hostname for a host lookup."""

    ip: str = Field(min_length=1, max_length=253)

    @field_validator("ip")
    @classmethod
    def validate_target(cls, value: str) -> str:
        target = value.strip().rstrip(".")
        if not target:
            raise ValueError("host target must not be blank")
        try:
            return str(ipaddress.ip_address(target))
        except ValueError:
            labels = target.split(".")
            if len(labels) < 2 or not all(_HOSTNAME_LABEL.fullmatch(label) for label in labels):
                raise ValueError("host target must be an IP address or valid hostname")
            return target.lower()


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
