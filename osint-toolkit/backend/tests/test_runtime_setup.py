"""Regression checks for local startup, configuration and independent reports."""

import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.features.domain_intel.client import DomainIntelClient
from app.features.domain_intel.schemas import DnsData, WhoisData
from app.features.report_engine.schemas import ReportRequest
from app.features.report_engine.service import ReportEngineService


def test_backend_home_opens_documentation(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/docs"
    assert client.get("/docs").status_code == 200


def test_health_endpoint_is_available_for_frontend(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_env_path_does_not_depend_on_launch_directory(tmp_path, monkeypatch):
    env_file = Path(Settings.model_config["env_file"])
    assert env_file.is_absolute()
    assert env_file.parent.name == "backend"
    monkeypatch.chdir(tmp_path)
    assert Path(Settings.model_config["env_file"]) == env_file


def test_settings_read_bom_env_and_honor_process_overrides(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("APP_NAME=From env file\nWHOIS_TIMEOUT_SECONDS=7\n", encoding="utf-8-sig")
    monkeypatch.delenv("WHOIS_TIMEOUT_SECONDS", raising=False)
    monkeypatch.setenv("APP_NAME", "From process")
    settings = Settings(_env_file=env_file)
    assert settings.app_name == "From process"
    assert settings.whois_timeout_seconds == 7


@pytest.mark.parametrize("field", ["dns_timeout_seconds", "dns_lifetime_seconds", "whois_timeout_seconds"])
def test_nonpositive_timeouts_are_rejected(field):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{field: 0})


def test_whois_uses_configured_timeout(monkeypatch):
    observed = {}

    def lookup(domain, **kwargs):
        observed.update(domain=domain, **kwargs)
        return SimpleNamespace(domain_name=domain, registrar="Test registrar")

    monkeypatch.setattr("app.features.domain_intel.client.whois.whois", lookup)
    DomainIntelClient().fetch_whois("example.com")
    assert observed == {"domain": "example.com", "timeout": get_settings().whois_timeout_seconds}


class FakeDomainService:
    def whois(self, domain):
        return WhoisData(registrar="Test registrar")

    def dns(self, domain):
        return DnsData(a=["192.0.2.1"])


def test_domain_report_works_without_optional_shodan_key(monkeypatch):
    monkeypatch.setattr(get_settings(), "shodan_api_key", "")
    service = ReportEngineService(domain_service=FakeDomainService(), cache={})
    report = asyncio.run(service.generate(ReportRequest(domain="example.com", modules=["domain_intel"])))
    assert next(section for section in report.sections if section.module == "domain_intel").status == "complete"


def test_missing_shodan_key_only_affects_network_report_section(monkeypatch):
    monkeypatch.setattr(get_settings(), "shodan_api_key", "")
    service = ReportEngineService(domain_service=FakeDomainService(), cache={})
    report = asyncio.run(service.generate(ReportRequest(domain="example.com", ip="1.1.1.1", modules=["domain_intel", "network_recon"])))
    statuses = {section.module: section.status for section in report.sections}
    assert statuses["domain_intel"] == "complete"
    assert statuses["network_recon"] == "unavailable"
