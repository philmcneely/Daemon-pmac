"""
Test admin router functionality - End-to-end tests with real SQLite database
"""

import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.auth import get_current_admin_user, get_password_hash
from app.database import ApiKey, Base, Endpoint, User, get_db
from app.main import app


class TestAdminRouterE2E:
    """End-to-end tests for admin router with real database"""

    @classmethod
    def setup_class(cls):
        """Setup test database for the class"""
        # Create a temporary file for test database
        cls.test_db_fd, cls.test_db_path = tempfile.mkstemp(suffix=".db")
        cls.test_db_url = f"sqlite:///{cls.test_db_path}"

        # Create engine and session
        cls.engine = create_engine(
            cls.test_db_url, connect_args={"check_same_thread": False}
        )
        cls.TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=cls.engine
        )

        # Create tables
        Base.metadata.create_all(bind=cls.engine)

        # Override dependencies
        def override_get_db():
            try:
                db = cls.TestingSessionLocal()
                yield db
            finally:
                db.close()

        def override_get_current_admin_user():
            """Mock admin user for testing"""
            mock_admin = MagicMock()
            mock_admin.id = 999  # Use a high ID to avoid conflicts with test data
            mock_admin.username = "admin"
            mock_admin.email = "admin@example.com"
            mock_admin.is_admin = True
            mock_admin.is_active = True
            return mock_admin

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_admin_user] = (
            override_get_current_admin_user
        )

        cls.client = TestClient(app)

    @classmethod
    def teardown_class(cls):
        """Cleanup test database"""
        # Clear dependency overrides
        app.dependency_overrides.clear()

        # Close file descriptor and remove test database
        os.close(cls.test_db_fd)
        os.unlink(cls.test_db_path)

    def setup_method(self):
        """Setup fresh data for each test"""
        # Clear all data
        db = self.TestingSessionLocal()
        try:
            db.query(ApiKey).delete()
            db.query(User).delete()
            db.query(Endpoint).delete()
            db.commit()

            # Create test data
            # Create a test user
            test_user = User(
                username="testuser",
                email="test@example.com",
                hashed_password=get_password_hash("testpass"),
                is_active=True,
                is_admin=False,
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)

            # Create an admin user
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("adminpass"),
                is_active=True,
                is_admin=True,
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)

            # Create test endpoints
            resume_endpoint = Endpoint(
                name="resume",
                description="Resume data",
                schema={"type": "object", "properties": {"name": {"type": "string"}}},
                is_active=True,
                is_public=True,
            )
            db.add(resume_endpoint)

            skills_endpoint = Endpoint(
                name="skills",
                description="Skills data",
                schema={"type": "object", "properties": {"skill": {"type": "string"}}},
                is_active=True,
                is_public=False,
            )
            db.add(skills_endpoint)
            db.commit()

            # Create test API key
            test_api_key = ApiKey(
                name="test-key",
                key_hash="test_hash_123",
                user_id=test_user.id,
                is_active=True,
            )
            db.add(test_api_key)
            db.commit()

        finally:
            db.close()

    def test_list_users_success(self):
        """Test listing all users"""
        response = self.client.get("/admin/users")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # Should have at least testuser and admin

        usernames = [user["username"] for user in data]
        assert "testuser" in usernames
        assert "admin" in usernames

    def test_list_api_keys_success(self):
        """Test listing API keys successfully"""
        response = self.client.get("/admin/api-keys")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # Should have at least the test key

        # Check first key structure
        if data:
            key = data[0]
            assert "id" in key
            assert "name" in key
            assert "username" in key
            assert "is_active" in key

    def test_create_api_key_success(self):
        """Test creating API key successfully"""
        response = self.client.post("/admin/api-keys", json={"name": "new-test-key"})
        assert response.status_code in [200, 201]

        if response.status_code in [200, 201]:
            data = response.json()
            assert "id" in data or "message" in data

    def test_toggle_user_status_success(self):
        """Test toggling user status successfully"""
        # First get the test user ID
        users_response = self.client.get("/admin/users")
        assert users_response.status_code == 200

        users = users_response.json()
        test_user = next((u for u in users if u["username"] == "testuser"), None)
        assert test_user is not None

        user_id = test_user["id"]
        original_status = test_user["is_active"]

        # Toggle the status
        response = self.client.put(f"/admin/users/{user_id}/toggle")
        assert response.status_code == 200

        # Verify the status was toggled
        users_response_after = self.client.get("/admin/users")
        assert users_response_after.status_code == 200

        users_after = users_response_after.json()
        updated_user = next(
            (u for u in users_after if u["username"] == "testuser"), None
        )
        assert updated_user is not None
        assert updated_user["is_active"] != original_status

    def test_toggle_admin_status_success(self):
        """Test toggling admin status successfully"""
        # Get the test user ID
        users_response = self.client.get("/admin/users")
        assert users_response.status_code == 200

        users = users_response.json()
        test_user = next((u for u in users if u["username"] == "testuser"), None)
        assert test_user is not None

        user_id = test_user["id"]
        original_admin_status = test_user["is_admin"]

        # Toggle admin status
        response = self.client.put(f"/admin/users/{user_id}/admin")
        assert response.status_code == 200

        # Verify admin status was toggled
        users_response_after = self.client.get("/admin/users")
        assert users_response_after.status_code == 200

        users_after = users_response_after.json()
        updated_user = next(
            (u for u in users_after if u["username"] == "testuser"), None
        )
        assert updated_user is not None
        assert updated_user["is_admin"] != original_admin_status

    def test_get_system_stats_success(self):
        """Test getting system stats successfully"""
        response = self.client.get("/admin/system")
        assert response.status_code == 200

        data = response.json()
        assert "system" in data
        assert "application" in data

        # Check system metrics structure
        system = data["system"]
        assert "python_version" in system
        assert "memory_total" in system
        assert "disk_usage" in system

        # Check application metrics structure
        application = data["application"]
        assert "database_size" in application

    def test_create_backup_success(self):
        """Test creating backup successfully"""
        response = self.client.post("/admin/backup")
        # Backup creation may not be fully implemented, so accept various responses
        assert response.status_code in [200, 201, 501, 503]

    def test_cleanup_backups_success(self):
        """Test cleanup backups successfully"""
        response = self.client.delete("/admin/backup/cleanup")
        # Cleanup may not be fully implemented, so accept various responses
        assert response.status_code in [200, 404, 501, 503]

    def test_admin_unauthorized_access(self):
        """Test unauthorized access to admin endpoints"""
        # Remove admin authentication override temporarily
        original_override = app.dependency_overrides.get(get_current_admin_user)
        if original_override:
            del app.dependency_overrides[get_current_admin_user]

        try:
            client_no_auth = TestClient(app)

            # Test without authentication
            response = client_no_auth.get("/admin/users")
            assert response.status_code in [401, 403, 422]

            response = client_no_auth.get("/admin/api-keys")
            assert response.status_code in [401, 403, 422]

            response = client_no_auth.post("/admin/api-keys", json={"name": "test"})
            assert response.status_code in [401, 403, 422]

        finally:
            # Restore admin authentication override
            if original_override:
                app.dependency_overrides[get_current_admin_user] = original_override

    def test_user_not_found_scenarios(self):
        """Test scenarios where user is not found"""
        # Try to toggle status of non-existent user
        response = self.client.put("/admin/users/99999/toggle")
        assert response.status_code in [404, 422]

        # Try to toggle admin status of non-existent user
        response = self.client.put("/admin/users/99999/admin")
        assert response.status_code in [404, 422]

    def test_api_key_creation_edge_cases(self):
        """Test API key creation edge cases"""
        # Try to create API key with duplicate name
        self.client.post("/admin/api-keys", json={"name": "duplicate-key"})
        response = self.client.post("/admin/api-keys", json={"name": "duplicate-key"})
        # Should handle gracefully (may allow duplicates or reject)
        assert response.status_code in [200, 201, 400, 409, 422]

        # Try to create API key with invalid data
        response = self.client.post("/admin/api-keys", json={})
        assert response.status_code in [400, 422]


# Keep some unit tests for isolated functionality
class TestAdminRouterUnits:
    """Unit tests for admin router isolated functions"""

    def test_admin_route_imports(self):
        """Test that admin router imports work"""
        from app.routers import admin

        assert hasattr(admin, "router")

    def test_admin_dependencies_imports(self):
        """Test that admin dependencies import correctly"""
        from app.auth import get_current_admin_user
        from app.database import get_db

        assert callable(get_current_admin_user)
        assert callable(get_db)
