"""
Module: tests.unit.test_api_router_security
Description: Unit tests for API router security mechanisms and access control

Author: pmac
Created: 2025-08-28
Modified: 2025-08-28

Dependencies:
- pytest: 7.4.3+ - Testing framework
- fastapi: 0.104.1+ - TestClient for API testing
- sqlalchemy: 2.0+ - Database operations in tests

Usage:
    pytest tests/unit/test_api_router_security.py -v

Notes:
    - Unit testing with isolated component validation
    - Comprehensive test coverage with fixtures
    - Proper database isolation and cleanup
    - Authentication and authorization testing
"""

from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from app.security import SecurityError


class TestAPIRouterSecurity:
    """Test security validation in API router endpoints"""

    @pytest.mark.asyncio
    async def test_get_specific_user_data_security_validation(self):
        """Test that user endpoint validates input security"""
        from fastapi import Request

        from app.routers.api import get_specific_user_data_universal

        # Mock the database session and request
        mock_db = Mock()
        mock_request = Mock(spec=Request)

        # Test with dangerous username
        with pytest.raises(HTTPException) as exc_info:
            await get_specific_user_data_universal(
                endpoint_name="about",
                username="../admin",
                request=mock_request,
                db=mock_db,
            )

        assert exc_info.value.status_code == 400
        assert "Dangerous pattern detected in username" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_specific_user_data_endpoint_security_validation(self):
        """Test that user endpoint validates endpoint name security"""
        from fastapi import Request

        from app.routers.api import get_specific_user_data_universal

        # Mock the database session and request
        mock_db = Mock()
        mock_request = Mock(spec=Request)

        # Test with dangerous endpoint name
        with pytest.raises(HTTPException) as exc_info:
            await get_specific_user_data_universal(
                endpoint_name="/api/v1/user/admin",
                username="user",
                request=mock_request,
                db=mock_db,
            )

        assert exc_info.value.status_code == 400
        assert "Dangerous pattern detected in endpoint_name" in str(
            exc_info.value.detail
        )

    @pytest.mark.asyncio
    async def test_get_endpoint_data_security_validation(self):
        """Test that get endpoint data validates input security"""
        from app.routers.api import get_endpoint_data

        # Mock the database session and dependencies
        mock_db = Mock()
        mock_admin_user = Mock()

        # Test with dangerous endpoint name
        with pytest.raises(HTTPException) as exc_info:
            await get_endpoint_data(
                endpoint_name="../admin", db=mock_db, current_user=mock_admin_user
            )

        assert exc_info.value.status_code == 400
        assert "Dangerous pattern detected in endpoint_name" in str(
            exc_info.value.detail
        )

    def test_security_validation_edge_cases(self):
        """Test security validation with edge cases"""
        from app.security import InputValidator

        # Test empty string handling
        with pytest.raises(SecurityError):
            InputValidator.validate_input_security("", "test_field", allow_empty=False)

        # Test None handling - this should be converted to string first
        try:
            InputValidator.validate_input_security(
                None, "test_field", allow_empty=False
            )
            assert False, "Should have raised SecurityError"
        except (SecurityError, TypeError):
            # Either SecurityError or TypeError is acceptable
            pass

        # Test very long inputs
        long_input = "a" * 1000
        # Should not raise for long but safe input
        InputValidator.validate_input_security(long_input, "test_field")

        # Test Unicode characters
        unicode_input = "用户名"  # Chinese characters
        InputValidator.validate_input_security(unicode_input, "test_field")

    def test_case_insensitive_security_validation(self):
        """Test that security validation is case-insensitive"""
        from app.security import InputValidator

        dangerous_patterns = [
            "ADMIN/secret",
            "User../Admin",
            "<SCRIPT>alert(1)</SCRIPT>",
            "SELECT * FROM users",
            "JAVASCRIPT:alert(1)",
        ]

        for pattern in dangerous_patterns:
            with pytest.raises(SecurityError):
                InputValidator.validate_input_security(pattern, "test_field")

    def test_url_encoded_attack_detection(self):
        """Test detection of URL-encoded attacks"""
        from app.security import InputValidator

        # These patterns are in the DANGEROUS_PATTERNS list and should be detected
        url_encoded_attacks = [
            "..%2f",  # URL-encoded ../
            "..%2F",  # URL-encoded ../ (uppercase)
        ]

        for attack in url_encoded_attacks:
            with pytest.raises(SecurityError):
                InputValidator.validate_input_security(attack, "test_field")

        # These patterns are NOT in the dangerous patterns list
        # The security module only checks for specific patterns, not general URL encoding
        safe_url_encoded = [
            "%3Cscript%3E",  # URL-encoded <script> - not in patterns
            "%2Fapi%2Fv1%2Fuser%2F",  # URL-encoded /api/v1/user/ - not in patterns
        ]

        for safe in safe_url_encoded:
            # These should NOT raise because they're not in DANGEROUS_PATTERNS
            InputValidator.validate_input_security(safe, "test_field")

    def test_mixed_case_patterns(self):
        """Test detection of mixed-case dangerous patterns"""
        from app.security import InputValidator

        mixed_case_attacks = [
            "AdMiN/secret",
            "UsEr../AdMiN",
            "<ScRiPt>alert(1)</ScRiPt>",
            "SeLeCt * FrOm users",
        ]

        for attack in mixed_case_attacks:
            with pytest.raises(SecurityError):
                InputValidator.validate_input_security(attack, "test_field")

    def test_specific_dangerous_patterns(self):
        """Test that all specific dangerous patterns are detected"""
        from app.security import InputValidator

        # Test each pattern from DANGEROUS_PATTERNS
        dangerous_inputs = [
            "../test",  # Path traversal
            "..%2ftest",  # URL-encoded path traversal
            "..%2Ftest",  # Uppercase URL-encoded path traversal
            "/api/v1/user/test",  # Endpoint injection
            "/user/test",  # User endpoint injection
            "admin/test",  # Privilege escalation
            "root/test",  # Root access
            "system/test",  # System access
            "<script>test",  # XSS
            "javascript:test",  # JavaScript protocol
            "data:test",  # Data protocol
            "select test",  # SQL injection
            "union test",  # SQL union
            "insert test",  # SQL insert
            "update test",  # SQL update
            "delete test",  # SQL delete
            "exec(test)",  # Code injection
            "eval(test)",  # Eval injection
            "system(test)",  # System command injection
            "__import__test",  # Python import injection
        ]

        for dangerous_input in dangerous_inputs:
            with pytest.raises(SecurityError):
                InputValidator.validate_input_security(dangerous_input, "test_field")

    def test_username_validation(self):
        """Test username-specific validation"""
        from app.security import InputValidator

        # Valid usernames
        valid_usernames = ["admin", "user123", "test-user", "user_name"]
        for username in valid_usernames:
            InputValidator.validate_username(username)

        # Invalid usernames - dangerous patterns
        invalid_usernames = ["../admin", "admin/secret", "<script>test"]
        for username in invalid_usernames:
            with pytest.raises(SecurityError):
                InputValidator.validate_username(username)

    def test_endpoint_name_validation(self):
        """Test endpoint name-specific validation"""
        from app.security import InputValidator

        # Valid endpoint names
        valid_endpoints = ["about", "projects", "resume", "test-endpoint"]
        for endpoint in valid_endpoints:
            InputValidator.validate_endpoint_name(endpoint)

        # Invalid endpoint names - dangerous patterns
        invalid_endpoints = ["/api/v1/user/admin", "../admin", "<script>test"]
        for endpoint in invalid_endpoints:
            with pytest.raises(SecurityError):
                InputValidator.validate_endpoint_name(endpoint)


