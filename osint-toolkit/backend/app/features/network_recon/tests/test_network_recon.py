"""Network reconnaissance API tests using a fake Shodan client only."""

from fastapi.testclient import TestClient

from app.core.exceptions import LookupNotFoundError, ShodanRateLimitError
from app.features.network_recon.router import get_network_recon_service
from app.features.network_recon.service import NetworkReconService


class FakeShodanClient:
    def __init__(self) -> None:
        self.host_calls = 0
        self.search_calls: list[tuple[str, int]] = []

    def host(self, ip: str) -> dict[str, object]:
        self.host_calls += 1
        return {
            "ip_str": ip, "ports": [80, 443], "org": "Example Org", "isp": "Example ISP",
            "os": "Linux", "last_update": "2025-01-01T00:00:00.000000",
            "location": {"country_name": "United States", "city": "Ashburn"},
            "data": [{"port": 80, "transport": "tcp", "product": "nginx", "version": "1.24"}],
        }

    def search(self, query: str, page: int) -> dict[str, object]:
        self.search_calls.append((query, page))
        return {
            "total": 25,
            "matches": [
                {"ip_str": f"192.0.2.{index}", "port": 80, "org": "Example Org", "location": {}}
                for index in range(1, 26)
            ],
        }


def set_service(client: TestClient, service: NetworkReconService) -> None:
    client.app.dependency_overrides[get_network_recon_service] = lambda: service


def test_host_valid_ip_returns_mocked_shodan_data(client: TestClient) -> None:
    set_service(client, NetworkReconService(FakeShodanClient(), cache={}))
    response = client.get("/api/v1/network-recon/host", params={"ip": "1.2.3.4"})
    assert response.status_code == 200
    assert response.json()["data"]["open_ports"] == [80, 443]
    assert response.json()["data"]["services"][0]["product"] == "nginx"


def test_host_with_no_shodan_data_returns_404(client: TestClient) -> None:
    class NoDataClient(FakeShodanClient):
        def host(self, ip: str) -> dict[str, object]:
            raise LookupNotFoundError("No Shodan information is available for this IP")

    set_service(client, NetworkReconService(NoDataClient(), cache={}))
    response = client.get("/api/v1/network-recon/host", params={"ip": "1.2.3.4"})
    assert response.status_code == 404
    assert response.json()["error"] == "not_found"


def test_invalid_ip_format_returns_422(client: TestClient) -> None:
    response = client.get("/api/v1/network-recon/host", params={"ip": "not-an-ip"})
    assert response.status_code == 422


def test_rate_limited_search_returns_429(client: TestClient) -> None:
    class RateLimitedClient(FakeShodanClient):
        def search(self, query: str, page: int) -> dict[str, object]:
            raise ShodanRateLimitError("Shodan request quota has been reached")

    set_service(client, NetworkReconService(RateLimitedClient(), cache={}))
    response = client.get("/api/v1/network-recon/search", params={"query": "product:nginx"})
    assert response.status_code == 429
    assert response.json()["error"] == "rate_limit_exceeded"


def test_search_caps_results_and_passes_page_to_client(client: TestClient) -> None:
    fake = FakeShodanClient()
    set_service(client, NetworkReconService(fake, cache={}))
    response = client.get(
        "/api/v1/network-recon/search", params={"query": "org:Example", "page": 2}
    )
    assert response.status_code == 200
    assert response.json()["data"]["page"] == 2
    assert len(response.json()["data"]["results"]) == 20
    assert fake.search_calls == [("org:Example", 2)]
