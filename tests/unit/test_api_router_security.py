# pyright: reportMissingImports=false
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

# Import SecurityError (ignore if the module cannot be resolved)
from app.security import SecurityError  # type: ignore

# The fixtures `unit_db_session` and `unit_client` are provided by the test suite.
# Type: ignore comments silence MyPy/Pylance warnings about undefined names.


class TestAPIRouterSecurity:
    """Test security validation in API router endpoints"""

    @pytest.mark.asyncio
    async def test_get_specific_user_data_security_validation(self):
        """Validate that dangerous usernames are rejected."""
        from fastapi import Request

        # Import the endpoint under test (ignore if not resolvable)
        from app.routers.api import get_specific_user_data_universal  # type: ignore

        mock_db = Mock()
        mock_request = Mock(spec=Request)

        # Dangerous username should raise HTTPException
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
        """Validate that dangerous endpoint names are rejected."""
        from fastapi import Request

        from app.routers.api import get_specific_user_data_universal  # type: ignore

        mock_db = Mock()
        mock_request = Mock(spec=Request)

        # Dangerous endpoint name should raise HTTPException
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
        """Validate that dangerous endpoint names are rejected for generic endpoint data."""
        from app.routers.api import get_endpoint_data  # type: ignore

        mock_db = Mock()
        mock_admin_user = Mock()

        # Dangerous endpoint name should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await get_endpoint_data(
                endpoint_name="../admin", db=mock_db, current_user=mock_admin_user
            )
        assert exc_info.value.status_code == 400
        assert "Dangerous pattern detected in endpoint_name" in str(
            exc_info.value.detail
        )

    def test_security_validation_edge_cases(self):
        """Test edge‑case inputs for the security validator."""
        from app.security import InputValidator

        # Empty string should raise SecurityError
        with pytest.raises(SecurityError):
            InputValidator.validate_input_security("", "test_field", allow_empty=False)

        # None input – type ignored for the test
        try:
            InputValidator.validate_input_security(
                None, "test_field", allow_empty=False
            )  # type: ignore
            assert False, "Expected SecurityError"
        except (SecurityError, TypeError):
            pass

        # Long safe input should not raise
        InputValidator.validate_input_security("a" * 1000, "test_field")

        # Unicode input should be handled correctly
        InputValidator.validate_input_security("用户名", "test_field")

    def test_case_insensitive_security_validation(self):
        """Ensure validation is case‑insensitive."""
        from app.security import InputValidator

        patterns = [
            "ADMIN/secret",
            "User../Admin",
            "<SCRIPT>alert(1)</SCRIPT>",
            "SELECT * FROM users",
            "JAVASCRIPT:alert(1)",
        ]
        for pat in patterns:
            with pytest.raises(SecurityError):
                InputValidator.validate_input_security(pat, "test_field")

    def test_url_encoded_attack_detection(self):
        """Detect URL‑encoded attack patterns."""
        from app.security import InputValidator

        attacks = ["..%2f", "..%2F"]
        for atk in attacks:
            with pytest.raises(SecurityError):
                InputValidator.validate_input_security(atk, "test_field")

        # Safe URL‑encoded strings should not raise
        safe = ["%3Cscript%3E", "%2Fapi%2Fv1%2Fuser%2F"]
        for s in safe:
            InputValidator.validate_input_security(s, "test_field")

    def test_mixed_case_patterns(self):
        """Detect mixed‑case dangerous patterns."""
        from app.security import InputValidator

        attacks = [
            "AdMiN/secret",
            "UsEr../AdMiN",
            "<ScRiPt>alert(1)</ScRiPt>",
            "SeLeCt * FrOm users",
        ]
        for atk in attacks:
            with pytest.raises(SecurityError):
                InputValidator.validate_input_security(atk, "test_field")

    def test_specific_dangerous_patterns(self):
        """Validate detection of all known dangerous patterns."""
        from app.security import InputValidator

        dangerous = [
            "../test",
            "..%2ftest",
            "..%2Ftest",
            "/api/v1/user/test",
            "/user/test",
            "admin/test",
            "root/test",
            "system/test",
            "<script>test",
            "javascript:test",
            "data:test",
            "select test",
            "union test",
            "insert test",
            "update test",
            "delete test",
            "exec(test)",
            "eval(test)",
            "system(test)",
            "__import__test",
        ]
        for d in dangerous:
            with pytest.raises(SecurityError):
                InputValidator.validate_input_security(d, "test_field")

    def test_username_validation(self):
        """Validate username‑specific checks."""
        from app.security import InputValidator

        valid = ["admin", "user123", "test-user", "user_name"]
        for u in valid:
            InputValidator.validate_username(u)

        invalid = ["../admin", "admin/secret", "<script>test"]
        for u in invalid:
            with pytest.raises(SecurityError):
                InputValidator.validate_username(u)

    def test_endpoint_name_validation(self):
        """Validate endpoint name‑specific checks."""
        from app.security import InputValidator

        valid = ["about", "projects", "resume", "test-endpoint"]
        for e in valid:
            InputValidator.validate_endpoint_name(e)

        invalid = ["/api/v1/user/admin", "../admin", "<script>test"]
        for e in invalid:
            with pytest.raises(SecurityError):
                InputValidator.validate_endpoint_name(e)