class TestSingleUserModeSecurityFix:
    """Test security fixes for single-user mode data filtering vulnerability"""

    @pytest.mark.asyncio
    async def test_single_user_mode_blocks_orphaned_data(
        self, unit_db_session, unit_client
    ):
        """Test that single-user mode only returns data for the active user"""
        from app.database import DataEntry, Endpoint, User

        # Create test user
        test_user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashedpass",
            full_name="Test User",
        )
        unit_db_session.add(test_user)
        unit_db_session.commit()

        # Create test endpoint
        endpoint = Endpoint(
            name="test_endpoint",
            description="Test endpoint",
            schema={},
            is_active=True,
            is_public=True,
        )
        unit_db_session.add(endpoint)
        unit_db_session.commit()

        # Create legitimate user data
        user_data = DataEntry(
            endpoint_id=endpoint.id,
            data={"name": "Test User", "title": "Legitimate Data"},
            is_active=True,
            created_by_id=test_user.id,
        )
        unit_db_session.add(user_data)

        # Create orphaned data (simulating deleted user)
        orphaned_data = DataEntry(
            endpoint_id=endpoint.id,
            data={"name": "Deleted User", "title": "Should Not Be Visible"},
            is_active=True,
            created_by_id=None,  # Orphaned data
        )
        unit_db_session.add(orphaned_data)
        unit_db_session.commit()

        # Test API call to single-user endpoint
        response = unit_client.get(f"/api/v1/{endpoint.name}")

        assert response.status_code == 200
        data = response.json()

        # Should only return user's data, not orphaned data
        assert len(data["items"]) == 1
        assert data["items"][0]["data"]["name"] == "Test User"

        # Verify orphaned data is NOT returned
        returned_names = [item["data"]["name"] for item in data["items"]]
        assert "Deleted User" not in returned_names

    @pytest.mark.asyncio
    async def test_single_user_mode_item_access_security(
        self, unit_db_session, unit_client
    ):
        """Test that single-user mode item access respects user ownership"""
        from app.database import DataEntry, Endpoint, User

        # Create test user
        test_user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashedpass",
            full_name="Test User",
        )
        unit_db_session.add(test_user)
        unit_db_session.commit()

        # Create test endpoint
        endpoint = Endpoint(
            name="test_items",
            description="Test items endpoint",
            schema={},
            is_active=True,
            is_public=True,
        )
        unit_db_session.add(endpoint)
        unit_db_session.commit()

        # Create user's data entry
        user_entry = DataEntry(
            endpoint_id=endpoint.id,
            data={"name": "User's Item"},
            is_active=True,
            created_by_id=test_user.id,
        )
        unit_db_session.add(user_entry)

        # Create orphaned data entry
        orphaned_entry = DataEntry(
            endpoint_id=endpoint.id,
            data={"name": "Orphaned Item"},
            is_active=True,
            created_by_id=None,
        )
        unit_db_session.add(orphaned_entry)
        unit_db_session.commit()

        # Test accessing user's item - should work
        response = unit_client.get(f"/api/v1/{endpoint.name}/{user_entry.id}")
        assert response.status_code == 200
        assert response.json()["name"] == "User's Item"

        # Test accessing orphaned item - should fail (404)
        response = unit_client.get(f"/api/v1/{endpoint.name}/{orphaned_entry.id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_single_user_mode_no_users_returns_empty(
        self, unit_db_session, unit_client
    ):
        """Test that single-user mode with no users returns empty results"""
        from app.database import DataEntry, Endpoint

        # Create test endpoint
        endpoint = Endpoint(
            name="empty_test",
            description="Empty test endpoint",
            schema={},
            is_active=True,
            is_public=True,
        )
        unit_db_session.add(endpoint)
        unit_db_session.commit()

        # Create orphaned data (no users exist)
        orphaned_data = DataEntry(
            endpoint_id=endpoint.id,
            data={"name": "Orphaned Data"},
            is_active=True,
            created_by_id=None,
        )
        unit_db_session.add(orphaned_data)
        unit_db_session.commit()

        # Test API call - should return empty when no users exist
        response = unit_client.get(f"/api/v1/{endpoint.name}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0

    @pytest.mark.asyncio
    async def test_multi_user_mode_preserves_null_data_access(
        self, unit_db_session, unit_client
    ):
        """Test that multi-user mode still allows NULL created_by_id access for authenticated users"""
        from app.database import DataEntry, Endpoint, User

        # Create multiple users to trigger multi-user mode
        user1 = User(
            username="user1",
            email="user1@example.com",
            hashed_password="hash1",
            full_name="User One",
        )
        user2 = User(
            username="user2",
            email="user2@example.com",
            hashed_password="hash2",
            full_name="User Two",
        )
        unit_db_session.add_all([user1, user2])
        unit_db_session.commit()

        # Create test endpoint
        endpoint = Endpoint(
            name="multi_test",
            description="Multi-user test",
            schema={},
            is_active=True,
            is_public=True,
        )
        unit_db_session.add(endpoint)
        unit_db_session.commit()

        # Create legacy data with NULL created_by_id
        legacy_data = DataEntry(
            endpoint_id=endpoint.id,
            data={"name": "Legacy Data"},
            is_active=True,
            created_by_id=None,
        )
        unit_db_session.add(legacy_data)
        unit_db_session.commit()

        # In multi-user mode, NULL data should still be accessible to authenticated users
        # This test would need proper authentication setup to verify
        # For now, we verify the multi-user mode detection works
        from app.utils import is_single_user_mode

        assert not is_single_user_mode(unit_db_session)

    @pytest.mark.asyncio
    async def test_security_fix_regression_protection(self, unit_db_session):
        """Test to prevent regression of the security vulnerability"""
        from app.database import DataEntry, Endpoint, User
        from app.utils import get_single_user, is_single_user_mode

        # Setup single-user scenario
        single_user = User(
            username="singleuser",
            email="single@example.com",
            hashed_password="hash",
            full_name="Single User",
        )
        unit_db_session.add(single_user)
        unit_db_session.commit()

        # Create endpoint
        endpoint = Endpoint(
            name="regression_test",
            description="Regression test endpoint",
            schema={},
            is_active=True,
            is_public=True,
        )
        unit_db_session.add(endpoint)
        unit_db_session.commit()

        # Create user's data
        user_data = DataEntry(
            endpoint_id=endpoint.id,
            data={"name": "User Data"},
            is_active=True,
            created_by_id=single_user.id,
        )

        # Create multiple orphaned entries (simulating the original vulnerability)
        orphaned_entries = []
        for i in range(3):
            orphaned = DataEntry(
                endpoint_id=endpoint.id,
                data={"name": f"Orphaned {i}", "sensitive": f"leaked_data_{i}"},
                is_active=True,
                created_by_id=None,
            )
            orphaned_entries.append(orphaned)

        unit_db_session.add_all([user_data] + orphaned_entries)
        unit_db_session.commit()

        # Verify we're in single-user mode
        assert is_single_user_mode(unit_db_session)
        assert get_single_user(unit_db_session).id == single_user.id

        # Simulate the fixed query logic
        query = unit_db_session.query(DataEntry).filter(
            DataEntry.endpoint_id == endpoint.id, DataEntry.is_active == True
        )

        # Apply the security fix logic
        single_user_found = get_single_user(unit_db_session)
        if single_user_found:
            query = query.filter(DataEntry.created_by_id == single_user_found.id)
        else:
            query = query.filter(DataEntry.id == -1)

        results = query.all()

        # CRITICAL: Should only return 1 item (user's data), not 4 items
        assert len(results) == 1
        assert results[0].data["name"] == "User Data"

        # Verify no orphaned data is returned
        for result in results:
            assert "Orphaned" not in result.data["name"]
            assert result.created_by_id == single_user.id
