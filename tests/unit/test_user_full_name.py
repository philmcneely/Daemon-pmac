"""
Unit tests for User model full_name functionality
"""

import pytest
from sqlalchemy.orm import Session

from app.auth import get_password_hash
from app.database import User, get_db
from app.schemas import UserCreate, UserResponse


def test_user_model_with_full_name():
    """Test that User model accepts and stores full_name"""
    # Create user with full_name
    user = User(
        username="test_user",
        full_name="Test User",
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_admin=False,
    )

    assert user.username == "test_user"
    assert user.full_name == "Test User"
    assert user.email == "test@example.com"


def test_user_model_without_full_name():
    """Test that User model works without full_name (None value)"""
    # Create user without full_name
    user = User(
        username="test_user2",
        email="test2@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_admin=False,
    )

    assert user.username == "test_user2"
    assert user.full_name is None
    assert user.email == "test2@example.com"


def test_user_create_schema_with_full_name():
    """Test that UserCreate schema accepts full_name"""
    user_data = UserCreate(
        username="schema_test",
        full_name="Schema Test User",
        email="schema@example.com",
        password="password123",
        is_admin=False,
    )

    assert user_data.username == "schema_test"
    assert user_data.full_name == "Schema Test User"
    assert user_data.email == "schema@example.com"


def test_user_create_schema_without_full_name():
    """Test that UserCreate schema works without full_name (optional)"""
    user_data = UserCreate(
        username="schema_test2",
        email="schema2@example.com",
        password="password123",
        is_admin=False,
    )

    assert user_data.username == "schema_test2"
    assert user_data.full_name is None
    assert user_data.email == "schema2@example.com"


def test_user_response_schema_includes_full_name():
    """Test that UserResponse schema includes full_name field"""
    from datetime import datetime

    user_response = UserResponse(
        id=1,
        username="response_test",
        full_name="Response Test User",
        email="response@example.com",
        is_active=True,
        is_admin=False,
        created_at=datetime.now(),
    )

    assert user_response.username == "response_test"
    assert user_response.full_name == "Response Test User"
    assert user_response.email == "response@example.com"


def test_user_response_schema_without_full_name():
    """Test that UserResponse schema works with None full_name"""
    from datetime import datetime

    user_response = UserResponse(
        id=2,
        username="response_test2",
        full_name=None,
        email="response2@example.com",
        is_active=True,
        is_admin=False,
        created_at=datetime.now(),
    )

    assert user_response.username == "response_test2"
    assert user_response.full_name is None
    assert user_response.email == "response2@example.com"
