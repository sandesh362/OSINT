"""Stable request and report models for the report engine."""

from datetime import datetime
from ipaddress import IPv4Address, IPv6Address
import re
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.features.breach_check.schemas import EMAIL_PATTERN
from app.features.domain_intel.schemas import DOMAIN_PATTERN
from app.features.social_profiling.schemas import USERNAME_PATTERN


ModuleName = Literal["domain_intel", "network_recon", "social_profiling", "breach_check"]
ReportFormat = Literal["html", "pdf"]
SectionStatus = Literal["complete", "empty", "unavailable", "not_requested", "skipped"]


class ReportRequest(BaseModel):
    """Inputs and requested feature modules for one in-process report."""

    domain: str | None = Field(default=None, max_length=253)
    email: str | None = Field(default=None, max_length=254)
    username: str | None = Field(default=None, max_length=39)
    ip: IPv4Address | IPv6Address | None = None
    modules: list[ModuleName] = Field(min_length=1, max_length=4)
    format: ReportFormat = "html"

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower().rstrip(".")
        if not DOMAIN_PATTERN.fullmatch(normalized):
            raise ValueError("domain must be a valid public domain name")
        return normalized

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if not EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("email must be a well-formed email address")
        return normalized

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not re.fullmatch(USERNAME_PATTERN, value):
            raise ValueError("username must contain only safe username characters")
        return value

    @field_validator("modules")
    @classmethod
    def unique_modules(cls, value: list[ModuleName]) -> list[ModuleName]:
        if len(value) != len(set(value)):
            raise ValueError("modules must not contain duplicates")
        return value


class ReportTarget(BaseModel):
    domain: str | None = None
    email: str | None = None
    username: str | None = None
    ip: str | None = None


class ReportSection(BaseModel):
    """Provider-neutral section consumed by every export generator."""

    module: ModuleName
    title: str
    status: SectionStatus
    summary: str
    data: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None


class InvestigationReport(BaseModel):
    report_id: str
    target: ReportTarget
    generated_at: datetime
    requested_modules: list[ModuleName]
    sections: list[ReportSection]
    findings: list[str]
    limitations: str


class HtmlReportData(BaseModel):
    report_id: str
    html: str


class PreviewData(BaseModel):
    report_id: str
    html: str
