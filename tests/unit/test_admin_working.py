"""
Test admin router functionality - working version with proper mocking
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.routers.admin import get_current_admin_user


class TestAdminRouter:
    """Test admin router functionality with proper mocking"""

    def test_list_api_keys_success(self):
        """Test listing API keys successfully"""

        # Mock admin user
        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        # Mock database session and API keys
        def mock_get_db():
            mock_db = MagicMock()

            # Mock API key objects - all keys must have users
            mock_key1 = MagicMock()
            mock_key1.id = 1
            mock_key1.name = "test-key-1"
            mock_key1.user_id = 1
            mock_key1.user = MagicMock()
            mock_key1.user.username = "user1"
            mock_key1.is_active = True
            mock_key1.expires_at = None
            mock_key1.last_used = None
            mock_key1.created_at = "2023-01-01T00:00:00"

            mock_key2 = MagicMock()
            mock_key2.id = 2
            mock_key2.name = "test-key-2"
            mock_key2.user_id = 2
            mock_key2.user = MagicMock()
            mock_key2.user.username = "user2"
            mock_key2.is_active = True
            mock_key2.expires_at = None
            mock_key2.last_used = None
            mock_key2.created_at = "2023-01-02T00:00:00"

            mock_db.query.return_value.all.return_value = [mock_key1, mock_key2]
            return mock_db

        # Override dependencies
        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.get("/admin/api-keys")

            # Should work with proper mocking
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 2
            assert data[0]["name"] == "test-key-1"
            assert data[1]["name"] == "test-key-2"
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()

    def test_list_users_success(self):
        """Test listing users successfully"""

        # Mock admin user
        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        # Mock database session and users
        def mock_get_db():
            mock_db = MagicMock()

            # Mock user objects
            mock_user1 = MagicMock()
            mock_user1.id = 1
            mock_user1.username = "user1"
            mock_user1.email = "user1@example.com"
            mock_user1.is_active = True
            mock_user1.is_admin = False
            mock_user1.created_at = "2023-01-01T00:00:00"
            mock_user1.last_login = None

            mock_user2 = MagicMock()
            mock_user2.id = 2
            mock_user2.username = "admin"
            mock_user2.email = "admin@example.com"
            mock_user2.is_active = True
            mock_user2.is_admin = True
            mock_user2.created_at = "2023-01-01T00:00:00"
            mock_user2.last_login = None

            mock_db.query.return_value.all.return_value = [mock_user1, mock_user2]
            return mock_db

        # Override dependencies
        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.get("/admin/users")

            # Should work with proper mocking
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 2
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()
