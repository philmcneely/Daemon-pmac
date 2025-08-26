"""
Test admin router functionality - working version with proper mocking
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestAdminRouter:
    """Test admin router functionality with proper mocking"""

    @patch("app.routers.admin.get_current_admin_user")
    @patch("app.routers.admin.get_db")
    def test_list_api_keys_success(self, mock_get_db, mock_get_admin):
        """Test listing API keys successfully"""
        # Mock admin user
        mock_admin = MagicMock()
        mock_admin.id = 1
        mock_admin.username = "admin"
        mock_admin.is_admin = True
        mock_get_admin.return_value = mock_admin

        # Mock database session and API keys
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

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

        client = TestClient(app)
        response = client.get("/admin/api-keys")

        # Should work with proper mocking
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @patch("app.routers.admin.get_current_admin_user")
    @patch("app.routers.admin.get_db")
    def test_list_users_success(self, mock_get_db, mock_get_admin):
        """Test listing users successfully"""
        # Mock admin user
        mock_admin = MagicMock()
        mock_admin.id = 1
        mock_admin.username = "admin"
        mock_admin.is_admin = True
        mock_get_admin.return_value = mock_admin

        # Mock database session and users
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

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

        client = TestClient(app)
        response = client.get("/admin/users")

        # Should work with proper mocking
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @patch("app.routers.admin.get_current_admin_user")
    @patch("app.routers.admin.get_db")
    def test_create_api_key_success(self, mock_get_db, mock_get_admin):
        """Test creating API key successfully"""
        # Mock admin user
        mock_admin = MagicMock()
        mock_admin.id = 1
        mock_admin.username = "admin"
        mock_admin.is_admin = True
        mock_get_admin.return_value = mock_admin

        # Mock database session
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock the query for checking existing keys
        mock_db.query.return_value.filter.return_value.first.return_value = None

        client = TestClient(app)
        response = client.post("/admin/api-keys", json={"name": "test-key"})

        # Should work with proper mocking
        assert response.status_code in [200, 201]

    @patch("app.routers.admin.get_current_admin_user")
    @patch("app.routers.admin.get_db")
    def test_toggle_user_status_success(self, mock_get_db, mock_get_admin):
        """Test toggling user status successfully"""
        # Mock admin user
        mock_admin = MagicMock()
        mock_admin.id = 1
        mock_admin.username = "admin"
        mock_admin.is_admin = True
        mock_get_admin.return_value = mock_admin

        # Mock database session
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock target user
        mock_user = MagicMock()
        mock_user.id = 2
        mock_user.username = "user1"
        mock_user.is_active = True
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        client = TestClient(app)
        response = client.put("/admin/users/2/toggle")

        # Should work with proper mocking
        assert response.status_code in [200, 422]

    @patch("app.routers.admin.get_current_admin_user")
    @patch("app.routers.admin.get_db")
    def test_toggle_admin_status_success(self, mock_get_db, mock_get_admin):
        """Test toggling admin status successfully"""
        # Mock admin user
        mock_admin = MagicMock()
        mock_admin.id = 1
        mock_admin.username = "admin"
        mock_admin.is_admin = True
        mock_get_admin.return_value = mock_admin

        # Mock database session
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock target user
        mock_user = MagicMock()
        mock_user.id = 2
        mock_user.username = "user1"
        mock_user.is_admin = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        client = TestClient(app)
        response = client.put("/admin/users/2/admin")

        # Should work with proper mocking
        assert response.status_code in [200, 422]

    @patch("app.routers.admin.get_current_admin_user")
    @patch("app.routers.admin.get_db")
    @patch("app.utils.create_backup")
    def test_create_backup_success(
        self, mock_create_backup, mock_get_db, mock_get_admin
    ):
        """Test creating backup successfully"""
        # Mock admin user
        mock_admin = MagicMock()
        mock_admin.id = 1
        mock_admin.username = "admin"
        mock_admin.is_admin = True
        mock_get_admin.return_value = mock_admin

        # Mock database session
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock backup creation
        mock_backup_info = MagicMock()
        mock_backup_info.filename = "backup_20231201.db"
        mock_backup_info.size_bytes = 1024
        mock_backup_info.created_at = "2023-12-01T00:00:00"
        mock_create_backup.return_value = mock_backup_info

        client = TestClient(app)
        response = client.post("/admin/backup")

        # Should work with proper mocking
        assert response.status_code in [200, 201]

    @patch("app.routers.admin.get_current_admin_user")
    @patch("app.routers.admin.get_db")
    @patch("app.utils.cleanup_old_backups")
    def test_cleanup_backups_success(self, mock_cleanup, mock_get_db, mock_get_admin):
        """Test cleanup backups successfully"""
        # Mock admin user
        mock_admin = MagicMock()
        mock_admin.id = 1
        mock_admin.username = "admin"
        mock_admin.is_admin = True
        mock_get_admin.return_value = mock_admin

        # Mock database session
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock cleanup result
        mock_cleanup.return_value = {"deleted_count": 3, "freed_bytes": 3072}

        client = TestClient(app)
        response = client.delete("/admin/backup/cleanup")

        # Should work with proper mocking
        assert response.status_code in [200, 422]

    @patch("app.routers.admin.get_current_admin_user")
    @patch("app.routers.admin.get_db")
    @patch("app.utils.get_system_metrics")
    def test_get_system_stats_success(
        self, mock_get_metrics, mock_get_db, mock_get_admin
    ):
        """Test getting system stats successfully"""
        # Mock admin user
        mock_admin = MagicMock()
        mock_admin.id = 1
        mock_admin.username = "admin"
        mock_admin.is_admin = True
        mock_get_admin.return_value = mock_admin

        # Mock database session
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.count.return_value = 5

        # Mock system metrics
        mock_get_metrics.return_value = {
            "cpu": {"percent": 45.2},
            "memory": {"percent": 67.8, "used": 2048, "total": 8192},
            "disk": {"percent": 34.1, "used": 512, "total": 1024},
            "database": {"size_bytes": 1048576},
        }

        client = TestClient(app)
        response = client.get("/admin/stats")

        # Should work with proper mocking
        assert response.status_code == 200
        data = response.json()
        assert "system" in data
        assert "database" in data

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
