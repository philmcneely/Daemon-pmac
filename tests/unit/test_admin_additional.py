"""
# mypy: ignore-errors
Module: tests.unit.test_admin_additional
Description: Additional unit tests for admin router to improve coverage
             covering error handling, edge cases, and missing functionality

Author: pmac
Created: 2025-10-19
Modified: 2025-10-19

Dependencies:
- pytest: 7.4.3+ - Testing framework
- fastapi: 0.104.1+ - TestClient for API testing
- sqlalchemy: 2.0+ - Database operations in tests

Usage:
    pytest tests/unit/test_admin_additional.py -v

Notes:
    - Tests error handling and edge cases in admin router
    - Covers missing lines from coverage report
    - Focuses on backup, restore, and system operations
"""

import os
import shutil
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.auth import get_current_admin_user  # type: ignore
from app.database import get_db  # type: ignore
from app.main import app  # type: ignore


class TestAdminErrorHandling:
    """Test admin router error handling and edge cases"""

    def test_toggle_user_status_self_deactivation(self):
        """Test that admin cannot deactivate themselves"""

        # Mock admin user
        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        # Mock database with user that matches admin ID
        def mock_get_db():
            mock_db = MagicMock()
            mock_user = MagicMock()
            mock_user.id = 1  # Same as admin ID
            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_user
            )
            return mock_db

        # Override dependencies
        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.put("/admin/users/1/toggle")
            # Should return 400 when trying to deactivate self
            assert response.status_code == 400
            assert "Cannot deactivate yourself" in response.json()["detail"]
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()

    def test_cleanup_deleted_data_empty(self):
        """Test data cleanup when no deleted entries exist"""

        # Mock admin user
        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        # Mock database - no deleted entries
        def mock_get_db():
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.count.return_value = 0
            mock_db.query.return_value.filter.return_value.delete.return_value = 0
            return mock_db

        # Override dependencies
        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.delete("/admin/data/cleanup")
            assert response.status_code == 200
            assert (
                "Permanently deleted 0 soft-deleted entries"
                in response.json()["message"]
            )
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()

    def test_create_backup_failure(self):
        """Test backup creation failure"""

        # Mock admin user
        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        # Override dependencies
        app.dependency_overrides[get_current_admin_user] = mock_get_admin

        try:
            client = TestClient(app)
            # Mock backup function to raise exception
            with patch(
                "app.routers.admin.create_backup",
                side_effect=Exception("Backup failed: Disk full"),
            ):
                response = client.post("/admin/backup")
                assert response.status_code == 500
                assert "Backup failed" in response.json()["detail"]
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()

    def test_backup_cleanup_failure(self):
        """Test backup cleanup failure"""

        # Mock admin user
        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        # Override dependencies
        app.dependency_overrides[get_current_admin_user] = mock_get_admin

        try:
            client = TestClient(app)
            # Mock cleanup function to raise exception
            with patch(
                "app.routers.admin.cleanup_old_backups",
                side_effect=Exception("Cleanup failed: Permission denied"),
            ):
                response = client.delete("/admin/backup/cleanup")
                assert response.status_code == 500
                assert "Backup cleanup failed" in response.json()["detail"]
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()

    def test_restore_backup_failure(self):
        """Test backup restore failure"""

        # Mock admin user
        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        # Override dependencies
        app.dependency_overrides[get_current_admin_user] = mock_get_admin

        try:
            client = TestClient(app)
            # Mock file exists but copy fails
            with patch("app.routers.admin.os.path.exists", return_value=True):
                with patch(
                    "app.routers.admin.shutil.copy2",
                    side_effect=Exception("Restore failed: Permission denied"),
                ):
                    response = client.post("/admin/restore/test.db")
                    assert response.status_code == 500
                    assert "Restore failed" in response.json()["detail"]
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()

    def test_audit_log_filtering(self):
        """Test audit log filtering by action and table name"""

        # Mock admin user
        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        # Mock database with audit log entries
        def mock_get_db():
            mock_db = MagicMock()
            mock_audit_log = MagicMock()
            mock_audit_log.id = 1
            mock_audit_log.action = "CREATE"
            mock_audit_log.table_name = "users"
            mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
                mock_audit_log
            ]
            mock_db.query.return_value.filter.return_value.count.return_value = 1
            return mock_db

        # Override dependencies
        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            # Test with action filter
            response = client.get("/admin/audit?action=create")
            assert response.status_code == 200
            assert "entries" in response.json()

            # Test with table name filter
            response = client.get("/admin/audit?table_name=users")
            assert response.status_code == 200
            assert "entries" in response.json()
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()

    def test_list_backups_empty_directory(self):
        """Test listing backups when directory is empty"""

        # Mock admin user
        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        # Override dependencies
        app.dependency_overrides[get_current_admin_user] = mock_get_admin

        try:
            client = TestClient(app)
            # Mock directory exists but is empty
            with patch("app.routers.admin.os.path.exists", return_value=True):
                with patch("app.routers.admin.os.listdir", return_value=[]):
                    response = client.get("/admin/backups")
                    assert response.status_code == 200
                    assert response.json()["backups"] == []
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()

    def test_list_backups_nonexistent_directory(self):
        """Test listing backups when directory doesn't exist"""

        # Mock admin user
        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        # Override dependencies
        app.dependency_overrides[get_current_admin_user] = mock_get_admin

        try:
            client = TestClient(app)
            # Mock directory doesn't exist
            with patch("app.routers.admin.os.path.exists", return_value=False):
                response = client.get("/admin/backups")
                assert response.status_code == 200
                assert response.json()["backups"] == []
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()

    def test_system_info_database_not_found(self):
        """Test system info when database file doesn't exist"""

        # Mock admin user
        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        # Override dependencies
        app.dependency_overrides[get_current_admin_user] = mock_get_admin

        try:
            client = TestClient(app)
            # Mock database file doesn't exist
            with patch("app.routers.admin.os.path.exists", return_value=False):
                response = client.get("/admin/system")
                assert response.status_code == 200
                assert response.json()["application"]["database_size"] == 0
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()

    def test_get_stats_empty_database(self):
        """Test stats with empty database"""

        # Mock admin user
        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        # Mock database with empty data
        def mock_get_db():
            mock_db = MagicMock()
            mock_db.query.return_value.all.return_value = []  # Empty endpoints
            mock_db.query.return_value.count.return_value = 0  # Empty counts
            return mock_db

        # Override dependencies
        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            # Mock database file doesn't exist
            with patch("app.routers.admin.os.path.exists", return_value=False):
                response = client.get("/admin/stats")
                assert response.status_code == 200
                assert response.json()["database"]["total_users"] == 0
                assert response.json()["database"]["total_endpoints"] == 0
                assert response.json()["database"]["total_entries"] == 0
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()

    def test_list_api_keys_with_inactive_user(self):
        """Test listing API keys when user is inactive"""

        # Mock admin user
        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        # Mock database with API key from inactive user
        def mock_get_db():
            mock_db = MagicMock()
            mock_api_key = MagicMock()
            mock_api_key.id = 1
            mock_api_key.name = "test-key"
            mock_api_key.user = None  # Simulate inactive user
            mock_db.query.return_value.all.return_value = [mock_api_key]
            return mock_db

        # Override dependencies
        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.get("/admin/api-keys")
            assert response.status_code == 200
            assert response.json()[0]["username"] == "Unknown"
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()

    def test_cleanup_deleted_data_with_entries(self):
        """Test data cleanup with actual deleted entries"""

        # Mock admin user
        def mock_get_admin():
            mock_admin = MagicMock()
            mock_admin.id = 1
            mock_admin.username = "admin"
            mock_admin.is_admin = True
            return mock_admin

        # Mock database with deleted entries
        def mock_get_db():
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.count.return_value = (
                5  # 5 deleted entries
            )
            mock_db.query.return_value.filter.return_value.delete.return_value = 5
            return mock_db

        # Override dependencies
        app.dependency_overrides[get_current_admin_user] = mock_get_admin
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.delete("/admin/data/cleanup")
            assert response.status_code == 200
            assert (
                "Permanently deleted 5 soft-deleted entries"
                in response.json()["message"]
            )
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()
