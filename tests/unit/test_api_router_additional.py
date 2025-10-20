"""
Module: tests.unit.test_api_router_additional
Description: Additional unit tests for API router endpoints and functionality

Author: pmac
Created: 2025-10-20
Modified: 2025-10-20

Dependencies:
- pytest: 7.4.3+ - Testing framework
- fastapi: 0.104.1+ - TestClient for API testing
- sqlalchemy: 2.0+ - Database operations in tests

Usage:
    pytest tests/unit/test_api_router_additional.py -v

Notes:
    - Comprehensive test coverage for API router endpoints
    - Mock database operations for isolated testing
    - Test both single-user and multi-user scenarios
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestAPIRouterEndpoints:
    """Test API router endpoint functionality using TestClient"""

    def test_get_endpoint_data_success(self):
        """Test successful retrieval of endpoint data using TestClient"""
        # Mock database operations
        with patch("app.routers.api.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            # Mock endpoint
            mock_endpoint = MagicMock()
            mock_endpoint.name = "resume"
            mock_endpoint.is_active = True
            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_endpoint
            )

            # Mock data item
            mock_data = MagicMock()
            mock_data.id = 1
            mock_data.data = {"name": "Test User", "title": "Developer"}
            mock_db.query.return_value.filter.return_value.all.return_value = [
                mock_data
            ]

            # Mock is_single_user_mode to return True
            with patch("app.utils.is_single_user_mode", return_value=True):
                client = TestClient(app)
                response = client.get("/api/v1/resume")

            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert len(data["items"]) == 1

    def test_get_endpoint_data_not_found(self):
        """Test endpoint data retrieval when endpoint not found"""
        with patch("app.routers.api.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            # Mock endpoint not found
            mock_db.query.return_value.filter.return_value.first.return_value = None

            # Mock is_single_user_mode to return True
            with patch("app.utils.is_single_user_mode", return_value=True):
                client = TestClient(app)
                response = client.get("/api/v1/nonexistent")

            assert response.status_code == 404
            assert "Endpoint 'nonexistent' not found" in response.json()["detail"]

    def test_get_specific_user_data_universal_success(self):
        """Test successful retrieval of specific user data"""
        with patch("app.routers.api.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            # Mock user
            mock_user = MagicMock()
            mock_user.username = "testuser"
            mock_user.is_active = True
            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_user
            )

            # Mock endpoint
            mock_endpoint = MagicMock()
            mock_endpoint.name = "resume"
            mock_endpoint.is_active = True
            mock_endpoint.is_public = True
            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_endpoint
            )

            # Mock data
            mock_data = MagicMock()
            mock_data.data = {"name": "Test User"}
            mock_db.query.return_value.filter.return_value.all.return_value = [
                mock_data
            ]

            # Mock is_single_user_mode to return False (multi-user mode)
            with patch("app.utils.is_single_user_mode", return_value=False):
                client = TestClient(app)
                response = client.get("/api/v1/resume/users/testuser")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1

    def test_get_specific_user_data_user_not_found(self):
        """Test specific user data retrieval when user not found"""
        with patch("app.routers.api.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            # Mock user not found
            mock_db.query.return_value.filter.return_value.first.return_value = None

            # Mock is_single_user_mode to return False (multi-user mode)
            with patch("app.utils.is_single_user_mode", return_value=False):
                client = TestClient(app)
                response = client.get("/api/v1/resume/users/nonexistent")

            assert response.status_code == 404
            assert "User 'nonexistent' not found" in response.json()["detail"]

    def test_get_endpoint_data_empty_result(self):
        """Test endpoint data retrieval with empty results"""
        with patch("app.routers.api.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            # Mock endpoint exists
            mock_endpoint = MagicMock()
            mock_endpoint.name = "resume"
            mock_endpoint.is_active = True
            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_endpoint
            )

            # Mock empty data
            mock_db.query.return_value.filter.return_value.all.return_value = []

            # Mock is_single_user_mode to return True
            with patch("app.utils.is_single_user_mode", return_value=True):
                client = TestClient(app)
                response = client.get("/api/v1/resume")

            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert len(data["items"]) == 0

    def test_get_endpoint_data_public_endpoint(self):
        """Test data retrieval for public endpoints"""
        with patch("app.routers.api.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            # Mock public endpoint
            mock_endpoint = MagicMock()
            mock_endpoint.name = "about"
            mock_endpoint.is_active = True
            mock_endpoint.is_public = True
            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_endpoint
            )

            # Mock data
            mock_data = MagicMock()
            mock_data.data = {"name": "Public Data"}
            mock_db.query.return_value.filter.return_value.all.return_value = [
                mock_data
            ]

            # Mock is_single_user_mode to return True
            with patch("app.utils.is_single_user_mode", return_value=True):
                client = TestClient(app)
                response = client.get("/api/v1/about")

            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert len(data["items"]) == 1

    def test_get_specific_user_data_public_access(self):
        """Test specific user data retrieval with public access"""
        with patch("app.routers.api.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            # Mock user
            mock_user = MagicMock()
            mock_user.username = "publicuser"
            mock_user.is_active = True
            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_user
            )

            # Mock public endpoint
            mock_endpoint = MagicMock()
            mock_endpoint.name = "about"
            mock_endpoint.is_active = True
            mock_endpoint.is_public = True
            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_endpoint
            )

            # Mock data
            mock_data = MagicMock()
            mock_data.data = {"name": "Public User Data"}
            mock_db.query.return_value.filter.return_value.all.return_value = [
                mock_data
            ]

            # Mock is_single_user_mode to return False (multi-user mode)
            with patch("app.utils.is_single_user_mode", return_value=False):
                client = TestClient(app)
                response = client.get("/api/v1/about/users/publicuser")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1


class TestAPIRouterEdgeCases:
    """Test edge cases and error handling in API router"""

    def test_get_endpoint_data_multiple_items(self):
        """Test endpoint data retrieval with multiple items"""
        with patch("app.routers.api.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            # Mock endpoint
            mock_endpoint = MagicMock()
            mock_endpoint.name = "projects"
            mock_endpoint.is_active = True
            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_endpoint
            )

            # Mock multiple data items
            mock_data1 = MagicMock()
            mock_data1.id = 1
            mock_data1.data = {"name": "Project 1", "description": "First project"}

            mock_data2 = MagicMock()
            mock_data2.id = 2
            mock_data2.data = {"name": "Project 2", "description": "Second project"}

            mock_db.query.return_value.filter.return_value.all.return_value = [
                mock_data1,
                mock_data2,
            ]

            # Mock is_single_user_mode to return True
            with patch("app.utils.is_single_user_mode", return_value=True):
                client = TestClient(app)
                response = client.get("/api/v1/projects")

            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert len(data["items"]) == 2

    def test_get_specific_user_data_endpoint_not_found(self):
        """Test specific user data retrieval when endpoint not found"""
        with patch("app.routers.api.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            # Mock user exists
            mock_user = MagicMock()
            mock_user.username = "testuser"
            mock_user.is_active = True
            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_user
            )

            # Mock endpoint not found
            mock_db.query.return_value.filter.return_value.first.return_value = None

            # Mock is_single_user_mode to return False (multi-user mode)
            with patch("app.utils.is_single_user_mode", return_value=False):
                client = TestClient(app)
                response = client.get("/api/v1/nonexistent/users/testuser")

            assert response.status_code == 404
            assert "Endpoint 'nonexistent' not found" in response.json()["detail"]

    def test_get_specific_user_data_empty_result(self):
        """Test specific user data retrieval with empty results"""
        with patch("app.routers.api.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            # Mock user exists
            mock_user = MagicMock()
            mock_user.username = "testuser"
            mock_user.is_active = True
            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_user
            )

            # Mock endpoint exists
            mock_endpoint = MagicMock()
            mock_endpoint.name = "resume"
            mock_endpoint.is_active = True
            mock_endpoint.is_public = True
            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_endpoint
            )

            # Mock empty data
            mock_db.query.return_value.filter.return_value.all.return_value = []

            # Mock is_single_user_mode to return False (multi-user mode)
            with patch("app.utils.is_single_user_mode", return_value=False):
                client = TestClient(app)
                response = client.get("/api/v1/resume/users/testuser")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 0
