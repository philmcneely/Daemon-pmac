"""
Module: tests.unit.test_auth_router
Description: Unit tests for authentication router endpoints

Author: pmac
Created: 2025-10-19
Modified: 2025-10-19

Dependencies:
- pytest: 7.4.3+ - Testing framework
- fastapi: 0.104.1+ - TestClient for API testing
- sqlalchemy: 2.0+ - Database operations in tests

Usage:
    pytest tests/unit/test_auth_router.py -v

Notes:
    - Unit testing with isolated component validation
    - Comprehensive test coverage for auth router endpoints
    - Proper database isolation and cleanup
    - Authentication and authorization testing
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.database import User, UserPrivacySettings
from app.main import app
from app.schemas import UserCreate


class TestAuthRouterEndpoints:
    """Test authentication router endpoints"""

    def test_login_success(self, client, admin_user):
        """Test successful login"""
        response = client.post(
            "/auth/login", data={"username": "admin", "password": "testpassword"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post(
            "/auth/login", data={"username": "invalid", "password": "invalid"}
        )
        assert response.status_code == 401
        assert "detail" in response.json()

    def test_login_inactive_user(self, client, test_db_session):
        """Test login with inactive user"""
        from app.auth import get_password_hash

        # Create an inactive user with proper password hash
        hashed_password = get_password_hash("testpassword")
        inactive_user = User(
            username="inactive",
            email="inactive@test.com",
            hashed_password=hashed_password,
            is_active=False,
            is_admin=False,
        )
        test_db_session.add(inactive_user)
        test_db_session.commit()

        response = client.post(
            "/auth/login", data={"username": "inactive", "password": "testpassword"}
        )
        assert response.status_code == 401
        assert "disabled" in response.json()["detail"]

    def test_register_success(self, client):
        """Test successful user registration"""
        response = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@test.com",
                "password": "testpassword123",
                "full_name": "New User",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@test.com"
        assert data["is_active"] is True

    def test_register_duplicate_username(self, client, admin_user):
        """Test registration with duplicate username"""
        response = client.post(
            "/auth/register",
            json={
                "username": "admin",  # Already exists
                "email": "different@test.com",
                "password": "testpassword123",
            },
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_duplicate_email(self, client, admin_user):
        """Test registration with duplicate email"""
        response = client.post(
            "/auth/register",
            json={
                "username": "different",
                "email": "admin@test.com",  # Already exists
                "password": "testpassword123",
            },
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_first_user_admin(self, client, test_db_session):
        """Test that first user becomes admin"""
        # Clear database first
        test_db_session.query(User).delete()
        test_db_session.commit()

        response = client.post(
            "/auth/register",
            json={
                "username": "firstuser",
                "email": "first@test.com",
                "password": "testpassword123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_admin"] is True

    def test_get_current_user_info(self, client, auth_headers):
        """Test /auth/me endpoint"""
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin"
        assert data["is_admin"] is True

    def test_get_current_user_info_unauthenticated(self, client):
        """Test /auth/me endpoint without authentication"""
        response = client.get("/auth/me")
        assert response.status_code in [401, 403]

    def test_create_user_admin_success(self, client, auth_headers):
        """Test admin creating a new user"""
        response = client.post(
            "/auth/users",
            json={
                "username": "newadminuser",
                "email": "newadmin@test.com",
                "password": "testpassword123",
                "is_admin": True,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newadminuser"
        assert data["is_admin"] is True

    def test_create_user_admin_unauthorized(self, client, regular_user_headers):
        """Test non-admin trying to create user"""
        response = client.post(
            "/auth/users",
            json={
                "username": "newuser",
                "email": "new@test.com",
                "password": "testpassword123",
            },
            headers=regular_user_headers,
        )
        assert response.status_code == 403

    def test_create_user_admin_duplicate(self, client, auth_headers, admin_user):
        """Test admin creating user with duplicate username"""
        response = client.post(
            "/auth/users",
            json={
                "username": "admin",  # Already exists
                "email": "different@test.com",
                "password": "testpassword123",
            },
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_list_users_admin(self, client, auth_headers, admin_user):
        """Test admin listing all users"""
        response = client.get("/auth/users", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["username"] == "admin"

    def test_list_users_unauthorized(self, client, regular_user_headers):
        """Test non-admin trying to list users"""
        response = client.get("/auth/users", headers=regular_user_headers)
        assert response.status_code == 403

    def test_get_user_by_username_admin(self, client, auth_headers, admin_user):
        """Test admin getting user by username"""
        response = client.get("/auth/users/admin", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin"

    def test_get_user_by_username_not_found(self, client, auth_headers):
        """Test admin getting non-existent user"""
        response = client.get("/auth/users/nonexistent", headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_user_by_username_unauthorized(self, client, regular_user_headers):
        """Test non-admin trying to get user by username"""
        response = client.get("/auth/users/admin", headers=regular_user_headers)
        assert response.status_code == 403

    def test_change_password_success(self, client, auth_headers, admin_user):
        """Test successful password change"""
        response = client.post(
            "/auth/change-password",
            params={
                "old_password": "testpassword",
                "new_password": "newpassword123",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert "updated successfully" in response.json()["message"]

    def test_change_password_wrong_old_password(self, client, auth_headers):
        """Test password change with wrong old password"""
        response = client.post(
            "/auth/change-password",
            params={
                "old_password": "wrongpassword",
                "new_password": "newpassword123",
            },
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "Incorrect old password" in response.json()["detail"]

    def test_change_password_weak_new_password(self, client, auth_headers):
        """Test password change with weak new password"""
        response = client.post(
            "/auth/change-password",
            params={
                "old_password": "testpassword",
                "new_password": "123",  # Too short
            },
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "at least 8 characters" in response.json()["detail"]

    def test_change_password_unauthorized(self, client, regular_user_headers):
        """Test non-admin trying to change password"""
        response = client.post(
            "/auth/change-password",
            params={
                "old_password": "testpassword",
                "new_password": "newpassword123",
            },
            headers=regular_user_headers,
        )
        assert response.status_code == 403

    def test_login_updates_last_login(self, client, admin_user, test_db_session):
        """Test that login updates last_login timestamp"""
        original_last_login = admin_user.last_login

        response = client.post(
            "/auth/login", data={"username": "admin", "password": "testpassword"}
        )
        assert response.status_code == 200

        # Refresh user from database
        test_db_session.refresh(admin_user)
        assert admin_user.last_login != original_last_login

    def test_register_creates_privacy_settings(self, client, test_db_session):
        """Test that registration creates default privacy settings"""
        response = client.post(
            "/auth/register",
            json={
                "username": "privacyuser",
                "email": "privacy@test.com",
                "password": "testpassword123",
            },
        )
        assert response.status_code == 200

        # Check that privacy settings were created
        user = (
            test_db_session.query(User).filter(User.username == "privacyuser").first()
        )
        privacy_settings = (
            test_db_session.query(UserPrivacySettings)
            .filter(UserPrivacySettings.user_id == user.id)
            .first()
        )
        assert privacy_settings is not None
        assert privacy_settings.show_contact_info is True
        assert privacy_settings.business_card_mode is False

    def test_create_user_admin_creates_privacy_settings(
        self, client, auth_headers, test_db_session
    ):
        """Test that admin user creation creates privacy settings"""
        response = client.post(
            "/auth/users",
            json={
                "username": "admincreated",
                "email": "admincreated@test.com",
                "password": "testpassword123",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Check that privacy settings were created
        user = (
            test_db_session.query(User).filter(User.username == "admincreated").first()
        )
        privacy_settings = (
            test_db_session.query(UserPrivacySettings)
            .filter(UserPrivacySettings.user_id == user.id)
            .first()
        )
        assert privacy_settings is not None

    def test_register_with_full_name(self, client):
        """Test registration with full name provided"""
        response = client.post(
            "/auth/register",
            json={
                "username": "fullnameuser",
                "email": "fullname@test.com",
                "password": "testpassword123",
                "full_name": "Full Name User",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Full Name User"

    def test_create_user_admin_with_full_name(self, client, auth_headers):
        """Test admin creating user with full name"""
        response = client.post(
            "/auth/users",
            json={
                "username": "adminfullname",
                "email": "adminfullname@test.com",
                "password": "testpassword123",
                "full_name": "Admin Full Name",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Admin Full Name"

    def test_token_expiration_info(self, client, admin_user):
        """Test that login returns token expiration info"""
        response = client.post(
            "/auth/login", data={"username": "admin", "password": "testpassword"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "expires_in" in data
        assert isinstance(data["expires_in"], int)
        assert data["expires_in"] > 0

    def test_login_missing_password(self, client):
        """Test login with missing password"""
        response = client.post(
            "/auth/login", data={"username": "admin"}  # Missing password
        )
        assert response.status_code == 422

    def test_login_missing_username(self, client):
        """Test login with missing username"""
        response = client.post(
            "/auth/login", data={"password": "testpassword"}  # Missing username
        )
        assert response.status_code == 422

    def test_register_missing_required_fields(self, client):
        """Test registration with missing required fields"""
        response = client.post(
            "/auth/register",
            json={
                "username": "missingfields",
                # Missing email and password
            },
        )
        assert response.status_code == 422

    def test_change_password_missing_fields(self, client, auth_headers):
        """Test password change with missing fields"""
        response = client.post(
            "/auth/change-password",
            params={
                "old_password": "testpassword",
                # Missing new_password
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_create_user_admin_missing_fields(self, client, auth_headers):
        """Test admin user creation with missing fields"""
        response = client.post(
            "/auth/users",
            json={
                "username": "missingfields",
                # Missing email and password
            },
            headers=auth_headers,
        )
        assert response.status_code == 422
