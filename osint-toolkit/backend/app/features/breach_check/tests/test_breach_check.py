"""Breach-check tests using fakes; no test makes a provider network request."""

import pytest

from fastapi.testclient import TestClient

from app.core.exceptions import BreachRateLimitError, BreachUnavailableError
from app.features.breach_check.client import XposedOrNotClient
from app.features.breach_check.router import get_breach_check_service
from app.features.breach_check.schemas import BreachSummary
from app.features.breach_check.service import BreachCheckService


class FakeXposedOrNotClient:
    def __init__(self, result: list[BreachSummary] | Exception) -> None:
        self.result = result
        self.calls = 0

    async def breaches_for_email(self, email: str) -> list[BreachSummary]:
        self.calls += 1
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


@pytest.fixture
def xposedornot_real_response() -> dict[str, object]:
    """Provider payload fields copied from the supplied live XposedOrNot response."""
    return {
        "BreachMetrics": {"risk": [{"risk_label": "Critical", "risk_score": 98}]},
        "BreachesSummary": {"site": "AlienStealerLogs;ZenBusiness"},
        "ExposedBreaches": {"breaches_details": [
            {"breach": "AlienStealerLogs", "details": "ALIEN TXTBASE, a stealer log collection.", "domain": "", "password_risk": "plaintext", "xposed_data": "Email addresses;Passwords", "xposed_date": "2025", "xposed_records": 299646818},
            {"breach": "ZenBusiness", "details": "ZenBusiness incident summary.", "domain": "zenbusiness.com", "password_risk": "unknown", "xposed_data": "Email addresses;Names;Usernames;Phone numbers;Physical addresses", "xposed_date": "2026", "xposed_records": 11854655},
            {"breach": "Malformed", "xposed_date": "2024", "xposed_data": ["not a string"], "details": "This entry must be skipped."},
        ]},
        "ExposedPastes": None,
        "PasteMetrics": None,
        "PastesSummary": {"cnt": 0, "domain": "", "tmpstmp": ""},
    }


def set_service(client: TestClient, service: BreachCheckService) -> None:
    client.app.dependency_overrides[get_breach_check_service] = lambda: service


def test_breached_address_returns_multiple_safe_summaries(client: TestClient) -> None:
    provider = FakeXposedOrNotClient([
        BreachSummary(name="Adobe", breach_date="2013-10-04", data_classes=["Email addresses", "Passwords"], description="Adobe breach."),
        BreachSummary(name="Gawker", breach_date="2010-12-11", data_classes=["Email addresses"], description="Gawker breach."),
    ])
    set_service(client, BreachCheckService(provider, cache={}))
    response = client.get("/api/v1/breach-check/email", params={"value": "someone@example.com"})
    body = response.json()
    assert response.status_code == 200
    assert body["data"]["breached"] is True
    assert len(body["data"]["breaches"]) == 2
    assert set(body["data"]["breaches"][0]) == {"name", "breach_date", "data_classes", "description"}


def test_clean_address_returns_false_and_an_empty_list(client: TestClient) -> None:
    set_service(client, BreachCheckService(FakeXposedOrNotClient([]), cache={}))
    body = client.get("/api/v1/breach-check/email", params={"value": "clean@example.com"}).json()
    assert body["data"] == {"value": "clean@example.com", "breached": False, "breaches": []}


def test_invalid_email_returns_422_before_provider_work(client: TestClient) -> None:
    response = client.get("/api/v1/breach-check/email", params={"value": "not-an-email"})
    assert response.status_code == 422


def test_provider_rate_limit_returns_429(client: TestClient) -> None:
    set_service(client, BreachCheckService(FakeXposedOrNotClient(BreachRateLimitError("Rate limit reached, try again later", retry_after=2)), cache={}))
    response = client.get("/api/v1/breach-check/email", params={"value": "limited@example.com"})
    assert response.status_code == 429
    assert response.json()["error"]["code"] == "rate_limit_exceeded"


def test_provider_503_returns_unavailable_message(client: TestClient) -> None:
    set_service(client, BreachCheckService(FakeXposedOrNotClient(BreachUnavailableError("Breach data temporarily unavailable")), cache={}))
    response = client.get("/api/v1/breach-check/email", params={"value": "offline@example.com"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "provider_unavailable"


def test_cache_hit_does_not_reissue_provider_call(client: TestClient) -> None:
    provider = FakeXposedOrNotClient([])
    set_service(client, BreachCheckService(provider, cache={}))
    for _ in range(2):
        assert client.get("/api/v1/breach-check/email", params={"value": "cached@example.com"}).status_code == 200
    assert provider.calls == 1


def test_xposedornot_real_response_is_mapped_to_safe_fields(xposedornot_real_response: dict[str, object]) -> None:
    result = XposedOrNotClient._to_summaries(xposedornot_real_response)
    assert result[0].model_dump() == {"name": "AlienStealerLogs", "breach_date": "2025", "data_classes": ["Email addresses", "Passwords"], "description": "ALIEN TXTBASE, a stealer log collection."}
    assert result[1].data_classes == ["Email addresses", "Names", "Usernames", "Phone numbers", "Physical addresses"]
    assert len(result) == 2
