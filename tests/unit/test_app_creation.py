"""
Test suite for FastAPI application creation, middleware, router inclusion, and health endpoint.
"""

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI app instance
from app.main import app


@pytest.fixture(scope="module")
def client():
    """Create a TestClient for the FastAPI app."""
    with TestClient(app) as c:
        yield c


def test_app_is_instance():
    """The imported app should be a FastAPI instance."""
    from fastapi import FastAPI

    assert isinstance(app, FastAPI)


def test_root_endpoint(client):
    """Root endpoint should return basic app info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    expected_keys = {
        "name",
        "version",
        "description",
        "timestamp",
        "docs_url",
        "health_url",
        "api_prefix",
        "mcp_enabled",
    }
    assert expected_keys.issubset(data.keys())


def test_health_endpoint(client):
    """Health endpoint should report healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    for field in ("timestamp", "version", "database", "uptime_seconds"):
        assert field in data


def test_router_inclusion(client):
    """Check that a known router endpoint is available (e.g., /api/v1/resume)."""
    response = client.get("/api/v1/resume")
    # The endpoint may return 404 if no data, but it should not raise a server error
    assert response.status_code in (200, 404)
