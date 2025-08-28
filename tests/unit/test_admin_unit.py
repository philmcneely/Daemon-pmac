"""
Test admin router functionality - Unit tests with mocked database
"""

from unittest.mock import MagicMock, patch

import pytest


class TestAdminRouterUnit:
    """Unit tests for admin router with mocked dependencies"""

    def test_toggle_user_status_success(
        self, unit_client, unit_admin_user, unit_auth_headers
    ):
        """Test successful user status toggle"""
        # Create a regular user to toggle
        regular_user_data = {
            "username": "regular_user",
            "email": "regular@test.com",
            "password": "testpass",
        }

        # First create the user
        response = unit_client.post("/auth/register", json=regular_user_data)
        assert response.status_code == 200  # Registration returns 200, not 201

        # Get the user ID by listing users
        response = unit_client.get("/admin/users", headers=unit_auth_headers)
        assert response.status_code == 200
        users = response.json()

        # Find the regular user
        regular_user = next((u for u in users if u["username"] == "regular_user"), None)
        assert regular_user is not None
        user_id = regular_user["id"]

        # Toggle user status using the correct endpoint format
        response = unit_client.put(
            f"/admin/users/{user_id}/toggle", headers=unit_auth_headers
        )
        assert response.status_code == 200

    def test_get_system_stats_success(
        self, unit_client, unit_admin_user, unit_auth_headers
    ):
        """Test successful system stats retrieval"""
        response = unit_client.get("/admin/data/stats", headers=unit_auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "endpoints" in data
        assert "totals" in data
        assert "active_entries" in data["totals"]
        assert "total_entries" in data["totals"]
        assert "endpoints_count" in data["totals"]

    def test_get_system_info_success(
        self, unit_client, unit_admin_user, unit_auth_headers
    ):
        """Test successful system info retrieval"""
        response = unit_client.get("/admin/system", headers=unit_auth_headers)
        assert response.status_code == 200

        data = response.json()
        # Based on the actual response structure
        assert "application" in data
        assert "system" in data
        assert "database_size" in data["application"]
