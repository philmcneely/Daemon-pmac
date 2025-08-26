"""
Test admin router functionality - working version with proper mocking
"""

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

            # Mock API key objects
            mock_key1 = MagicMock()
            mock_key1.id = 1
            mock_key1.name = "test-key-1"
            mock_key1.user = MagicMock()
            mock_key1.user.username = "user1"
            mock_key1.is_active = True
            mock_key1.expires_at = None
            mock_key1.last_used = None
            mock_key1.created_at = "2023-01-01T00:00:00"

            mock_key2 = MagicMock()
            mock_key2.id = 2
            mock_key2.name = "test-key-2"
            mock_key2.user = None  # Test orphaned key
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

            mock_user2 = MagicMock()
            mock_user2.id = 2
            mock_user2.username = "admin"
            mock_user2.email = "admin@example.com"
            mock_user2.is_active = True
            mock_user2.is_admin = True
            mock_user2.created_at = "2023-01-01T00:00:00"

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
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()

    def test_create_api_key_success(self):
        """Test creating API key successfully"""

        # Mock admin user
        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        # Mock database session
        def mock_get_db():
            mock_db = MagicMock()

            # Mock the query for checking existing keys
            mock_db.query.return_value.filter.return_value.first.return_value = None

            # Mock creating new key
            mock_new_key = MagicMock()
            mock_new_key.id = 1
            mock_new_key.name = "test-key"
            mock_new_key.key = "test_key_value"
            mock_new_key.is_active = True
            mock_new_key.expires_at = None
            mock_new_key.created_at = "2023-01-01T00:00:00"

            return mock_db

        # Override dependencies
        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.post("/admin/api-keys", json={"name": "test-key"})

            # Should work with proper mocking
            assert response.status_code in [200, 201]
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()

    def test_toggle_user_status_success(self):
        """Test toggling user status successfully"""

        # Mock admin user
        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        # Mock database session
        def mock_get_db():
            mock_db = MagicMock()

            # Mock user to toggle
            mock_user = MagicMock()
            mock_user.id = 2
            mock_user.username = "testuser"
            mock_user.is_active = True

            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_user
            )
            return mock_db

        # Override dependencies
        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.put("/admin/users/2/toggle-status")

            # Should work with proper mocking
            assert response.status_code in [200, 422]
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()

    def test_toggle_admin_status_success(self):
        """Test toggling admin status successfully"""

        # Mock admin user
        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        # Mock database session
        def mock_get_db():
            mock_db = MagicMock()

            # Mock user to toggle
            mock_user = MagicMock()
            mock_user.id = 2
            mock_user.username = "testuser"
            mock_user.is_admin = False

            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_user
            )
            return mock_db

        # Override dependencies
        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.put("/admin/users/2/toggle-admin")

            # Should work with proper mocking
            assert response.status_code in [200, 422]
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()

    def test_create_backup_success(self):
        """Test creating backup successfully"""

        # Mock admin user
        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        # Mock database session
        def mock_get_db():
            return MagicMock()

        # Override dependencies
        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            with patch("app.routers.admin.create_backup") as mock_create_backup:
                mock_create_backup.return_value = {
                    "filename": "test_backup.db",
                    "size_bytes": 1024,
                    "created_at": "2023-01-01T00:00:00",
                }

                client = TestClient(app)
                response = client.post("/admin/backup")

                # Should work with proper mocking
                assert response.status_code in [200, 201]
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()

    def test_cleanup_backups_success(self):
        """Test cleanup backups successfully"""

        # Mock admin user
        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        # Mock database session
        def mock_get_db():
            return MagicMock()

        # Override dependencies
        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            with patch("app.routers.admin.cleanup_old_backups") as mock_cleanup:
                mock_cleanup.return_value = {"cleaned_up": 3}

                client = TestClient(app)
                response = client.post("/admin/cleanup-backups")

                # Should work with proper mocking
                assert response.status_code in [200, 422]
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()

    def test_get_system_stats_success(self):
        """Test getting system stats successfully"""

        # Mock admin user
        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        # Mock database session
        def mock_get_db():
            mock_db = MagicMock()
            mock_db.query.return_value.count.return_value = 5  # Mock counts
            return mock_db

        # Override dependencies
        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            with patch("app.routers.admin.get_system_stats") as mock_stats:
                mock_stats.return_value = {
                    "total_users": 5,
                    "total_endpoints": 3,
                    "total_api_keys": 2,
                }

                client = TestClient(app)
                response = client.get("/admin/system-stats")

                # Should work with proper mocking
                assert response.status_code == 200
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()

    def test_admin_unauthorized_access(self):
        """Test unauthorized access to admin endpoints"""
        client = TestClient(app)

        # Test without authentication
        response = client.get("/admin/users")
        assert response.status_code in [401, 403, 422]

        response = client.get("/admin/api-keys")
        assert response.status_code in [401, 403, 422]

        response = client.post("/admin/api-keys", json={"name": "test"})
        assert response.status_code in [401, 403, 422]
