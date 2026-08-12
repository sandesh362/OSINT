"""Unit tests for domain intelligence HTTP behavior, with no network access."""

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.core.exceptions import LookupNotFoundError, LookupTimeoutError
from app.features.domain_intel.router import get_domain_intel_service
from app.features.domain_intel.schemas import DnsData, WhoisData
from app.features.domain_intel.service import DomainIntelService


class FakeClient:
    def fetch_whois(self, domain: str) -> WhoisData:
        return WhoisData(
            registrar="Example Registrar",
            creation_date=datetime(2020, 1, 1, tzinfo=timezone.utc),
            expiration_date=datetime(2030, 1, 1, tzinfo=timezone.utc),
            name_servers=["ns1.example.com"],
            registrant_org="Example Org",
        )

    def fetch_dns(self, domain: str) -> DnsData:
        return DnsData(a=["93.184.216.34"], ns=["a.iana-servers.net"])


def set_service(client: TestClient, service: object) -> None:
    client.app.dependency_overrides[get_domain_intel_service] = lambda: service


def test_whois_valid_domain_returns_mocked_data(client: TestClient) -> None:
    set_service(client, DomainIntelService(FakeClient()))
    response = client.get("/api/v1/domain-intel/whois", params={"domain": "example.com"})
    assert response.status_code == 200
    assert response.json()["data"]["registrar"] == "Example Registrar"


def test_invalid_domain_format_returns_422(client: TestClient) -> None:
    response = client.get("/api/v1/domain-intel/dns", params={"domain": "not a domain"})
    assert response.status_code == 422


def test_non_resolving_domain_returns_404(client: TestClient) -> None:
    class NotFoundClient(FakeClient):
        def fetch_dns(self, domain: str) -> DnsData:
            raise LookupNotFoundError("Domain does not resolve")

    set_service(client, DomainIntelService(NotFoundClient()))
    response = client.get("/api/v1/domain-intel/dns", params={"domain": "missing.example"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_whois_timeout_returns_504(client: TestClient) -> None:
    class TimeoutClient(FakeClient):
        def fetch_whois(self, domain: str) -> WhoisData:
            raise LookupTimeoutError("WHOIS lookup timed out")

    set_service(client, DomainIntelService(TimeoutClient()))
    response = client.get("/api/v1/domain-intel/whois", params={"domain": "example.com"})
    assert response.status_code == 504
    assert response.json()["error"]["code"] == "upstream_timeout"


def test_dns_response_uses_consistent_envelope(client: TestClient) -> None:
    set_service(client, DomainIntelService(FakeClient()))
    body = client.get("/api/v1/domain-intel/dns", params={"domain": "example.com"}).json()
    assert body["success"] is True
    assert set(body) == {"success", "data", "meta", "error"}
    assert body["error"] is None
    assert "queried_at" in body["meta"]
