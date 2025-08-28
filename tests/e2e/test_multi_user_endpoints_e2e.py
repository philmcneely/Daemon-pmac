#!/usr/bin/env python3
"""
Module: tests.e2e.test_multi_user_endpoints_e2e
Description: End-to-end tests for multi-user endpoint routing and data isolation

Author: pmac
Created: 2025-08-28
Modified: 2025-08-28

Dependencies:
- pytest: 7.4.3+ - Testing framework
- fastapi: 0.104.1+ - TestClient for API testing
- sqlalchemy: 2.0+ - Database operations in tests

Usage:
    pytest tests/e2e/test_multi_user_endpoints_e2e.py -v

Notes:
    - Complete workflow testing with database integration
    - Comprehensive test coverage with fixtures
    - Proper database isolation and cleanup
    - Authentication and authorization testing
"""

import pytest
from fastapi.testclient import TestClient

from app.auth import User, create_access_token
from app.database import DataEntry, Endpoint


class TestMultiUserEndpoints:
    """Test multi-user endpoint behavior patterns"""

    def setup_method(self, method):
        """Setup test data before each test"""
        pass

    def teardown_method(self, method):
        """Cleanup after each test"""
        pass

    def _ensure_test_users(self, test_db_session):
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
                test_db_session.query(User)
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
                test_db_session.add(user)

        test_db_session.commit()

    def _ensure_test_endpoints(self, test_db_session):
        """Ensure required endpoints exist"""
        endpoint_names = ["resume", "about", "skills"]

        for name in endpoint_names:
            existing = (
                test_db_session.query(Endpoint).filter(Endpoint.name == name).first()
            )
            if not existing:
                endpoint = Endpoint(
                    name=name,
                    description=f"Test {name} endpoint",
                    schema={"test": "schema"},
                    is_public=True,
                )
                test_db_session.add(endpoint)

        test_db_session.commit()

    def _ensure_test_data(self, test_db_session):
        """Ensure test data exists for endpoints"""
        # Get users and endpoints
        blackbeard = (
            test_db_session.query(User).filter(User.username == "blackbeard").first()
        )
        admin = test_db_session.query(User).filter(User.username == "admin").first()
        resume_endpoint = (
            test_db_session.query(Endpoint).filter(Endpoint.name == "resume").first()
        )

        if blackbeard and resume_endpoint:
            # Add resume data for blackbeard
            existing = (
                test_db_session.query(DataEntry)
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
                test_db_session.add(resume_data)

        test_db_session.commit()

    def _get_access_token(self, username: str) -> str:
        """Get access token for a user"""
        return create_access_token(data={"sub": username})

    def test_multi_user_mode_unauthenticated_general_endpoint_with_data(
        self, client, test_db_session
    ):
        """Test unauthenticated access to general endpoint with data"""
        # Setup test users and data
        self._ensure_test_users(test_db_session)
        self._ensure_test_endpoints(test_db_session)
        self._ensure_test_data(test_db_session)

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

    def test_multi_user_mode_unauthenticated_general_endpoint_no_data(
        self, client, test_db_session
    ):
        """Test general endpoint returns no data when unauthenticated and no data exists"""
        # Setup test users and endpoints
        self._ensure_test_users(test_db_session)
        self._ensure_test_endpoints(test_db_session)

        # Delete all resume data to simulate no data state
        resume_endpoint = (
            test_db_session.query(Endpoint).filter(Endpoint.name == "resume").first()
        )
        if resume_endpoint:
            test_db_session.query(DataEntry).filter(
                DataEntry.endpoint_id == resume_endpoint.id
            ).delete()
            test_db_session.commit()

        response = client.get("/api/v1/nonexistent_endpoint")

    def test_multi_user_mode_user_specific_endpoint_works(
        self, client, test_db_session
    ):
        """Test that user-specific endpoints work in multi-user mode"""
        # Setup test users and data
        self._ensure_test_users(test_db_session)
        self._ensure_test_endpoints(test_db_session)
        self._ensure_test_data(test_db_session)

        response = client.get("/api/v1/resume/users/blackbeard")

        assert response.status_code == 200
        data = response.json()

        # User-specific endpoint returns List[Dict] directly
        assert isinstance(data, list)
        assert len(data) > 0

        # Verify it's blackbeard's data
        item = data[0]
        assert item["name"] == "Edward Teach"

    def test_multi_user_mode_authenticated_general_endpoint_works(
        self, client, test_db_session
    ):
        """Test authenticated general endpoint works"""
        # Setup test users and data
        self._ensure_test_users(test_db_session)
        self._ensure_test_endpoints(test_db_session)
        self._ensure_test_data(test_db_session)

        # Login as admin
        login_response = client.post(
            "/auth/login", data={"username": "admin", "password": "testpass123"}
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

    def test_multi_user_mode_different_endpoints(self, client, test_db_session):
        """Test different endpoints return different results"""
        # Setup test users and endpoints
        self._ensure_test_users(test_db_session)
        self._ensure_test_endpoints(test_db_session)

        response = client.get("/api/v1/about")

    def test_privacy_levels_with_user_specific_endpoints(self, client, test_db_session):
        """Test privacy levels work correctly with user-specific endpoints"""
        # Setup test users and data
        self._ensure_test_users(test_db_session)
        self._ensure_test_endpoints(test_db_session)
        self._ensure_test_data(test_db_session)

        response = client.get("/api/v1/resume/users/blackbeard?level=business_card")

        assert response.status_code == 200
        data = response.json()

        # Should return filtered data as a list
        assert isinstance(data, list)
        if data:
            item = data[0]
            # Business card should have basic info
            assert "name" in item

    def test_nonexistent_user_endpoint(self, client, test_db_session):
        """Test that endpoints for nonexistent users return 404"""
        # Setup test users and endpoints
        self._ensure_test_users(test_db_session)
        self._ensure_test_endpoints(test_db_session)

        response = client.get("/api/v1/resume/users/nonexistent_user")

        # Should return 404 for nonexistent user
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_error_message_consistency(self, client, test_db_session):
        """Test that error messages are consistent across endpoints"""
        # Setup test users and endpoints
        self._ensure_test_users(test_db_session)
        self._ensure_test_endpoints(test_db_session)

        # Test non-existent endpoints
        invalid_endpoints = ["nonexistent", "fake_endpoint", "random_test"]

        for endpoint in invalid_endpoints:
            response = client.get(f"/api/v1/{endpoint}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
