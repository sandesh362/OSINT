"""Shared test fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    """Return an isolated test client with dependency overrides reset."""
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
