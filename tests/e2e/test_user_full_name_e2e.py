"""
E2E tests for User full_name functionality in API endpoints
"""

import pytest


def test_register_user_with_full_name(client):
    """Test user registration with full_name field"""
    response = client.post(
        "/auth/register",
        json={
            "username": "jane_fullname",
            "full_name": "Jane Chen",
            "email": "jane.fullname@test.com",
            "password": "testpassword123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "jane_fullname"
    assert data["full_name"] == "Jane Chen"
    assert data["email"] == "jane.fullname@test.com"


def test_register_user_without_full_name(client):
    """Test user registration without full_name field (optional)"""
    response = client.post(
        "/auth/register",
        json={
            "username": "john_noname",
            "email": "john.noname@test.com",
            "password": "testpassword123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "john_noname"
    assert data["full_name"] is None
    assert data["email"] == "john.noname@test.com"


def test_system_info_includes_user_full_names(client, admin_user):
    """Test that system info endpoint returns user objects with full_name"""
    # Create a user with full_name for testing
    client.post(
        "/auth/register",
        json={
            "username": "test_user_full",
            "full_name": "Test Full Name",
            "email": "test.full@test.com",
            "password": "testpassword123",
        },
    )

    response = client.get("/api/v1/system/info")
    assert response.status_code == 200
    data = response.json()

    assert "users" in data
    assert isinstance(data["users"], list)

    # Find our test user
    test_user = None
    for user in data["users"]:
        if user["username"] == "test_user_full":
            test_user = user
            break

    assert test_user is not None
    assert test_user["username"] == "test_user_full"
    assert test_user["full_name"] == "Test Full Name"
    assert test_user["email"] == "test.full@test.com"


def test_me_endpoint_includes_full_name(client):
    """Test that /auth/me endpoint returns full_name"""
    # Register user with full_name
    register_response = client.post(
        "/auth/register",
        json={
            "username": "me_test_user",
            "full_name": "Me Test User",
            "email": "me.test@test.com",
            "password": "testpassword123",
        },
    )
    assert register_response.status_code == 200

    # Login to get token
    login_response = client.post(
        "/auth/login",
        data={
            "username": "me_test_user",
            "password": "testpassword123",
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Call /me endpoint
    me_response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    data = me_response.json()

    assert data["username"] == "me_test_user"
    assert data["full_name"] == "Me Test User"
    assert data["email"] == "me.test@test.com"
