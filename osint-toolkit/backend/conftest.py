"""Fixtures shared by all backend tests, including feature-level test folders."""

import socket

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture(autouse=True)
def block_real_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail tests that accidentally attempt a real TCP connection."""
    original_connect = socket.socket.connect

    def blocked_connect(self: socket.socket, address: object) -> None:
        if isinstance(address, tuple) and address[0] in {"127.0.0.1", "::1"}:
            original_connect(self, address)
            return
        raise AssertionError(f"Real network access is prohibited in tests: {address!r}")

    monkeypatch.setattr(socket.socket, "connect", blocked_connect)


@pytest.fixture
def client() -> TestClient:
    """Return an isolated application with dependency overrides reset."""
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
