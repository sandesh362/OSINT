"""Shared test fixtures."""

import pytest
import socket
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture(autouse=True)
def block_real_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail tests that accidentally attempt a real TCP connection."""
    def blocked_connect(self: socket.socket, address: object) -> None:
        raise AssertionError(f"Real network access is prohibited in tests: {address!r}")

    monkeypatch.setattr(socket.socket, "connect", blocked_connect)


@pytest.fixture
def client() -> TestClient:
    """Return an isolated test client with dependency overrides reset."""
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
