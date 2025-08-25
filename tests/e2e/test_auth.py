"""
Test authentication endpoints
"""

import pytest


def test_login_success(client, admin_user):
    """Test successful login"""
    response = client.post(
        "/auth/login", data={"username": "admin", "password": "testpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data


def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = client.post(
        "/auth/login", data={"username": "invalid", "password": "invalid"}
    )
    assert response.status_code == 401
    assert "detail" in response.json()


def test_login_missing_fields(client):
    """Test login with missing fields"""
    response = client.post(
        "/auth/login",
        data={
            "username": "admin"
            # Missing password
        },
    )
    assert response.status_code == 422


def test_register_success(client):
    """Test successful user registration (first user becomes admin)"""
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
    assert data["username"] == "firstuser"
    assert data["email"] == "first@test.com"
    assert data["is_admin"]  # First user should be admin


def test_register_duplicate_username(client, admin_user):
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


def test_register_duplicate_email(client, admin_user):
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


def test_register_invalid_email(client):
    """Test registration with invalid email format"""
    response = client.post(
        "/auth/register",
        json={
            "username": "newuser",
            "email": "invalid-email",
            "password": "testpassword123",
        },
    )
    assert response.status_code == 422


def test_register_weak_password(client):
    """Test registration with weak password"""
    response = client.post(
        "/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "123",  # Too short
        },
    )
    assert response.status_code == 422


def test_me_endpoint_authenticated(client, auth_headers):
    """Test /auth/me endpoint with valid token"""
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"
    assert data["is_admin"]


def test_me_endpoint_unauthenticated(client):
    """Test /auth/me endpoint without token"""
    response = client.get("/auth/me")
    # Both unauthorized responses are valid
    assert response.status_code in [401, 403]


def test_me_endpoint_invalid_token(client):
    """Test /auth/me endpoint with invalid token"""
    response = client.get("/auth/me", headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == 401


def test_protected_endpoint_access(client, auth_headers):
    """Test accessing protected endpoint with valid token"""
    response = client.post(
        "/api/v1/ideas",
        json={"title": "Protected Idea", "description": "Created with authentication"},
        headers=auth_headers,
    )
    assert response.status_code == 200


def test_admin_only_endpoint(client, auth_headers, regular_user_headers):
    """Test admin-only endpoint access"""
    # Create a regular user first
    client.post(
        "/auth/register",
        json={
            "username": "regularuser",
            "email": "regular@test.com",
            "password": "testpassword123",
        },
    )

    # Admin should have access
    admin_response = client.get("/admin/users", headers=auth_headers)
    assert admin_response.status_code == 200

    # Regular user should be denied
    user_response = client.get("/admin/users", headers=regular_user_headers)
    assert user_response.status_code == 403


def test_token_expiration_handling(client, admin_user):
    """Test handling of expired tokens (simulate)"""
    # This would require mocking time or using a very short expiration
    # For now, just test that tokens have expiration info
    response = client.post(
        "/auth/login", data={"username": "admin", "password": "testpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "expires_in" in data
    assert data["expires_in"] > 0


def test_login_updates_last_login(client, admin_user, test_db_session):
    """Test that login updates the last_login timestamp"""
    original_last_login = admin_user.last_login

    response = client.post(
        "/auth/login", data={"username": "admin", "password": "testpassword"}
    )
    assert response.status_code == 200

    # Refresh user from database
    test_db_session.refresh(admin_user)
    assert admin_user.last_login != original_last_login
