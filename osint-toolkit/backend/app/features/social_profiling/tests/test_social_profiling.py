"""Social profiling tests with mocked HTTP transports only."""

import httpx
from fastapi.testclient import TestClient

from app.features.social_profiling.client import SocialProfilingClient
from app.features.social_profiling.platforms import PLATFORMS
from app.features.social_profiling.router import get_social_profiling_service
from app.features.social_profiling.service import SocialProfilingService


def set_service(client: TestClient, service: SocialProfilingService) -> None:
    client.app.dependency_overrides[get_social_profiling_service] = lambda: service


def mocked_service(handler: httpx.MockTransport, cache: dict | None = None) -> SocialProfilingService:
    http_client = httpx.AsyncClient(transport=handler, headers={"User-Agent": "test"})
    return SocialProfilingService(SocialProfilingClient(http_client), cache={} if cache is None else cache)


def test_username_found_on_all_platforms(client: TestClient) -> None:
    calls = []
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url)
        return httpx.Response(200, text="<title>someuser profile</title>", request=request)
    set_service(client, mocked_service(httpx.MockTransport(handler)))
    response = client.get("/api/v1/social-profiling/username", params={"value": "someuser"})
    assert response.status_code == 200
    assert {result["status"] for result in response.json()["data"]["results"]} == {"found"}
    assert len(calls) == len(PLATFORMS)


def test_username_not_found_anywhere(client: TestClient) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, request=request)
    set_service(client, mocked_service(httpx.MockTransport(handler)))
    body = client.get("/api/v1/social-profiling/username", params={"value": "nobody"}).json()
    assert {result["status"] for result in body["data"]["results"]} == {"not_found"}


def test_mixed_results_and_soft_404(client: TestClient) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "github.com" in str(request.url):
            return httpx.Response(200, text="<title>profile</title>", request=request)
        if "gitlab.com" in str(request.url):
            return httpx.Response(200, text="<h1>Page not found</h1>", request=request)
        return httpx.Response(503, request=request)
    set_service(client, mocked_service(httpx.MockTransport(handler)))
    results = client.get("/api/v1/social-profiling/username", params={"value": "mixed"}).json()["data"]["results"]
    assert results[0]["status"] == "found"
    assert results[1]["status"] == "not_found"
    assert {result["status"] for result in results[2:]} == {"uncertain"}


def test_invalid_username_returns_422_before_outbound_work(client: TestClient) -> None:
    response = client.get("/api/v1/social-profiling/username", params={"value": "bad/name"})
    assert response.status_code == 422


def test_one_platform_timeout_is_uncertain(client: TestClient) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "github.com" in str(request.url):
            raise httpx.ReadTimeout("timeout", request=request)
        return httpx.Response(404, request=request)
    set_service(client, mocked_service(httpx.MockTransport(handler)))
    results = client.get("/api/v1/social-profiling/username", params={"value": "timeout"}).json()["data"]["results"]
    assert results[0]["status"] == "uncertain"
    assert {result["status"] for result in results[1:]} == {"not_found"}


def test_cache_hit_does_not_reissue_http_calls(client: TestClient) -> None:
    calls = 0
    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(404, request=request)
    set_service(client, mocked_service(httpx.MockTransport(handler)))
    for _ in range(2):
        response = client.get("/api/v1/social-profiling/username", params={"value": "cached"})
        assert response.status_code == 200
    assert calls == len(PLATFORMS)
