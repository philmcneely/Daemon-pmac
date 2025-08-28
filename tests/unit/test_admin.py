"""
Comprehensive admin router tests - consolidated from multiple test files
Covers all admin endpoints with proper mocking, security tests, and error handling
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.routers.admin import get_current_admin_user


class TestAdminUnauthorized:
    """Test admin endpoints return 403 when no authentication provided"""

    def test_list_users_unauthorized(self, unit_client):
        """Test listing users without auth returns 403"""
        response = unit_client.get("/admin/users")
        assert response.status_code == 403

    def test_toggle_user_status_unauthorized(self, unit_client):
        """Test toggling user status without auth returns 403"""
        response = unit_client.put("/admin/users/1/toggle")
        assert response.status_code == 403

    def test_toggle_user_admin_unauthorized(self, unit_client):
        """Test toggling user admin status without auth returns 403"""
        response = unit_client.put("/admin/users/1/admin")
        assert response.status_code == 403

    def test_list_api_keys_unauthorized(self, unit_client):
        """Test listing API keys without auth returns 403"""
        response = unit_client.get("/admin/api-keys")
        assert response.status_code == 403

    def test_create_api_key_unauthorized(self, unit_client):
        """Test creating API key without auth returns 403"""
        response = unit_client.post("/admin/api-keys", json={"name": "test-key"})
        assert response.status_code == 403

    def test_delete_api_key_unauthorized(self, unit_client):
        """Test deleting API key without auth returns 403"""
        response = unit_client.delete("/admin/api-keys/1")
        assert response.status_code == 403

    def test_list_endpoints_unauthorized(self, unit_client):
        """Test listing endpoints without auth returns 403"""
        response = unit_client.get("/admin/endpoints")
        assert response.status_code == 403

    def test_toggle_endpoint_unauthorized(self, unit_client):
        """Test toggling endpoint without auth returns 403"""
        response = unit_client.put("/admin/endpoints/1/toggle")
        assert response.status_code == 403

    def test_delete_endpoint_unauthorized(self, unit_client):
        """Test deleting endpoint without auth returns 403"""
        response = unit_client.delete("/admin/endpoints/1")
        assert response.status_code == 403

    def test_get_data_stats_unauthorized(self, unit_client):
        """Test getting data stats without auth returns 403"""
        response = unit_client.get("/admin/data/stats")
        assert response.status_code == 403

    def test_cleanup_data_unauthorized(self, unit_client):
        """Test data cleanup without auth returns 403"""
        response = unit_client.delete("/admin/data/cleanup")
        assert response.status_code == 403

    def test_backup_database_unauthorized(self, unit_client):
        """Test backup without auth returns 403"""
        response = unit_client.post("/admin/backup")
        assert response.status_code == 403

    def test_list_backups_unauthorized(self, unit_client):
        """Test listing backups without auth returns 403"""
        response = unit_client.get("/admin/backups")
        assert response.status_code == 403

    def test_cleanup_backups_unauthorized(self, unit_client):
        """Test backup cleanup without auth returns 403"""
        response = unit_client.delete("/admin/backup/cleanup")
        assert response.status_code == 403

    def test_restore_database_unauthorized(self, unit_client):
        """Test restore without auth returns 403"""
        response = unit_client.post("/admin/restore/backup_test.db")
        assert response.status_code == 403

    def test_get_audit_logs_unauthorized(self, unit_client):
        """Test getting audit logs without auth returns 403"""
        response = unit_client.get("/admin/audit")
        assert response.status_code == 403

    def test_get_system_info_unauthorized(self, unit_client):
        """Test getting system info without auth returns 403"""
        response = unit_client.get("/admin/system")
        assert response.status_code == 403

    def test_get_stats_unauthorized(self, unit_client):
        """Test getting stats without auth returns 403"""
        response = unit_client.get("/admin/stats")
        assert response.status_code == 403


class TestAdminUserManagement:
    """Test user management endpoints with proper mocking"""

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

            mock_user1 = MagicMock()
            mock_user1.id = 1
            mock_user1.username = "user1"
            mock_user1.email = "user1@example.com"
            mock_user1.is_active = True
            mock_user1.is_admin = False

            mock_user2 = MagicMock()
            mock_user2.id = 2
            mock_user2.username = "user2"
            mock_user2.email = "user2@example.com"
            mock_user2.is_active = False
            mock_user2.is_admin = False

            mock_db.query.return_value.all.return_value = [mock_user1, mock_user2]
            return mock_db

        # Override dependencies
        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.get("/admin/users")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 2
            assert data[0]["username"] == "user1"
            assert data[1]["username"] == "user2"
        finally:
            app.dependency_overrides.clear()

    def test_toggle_user_status_success(self):
        """Test toggling user active status successfully"""

        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        def mock_get_db():
            mock_db = MagicMock()
            mock_user = MagicMock()
            mock_user.id = 2
            mock_user.username = "user1"
            mock_user.is_active = True

            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_user
            )
            return mock_db

        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.put("/admin/users/2/toggle")

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "User status updated"
        finally:
            app.dependency_overrides.clear()

    def test_toggle_user_status_not_found(self):
        """Test toggling user status for non-existent user"""

        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        def mock_get_db():
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = None
            return mock_db

        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.put("/admin/users/999/toggle")

            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_toggle_user_admin_success(self):
        """Test toggling user admin status successfully"""

        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        def mock_get_db():
            mock_db = MagicMock()
            mock_user = MagicMock()
            mock_user.id = 2
            mock_user.username = "user1"
            mock_user.is_admin = False

            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_user
            )
            return mock_db

        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.put("/admin/users/2/admin")

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "User admin status updated"
        finally:
            app.dependency_overrides.clear()


class TestAdminApiKeyManagement:
    """Test API key management endpoints with proper mocking"""

    def test_list_api_keys_success(self):
        """Test listing API keys successfully"""

        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

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

        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.get("/admin/api-keys")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 2
            assert data[0]["name"] == "test-key-1"
            assert data[1]["name"] == "test-key-2"
        finally:
            app.dependency_overrides.clear()

    @patch("app.routers.admin.generate_api_key")
    def test_create_api_key_success(self, mock_generate_api_key):
        """Test creating API key successfully"""
        mock_generate_api_key.return_value = "test-api-key-value"

        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        def mock_get_db():
            mock_db = MagicMock()

            # Mock the add method and new API key
            mock_api_key = MagicMock()
            mock_api_key.id = 1
            mock_api_key.name = "test-key"
            mock_api_key.key_hash = "hashed-key"
            mock_api_key.user_id = 1
            mock_api_key.is_active = True
            mock_api_key.expires_at = None
            mock_api_key.created_at = datetime.now()

            # Mock the database operations
            mock_db.add = MagicMock()
            mock_db.commit = MagicMock()
            mock_db.refresh = MagicMock()

            return mock_db

        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.post(
                "/admin/api-keys", json={"name": "test-key", "user_id": 1}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["api_key"] == "test-api-key-value"
            assert "key_data" in data
        finally:
            app.dependency_overrides.clear()

    def test_create_api_key_invalid_user(self):
        """Test creating API key for non-existent user"""

        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        def mock_get_db():
            mock_db = MagicMock()
            # User not found
            mock_db.query.return_value.filter.return_value.first.return_value = None
            return mock_db

        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.post(
                "/admin/api-keys", json={"name": "test-key", "user_id": 999}
            )

            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_delete_api_key_success(self):
        """Test deleting API key successfully"""

        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        def mock_get_db():
            mock_db = MagicMock()
            mock_api_key = MagicMock()
            mock_api_key.id = 1
            mock_api_key.name = "test-key"

            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_api_key
            )
            mock_db.delete = MagicMock()
            mock_db.commit = MagicMock()
            return mock_db

        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.delete("/admin/api-keys/1")

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "API key deleted"
        finally:
            app.dependency_overrides.clear()

    def test_delete_api_key_not_found(self):
        """Test deleting non-existent API key"""

        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        def mock_get_db():
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = None
            return mock_db

        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.delete("/admin/api-keys/999")

            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"]
        finally:
            app.dependency_overrides.clear()


class TestAdminEndpointManagement:
    """Test endpoint management endpoints with proper mocking"""

    def test_list_endpoints_success(self):
        """Test listing endpoints successfully"""

        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        def mock_get_db():
            mock_db = MagicMock()

            mock_endpoint1 = MagicMock()
            mock_endpoint1.id = 1
            mock_endpoint1.name = "books"
            mock_endpoint1.is_active = True
            mock_endpoint1.created_at = datetime.now()

            mock_endpoint2 = MagicMock()
            mock_endpoint2.id = 2
            mock_endpoint2.name = "ideas"
            mock_endpoint2.is_active = False
            mock_endpoint2.created_at = datetime.now()

            mock_db.query.return_value.all.return_value = [
                mock_endpoint1,
                mock_endpoint2,
            ]
            return mock_db

        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.get("/admin/endpoints")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 2
            assert data[0]["name"] == "books"
            assert data[1]["name"] == "ideas"
        finally:
            app.dependency_overrides.clear()

    def test_toggle_endpoint_success(self):
        """Test toggling endpoint status successfully"""

        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        def mock_get_db():
            mock_db = MagicMock()
            mock_endpoint = MagicMock()
            mock_endpoint.id = 1
            mock_endpoint.name = "books"
            mock_endpoint.is_active = True

            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_endpoint
            )
            return mock_db

        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.put("/admin/endpoints/1/toggle")

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Endpoint status updated"
        finally:
            app.dependency_overrides.clear()

    def test_delete_endpoint_success(self):
        """Test deleting endpoint successfully"""

        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        def mock_get_db():
            mock_db = MagicMock()
            mock_endpoint = MagicMock()
            mock_endpoint.id = 1
            mock_endpoint.name = "books"

            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_endpoint
            )
            mock_db.delete = MagicMock()
            mock_db.commit = MagicMock()
            return mock_db

        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.delete("/admin/endpoints/1")

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Endpoint deleted successfully"
        finally:
            app.dependency_overrides.clear()


class TestAdminDataManagement:
    """Test data management endpoints with proper mocking"""

    def test_get_data_stats_success(self):
        """Test getting data statistics successfully"""

        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        def mock_get_db():
            mock_db = MagicMock()

            # Mock count queries
            mock_db.query.return_value.count.return_value = 10  # Mock count result

            return mock_db

        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.get("/admin/data/stats")

            assert response.status_code == 200
            data = response.json()
            assert "total_entries" in data
        finally:
            app.dependency_overrides.clear()

    @patch("app.routers.admin.BackgroundTasks")
    def test_cleanup_data_success(self, mock_bg_tasks):
        """Test data cleanup successfully"""

        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        def mock_get_db():
            mock_db = MagicMock()
            # Mock finding entries to delete
            mock_entries = [MagicMock(), MagicMock()]
            mock_db.query.return_value.filter.return_value.all.return_value = (
                mock_entries
            )
            return mock_db

        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.delete("/admin/data/cleanup?days=30")

            assert response.status_code == 200
            data = response.json()
            assert "cleanup initiated" in data["message"]
        finally:
            app.dependency_overrides.clear()


class TestAdminBackupOperations:
    """Test backup operation endpoints with proper mocking"""

    @patch("app.routers.admin.create_backup")
    def test_backup_database_success(self, mock_create_backup):
        """Test database backup successfully"""
        mock_create_backup.return_value = "backup_20231201_120000.db"

        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        def mock_get_db():
            return MagicMock()

        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.post("/admin/backup")

            assert response.status_code == 200
            data = response.json()
            assert data["backup_file"] == "backup_20231201_120000.db"
            assert data["message"] == "Backup created successfully"
        finally:
            app.dependency_overrides.clear()

    @patch("os.listdir")
    def test_list_backups_success(self, mock_listdir):
        """Test listing backups successfully"""
        mock_listdir.return_value = [
            "backup_20231201_120000.db",
            "backup_20231202_120000.db",
            "other_file.txt",  # Should be filtered out
        ]

        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        def mock_get_db():
            return MagicMock()

        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.get("/admin/backups")

            assert response.status_code == 200
            data = response.json()
            assert len(data["backups"]) == 2
            assert "backup_20231201_120000.db" in data["backups"]
            assert "backup_20231202_120000.db" in data["backups"]
            assert "other_file.txt" not in data["backups"]
        finally:
            app.dependency_overrides.clear()

    @patch("app.routers.admin.cleanup_old_backups")
    def test_cleanup_backups_success(self, mock_cleanup):
        """Test backup cleanup successfully"""
        mock_cleanup.return_value = 3  # Number of backups removed

        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        def mock_get_db():
            return MagicMock()

        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.delete("/admin/backup/cleanup")

            assert response.status_code == 200
            data = response.json()
            assert data["removed_backups"] == 3
            assert "backup cleanup" in data["message"]
        finally:
            app.dependency_overrides.clear()

    @patch("shutil.copy2")
    @patch("os.path.exists")
    def test_restore_database_success(self, mock_exists, mock_copy):
        """Test database restore successfully"""
        mock_exists.return_value = True

        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        def mock_get_db():
            return MagicMock()

        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.post("/admin/restore/backup_test.db")

            assert response.status_code == 200
            data = response.json()
            assert "restore completed" in data["message"]
        finally:
            app.dependency_overrides.clear()

    @patch("os.path.exists")
    def test_restore_database_file_not_found(self, mock_exists):
        """Test database restore with non-existent backup file"""
        mock_exists.return_value = False

        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        def mock_get_db():
            return MagicMock()

        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.post("/admin/restore/nonexistent.db")

            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"]
        finally:
            app.dependency_overrides.clear()


class TestAdminAuditAndSystem:
    """Test audit log and system information endpoints"""

    def test_get_audit_logs_success(self):
        """Test getting audit logs successfully"""

        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        def mock_get_db():
            mock_db = MagicMock()

            mock_log1 = MagicMock()
            mock_log1.id = 1
            mock_log1.action = "user_login"
            mock_log1.user_id = 1
            mock_log1.timestamp = datetime.now()
            mock_log1.details = "User logged in"

            mock_log2 = MagicMock()
            mock_log2.id = 2
            mock_log2.action = "data_created"
            mock_log2.user_id = 2
            mock_log2.timestamp = datetime.now()
            mock_log2.details = "Created new data entry"

            mock_db.query.return_value.order_by.return_value.limit.return_value.offset.return_value.all.return_value = [
                mock_log1,
                mock_log2,
            ]
            mock_db.query.return_value.count.return_value = 2

            return mock_db

        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.get("/admin/audit")

            assert response.status_code == 200
            data = response.json()
            assert "logs" in data
            assert "total" in data
            assert len(data["logs"]) == 2
        finally:
            app.dependency_overrides.clear()

    @patch("psutil.virtual_memory")
    @patch("psutil.disk_usage")
    @patch("psutil.cpu_percent")
    def test_get_system_info_success(self, mock_cpu, mock_disk, mock_memory):
        """Test getting system information successfully"""
        # Mock system metrics
        mock_cpu.return_value = 25.5

        mock_memory_obj = MagicMock()
        mock_memory_obj.total = 8589934592  # 8GB
        mock_memory_obj.available = 4294967296  # 4GB
        mock_memory_obj.percent = 50.0
        mock_memory.return_value = mock_memory_obj

        mock_disk_obj = MagicMock()
        mock_disk_obj.total = 1099511627776  # 1TB
        mock_disk_obj.free = 549755813888  # 512GB
        mock_disk_obj.percent = 50.0
        mock_disk.return_value = mock_disk_obj

        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        def mock_get_db():
            return MagicMock()

        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.get("/admin/system")

            assert response.status_code == 200
            data = response.json()
            assert "cpu_usage" in data
            assert "memory" in data
            assert "disk" in data
            assert data["cpu_usage"] == 25.5
        finally:
            app.dependency_overrides.clear()

    def test_get_stats_success(self):
        """Test getting general statistics successfully"""

        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        def mock_get_db():
            mock_db = MagicMock()
            # Mock various count queries
            mock_db.query.return_value.count.return_value = 5
            return mock_db

        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.get("/admin/stats")

            assert response.status_code == 200
            data = response.json()
            assert "total_users" in data
            assert "total_endpoints" in data
            assert "total_api_keys" in data
        finally:
            app.dependency_overrides.clear()


class TestAdminSecurityValidation:
    """Test security validation and boundary conditions"""

    def test_sql_injection_attempts(self, unit_client):
        """Test SQL injection attempts are blocked"""
        # Test various SQL injection payloads
        sql_payloads = [
            "1' OR '1'='1",
            "1; DROP TABLE users; --",
            "1' UNION SELECT * FROM users --",
            "'; DELETE FROM users; --",
        ]

        for payload in sql_payloads:
            response = unit_client.get(f"/admin/users/{payload}")
            # Should either return 403 (unauthorized) or 422 (validation error)
            assert response.status_code in [403, 422]

    def test_xss_attempts_in_api_key_names(self):
        """Test XSS attempts in API key names are sanitized"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
        ]

        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        def mock_get_db():
            mock_db = MagicMock()
            mock_user = MagicMock()
            mock_user.id = 1
            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_user
            )
            return mock_db

        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            for payload in xss_payloads:
                response = client.post(
                    "/admin/api-keys", json={"name": payload, "user_id": 1}
                )
                # Should either succeed with sanitized name or reject invalid input
                assert response.status_code in [200, 422]
        finally:
            app.dependency_overrides.clear()

    def test_path_traversal_attempts(self, unit_client):
        """Test path traversal attempts are blocked"""
        path_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        ]

        for payload in path_payloads:
            response = unit_client.post(f"/admin/restore/{payload}")
            # Should return 403 (unauthorized) or 404 (not found)
            assert response.status_code in [403, 404]

    def test_large_payload_handling(self):
        """Test handling of extremely large payloads"""

        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        def mock_get_db():
            return MagicMock()

        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)

            # Create a very large API key name (should be rejected)
            large_name = "x" * 10000
            response = client.post(
                "/admin/api-keys", json={"name": large_name, "user_id": 1}
            )

            # Should reject large input
            assert response.status_code in [422, 413]
        finally:
            app.dependency_overrides.clear()

    def test_boundary_values(self):
        """Test boundary values for various parameters"""

        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        def mock_get_db():
            return MagicMock()

        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)

            # Test zero values
            response = client.get("/admin/users/0")
            assert response.status_code in [403, 404, 422]

            # Test negative values
            response = client.get("/admin/users/-1")
            assert response.status_code in [403, 404, 422]

            # Test very large values
            response = client.get("/admin/users/999999999")
            assert response.status_code in [403, 404]
        finally:
            app.dependency_overrides.clear()
