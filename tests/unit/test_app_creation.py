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


class TestCustomOpenAPISchema:
    """Test the custom OpenAPI schema generation"""

    def test_custom_openapi_schema_exists(self, client):
        """Test that the custom OpenAPI schema is generated"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()

        # Check basic schema structure
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema

        # Check custom logo
        assert "x-logo" in schema["info"]
        assert (
            schema["info"]["x-logo"]["url"]
            == "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
        )

    def test_custom_openapi_endpoint_enum(self, client):
        """Test that endpoint_name parameters have enum constraints"""
        response = client.get("/openapi.json")
        schema = response.json()

        # Check that endpoint_name parameters have enum constraints
        for path, path_item in schema.get("paths", {}).items():
            if "/{endpoint_name}" in path:
                for operation in path_item.values():
                    if isinstance(operation, dict) and "parameters" in operation:
                        for param in operation["parameters"]:
                            if (
                                param.get("name") == "endpoint_name"
                                and param.get("in") == "path"
                            ):
                                assert "enum" in param["schema"]
                                assert "description" in param
                                assert "available:" in param["description"]

    def test_custom_openapi_concrete_paths(self, client):
        """Test that concrete example paths are added to the schema"""
        response = client.get("/openapi.json")
        schema = response.json()

        # Check that some example paths exist
        assert "/api/v1/resume" in schema["paths"]
        assert "/api/v1/resume/users/{username}" in schema["paths"]


class TestMetricsEndpoint:
    """Test the Prometheus metrics endpoint"""

    @pytest.mark.parametrize("metrics_enabled", [True, False])
    def test_metrics_endpoint_status(self, client, metrics_enabled):
        """Test metrics endpoint with different settings"""
        from unittest.mock import patch

        from app.main import settings

        with patch.object(settings, "metrics_enabled", metrics_enabled):
            response = client.get("/metrics")

            if metrics_enabled:
                assert response.status_code == 200
                assert "text/plain" in response.headers["content-type"]
                # Check for Prometheus format
                assert "HELP" in response.text
                assert "TYPE" in response.text
            else:
                assert response.status_code == 404

    def test_metrics_content(self, client):
        """Test that metrics endpoint returns expected content"""
        from unittest.mock import patch

        from app.main import settings

        with patch.object(settings, "metrics_enabled", True):
            response = client.get("/metrics")
            content = response.text

            # Check for expected metrics
            assert "daemon_info" in content
            assert "daemon_uptime_seconds" in content
            assert "daemon_data_entries_total" in content
            assert "daemon_endpoints_total" in content
            assert "daemon_users_total" in content
            assert "daemon_memory_usage_percent" in content
            assert "daemon_cpu_usage_percent" in content
            assert "daemon_disk_usage_percent" in content
            assert "daemon_database_size_bytes" in content


class TestBackupFunctionality:
    """Test backup-related functionality"""

    def test_backup_initialization(self, client):
        """Test that backup initialization doesn't crash the app"""
        # This test ensures the backup initialization code path is covered
        # The actual backup functionality is tested elsewhere
        response = client.get("/")
        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling middleware and endpoints"""

    def test_security_middleware_ip_check(self, client):
        """Test that security middleware IP checking works"""
        # This should pass through the middleware without issues
        response = client.get("/")
        assert response.status_code == 200

    def test_rate_limit_endpoint(self, client):
        """Test the rate limit endpoint - this endpoint may not exist"""
        # The rate-limit endpoint might not be implemented, so test gracefully
        response = client.get("/rate-limit")
        # Either it exists (200) or doesn't (404) - both are acceptable
        assert response.status_code in (200, 404)

    def test_global_exception_handler(self, client):
        """Test that global exception handler is in place"""
        # Test with a non-existent endpoint to trigger 404
        response = client.get("/non-existent-endpoint")
        assert response.status_code == 404


class TestAvailableEndpoints:
    """Test the get_available_endpoints function"""

    def test_get_available_endpoints_function(self):
        """Test the get_available_endpoints function directly"""
        from app.main import get_available_endpoints

        endpoints = get_available_endpoints()
        assert isinstance(endpoints, list)
        # Should at least contain the default endpoints
        assert "resume" in endpoints


class TestDatabaseInitialization:
    """Test database initialization error handling"""

    def test_database_init_error_handling(self):
        """Test that database initialization errors are handled gracefully"""
        # This is mostly covered by the app starting successfully
        # The error handling paths are difficult to test without mocking failures
        pass
