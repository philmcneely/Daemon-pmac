#!/usr/bin/env python3
"""
Tests for multi-user endpoint behavior
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth import User, create_access_token
from app.database import DataEntry, Endpoint
from app.main import app

client = TestClient(app)


class TestMultiUserEndpoints:
    """Test multi-user endpoint behavior patterns"""

    def setup_method(self):
        """Setup test data before each test"""
        from app.database import SessionLocal

        self.db = SessionLocal()

        # Ensure we have multiple users for multi-user mode
        self._ensure_test_users()
        self._ensure_test_endpoints()
        self._ensure_test_data()

    def teardown_method(self):
        """Cleanup after each test"""
        self.db.close()

    def _ensure_test_users(self):
        """Ensure we have the required test users"""
        users_data = [
            {"username": "admin", "email": "admin@test.com", "is_admin": True},
            {"username": "testuser", "email": "test@test.com", "is_admin": False},
            {
                "username": "blackbeard",
                "email": "blackbeard@test.com",
                "is_admin": False,
            },
        ]

        for user_data in users_data:
            existing_user = (
                self.db.query(User)
                .filter(User.username == user_data["username"])
                .first()
            )
            if not existing_user:
                from app.auth import get_password_hash

                user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    hashed_password=get_password_hash("testpass123"),
                    is_active=True,
                    is_admin=user_data["is_admin"],
                )
                self.db.add(user)

        self.db.commit()

    def _ensure_test_endpoints(self):
        """Ensure required endpoints exist"""
        endpoint_names = ["resume", "about", "skills"]

        for name in endpoint_names:
            existing = self.db.query(Endpoint).filter(Endpoint.name == name).first()
            if not existing:
                endpoint = Endpoint(
                    name=name,
                    description=f"Test {name} endpoint",
                    schema={"test": "schema"},
                    is_public=True,
                )
                self.db.add(endpoint)

        self.db.commit()

    def _ensure_test_data(self):
        """Ensure test data exists for endpoints"""
        # Get users and endpoints
        blackbeard = self.db.query(User).filter(User.username == "blackbeard").first()
        admin = self.db.query(User).filter(User.username == "admin").first()
        resume_endpoint = (
            self.db.query(Endpoint).filter(Endpoint.name == "resume").first()
        )

        if blackbeard and resume_endpoint:
            # Add resume data for blackbeard
            existing = (
                self.db.query(DataEntry)
                .filter(
                    DataEntry.endpoint_id == resume_endpoint.id,
                    DataEntry.created_by_id == blackbeard.id,
                )
                .first()
            )
            if not existing:
                resume_data = DataEntry(
                    endpoint_id=resume_endpoint.id,
                    data={"name": "Edward Teach", "title": "Notorious Pirate Captain"},
                    created_by_id=blackbeard.id,
                    is_active=True,
                )
                self.db.add(resume_data)

        self.db.commit()

    def _get_access_token(self, username: str) -> str:
        """Get access token for a user"""
        return create_access_token(data={"sub": username})

    def test_multi_user_mode_unauthenticated_general_endpoint_with_data(self):
        """Test that general endpoints return helpful error in multi-user mode"""
        response = client.get("/api/v1/resume")

        assert response.status_code == 400
        data = response.json()

        # Verify error structure
        assert "detail" in data
        detail = data["detail"]

        assert detail["error"] == "Multi-user mode: User-specific endpoint required"
        assert "resume data" in detail["message"]
        assert detail["pattern"] == "/api/v1/resume/users/{username}"
        assert detail["example"] == "/api/v1/resume/users/your_username"
        assert "Replace 'your_username'" in detail["note"]
        assert "authenticate" in detail["note"]

    def test_multi_user_mode_unauthenticated_general_endpoint_no_data(self):
        """Test that general endpoints with no data return empty results"""
        # Test an endpoint that likely has no data
        response = client.get("/api/v1/nonexistent_endpoint")

        # Should return 404 for non-existent endpoint
        assert response.status_code == 404

    def test_multi_user_mode_user_specific_endpoint_works(self):
        """Test that user-specific endpoints work in multi-user mode"""
        response = client.get("/api/v1/resume/users/blackbeard")

        assert response.status_code == 200
        data = response.json()

        # User-specific endpoint returns List[Dict] directly
        assert isinstance(data, list)
        assert len(data) > 0

        # Verify it's blackbeard's data
        item = data[0]
        assert item["name"] == "Edward Teach"

    def test_multi_user_mode_authenticated_general_endpoint_works(self):
        """Test that authenticated users can access general endpoints"""
        # Login to get a valid token using form data
        login_response = client.post(
            "/auth/login",
            data={"username": "blackbeard", "password": "testpass123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert login_response.status_code == 200
        token_data = login_response.json()
        token = token_data["access_token"]

        # Use the token to access the general endpoint
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/resume", headers=headers)

        # Should work now that JWT authentication is properly implemented
        assert response.status_code == 200
        data = response.json()

        # Should return the user's data in PersonalItemListResponse format
        assert "items" in data
        # User should get their own data (may be empty but should not error)
        assert isinstance(data["items"], list)

    def test_multi_user_mode_different_endpoints(self):
        """Test that the error message adapts to different endpoint names"""
        # Test with different endpoint
        response = client.get("/api/v1/about")

        if response.status_code == 400:
            data = response.json()
            detail = data["detail"]

            assert "about data" in detail["message"]
            assert detail["pattern"] == "/api/v1/about/users/{username}"
            assert detail["example"] == "/api/v1/about/users/your_username"

    def test_privacy_levels_with_user_specific_endpoints(self):
        """Test that privacy levels work with user-specific endpoints"""
        response = client.get("/api/v1/resume/users/blackbeard?level=business_card")

        assert response.status_code == 200
        data = response.json()

        # Should return filtered data as a list
        assert isinstance(data, list)
        if data:
            item = data[0]
            # Business card should have basic info
            assert "name" in item

    def test_nonexistent_user_endpoint(self):
        """Test accessing user-specific endpoint for nonexistent user"""
        response = client.get("/api/v1/resume/users/nonexistent_user")

        # Should return 404 for nonexistent user
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_error_message_consistency(self):
        """Test that error messages are consistent across different endpoints"""
        endpoints_to_test = ["resume", "about", "skills"]

        for endpoint in endpoints_to_test:
            response = client.get(f"/api/v1/{endpoint}")

            if response.status_code == 400:  # Has data, shows error
                data = response.json()
                detail = data["detail"]

                # Verify consistent structure
                required_keys = ["error", "message", "pattern", "example", "note"]
                for key in required_keys:
                    assert key in detail, f"Missing {key} in {endpoint} error"

                # Verify endpoint-specific content
                assert endpoint in detail["pattern"]
                assert endpoint in detail["example"]
        if response.status_code == 200:  # No data, returns empty
            data = response.json()
            assert data["items"] == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
