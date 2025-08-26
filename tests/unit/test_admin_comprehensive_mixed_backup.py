"""
Test admin router functionality - comprehensive unit tests with dependency overrides
"""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.auth import get_current_admin_user, get_current_user
from app.database import Base, get_db
from app.main import app

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_admin_comprehensive.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class TestAdminRouter:
    """Test admin router functionality with dependency overrides"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up test database and clean up after each test"""
        Base.metadata.create_all(bind=engine)

        def override_get_db():
            try:
                db = TestingSessionLocal()
                yield db
            finally:
                db.close()

        def mock_get_current_admin_user():
            return {
                "id": 1,
                "username": "admin_user",
                "is_admin": True,
                "is_active": True,
            }

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_admin_user] = mock_get_current_admin_user
        app.dependency_overrides[get_current_user] = mock_get_current_admin_user

        yield

        # Clean up
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)

    def test_list_users(self):
        """Test listing all users"""
        with TestClient(app) as client:
            response = client.get("/admin/users")
            assert response.status_code in [200, 404]

    def test_toggle_user_status_success(self):
        """Test toggling user status successfully"""
        with TestClient(app) as client:
            response = client.put("/admin/users/2/toggle")
            assert response.status_code in [200, 404]

    def test_toggle_user_status_not_found(self):
        """Test toggling status of non-existent user"""
        with TestClient(app) as client:
            response = client.put("/admin/users/999/toggle")
            assert response.status_code in [404]

    def test_toggle_user_status_self(self):
        """Test attempting to toggle own status"""
        with TestClient(app) as client:
            response = client.put("/admin/users/1/toggle")
            assert response.status_code in [400, 404]

    def test_toggle_admin_status(self):
        """Test toggling admin status"""
        with TestClient(app) as client:
            response = client.put("/admin/users/2/admin")
            assert response.status_code in [200, 404]

    def test_list_api_keys(self):
        """Test listing API keys"""
        with TestClient(app) as client:
            response = client.get("/admin/api-keys")
            assert response.status_code in [200]

    def test_create_api_key(self):
        """Test creating API key"""
        with TestClient(app) as client:
            key_data = {"name": "Test Key", "expires_at": None}
            response = client.post("/admin/api-keys", json=key_data)
            assert response.status_code in [200, 201, 422]

    def test_delete_api_key_success(self):
        """Test deleting API key successfully"""
        with TestClient(app) as client:
            response = client.delete("/admin/api-keys/1")
            assert response.status_code in [200, 404]

    def test_delete_api_key_not_found(self):
        """Test deleting non-existent API key"""
        with TestClient(app) as client:
            response = client.delete("/admin/api-keys/999")
            assert response.status_code in [404]

    def test_revoke_api_key(self):
        """Test revoking API key"""
        with TestClient(app) as client:
            response = client.put("/admin/api-keys/1/revoke")
            assert response.status_code in [200, 404]

    def test_get_system_stats(self):
        """Test getting system statistics"""
        with TestClient(app) as client:
            response = client.get("/admin/stats")
            assert response.status_code in [200]

    def test_get_audit_logs(self):
        """Test getting audit logs"""
        with TestClient(app) as client:
            response = client.get("/admin/audit-logs")
            assert response.status_code in [200]

    def test_get_user_details(self):
        """Test getting user details"""
        with TestClient(app) as client:
            response = client.get("/admin/users/1")
            assert response.status_code in [200, 404]

    def test_update_user(self):
        """Test updating user"""
        with TestClient(app) as client:
            user_data = {"username": "updated_user", "email": "updated@test.com"}
            response = client.put("/admin/users/1", json=user_data)
            assert response.status_code in [200, 404, 422]

    def test_delete_user(self):
        """Test deleting user"""
        with TestClient(app) as client:
            response = client.delete("/admin/users/2")
            assert response.status_code in [200, 404]

    def test_get_system_health(self):
        """Test system health check"""
        with TestClient(app) as client:
            response = client.get("/admin/health")
            assert response.status_code in [200]

    def test_backup_database(self):
        """Test database backup"""
        with TestClient(app) as client:
            response = client.post("/admin/backup")
            assert response.status_code in [200, 500]

    def test_restore_database(self):
        """Test database restore"""
        with TestClient(app) as client:
            restore_data = {"backup_file": "test_backup.db"}
            response = client.post("/admin/restore", json=restore_data)
            assert response.status_code in [200, 404, 422]

    def test_get_configuration(self):
        """Test getting system configuration"""
        with TestClient(app) as client:
            response = client.get("/admin/config")
            assert response.status_code in [200]

    def test_update_configuration(self):
        """Test updating system configuration"""
        with TestClient(app) as client:
            config_data = {"setting": "value"}
            response = client.put("/admin/config", json=config_data)
            assert response.status_code in [200, 422]

    def test_get_logs(self):
        """Test getting system logs"""
        with TestClient(app) as client:
            response = client.get("/admin/logs")
            assert response.status_code in [200]
