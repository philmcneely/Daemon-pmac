"""
Module: tests.unit.test_security
Description: Unit tests for security validation utilities, input sanitization,
             and threat detection mechanisms

Author: pmac
Created: 2025-08-28
Modified: 2025-08-28

Dependencies:
- pytest: 7.4.3+ - Testing framework
- app.security: Security validation module

Usage:
    pytest tests/unit/test_security.py -v

Notes:
    - Tests input sanitization and validation
    - Validates threat detection patterns
    - Covers SQL injection and XSS protection
    - Tests security exception handling
"""

import pytest

from app.security import (
    InputValidator,
    SecurityError,
    validate_endpoint_route_security,
    validate_user_route_security,
)


class TestInputValidator:
    """Test the InputValidator class"""

    def test_validate_input_security_safe_inputs(self):
        """Test that safe inputs pass validation"""
        safe_inputs = [
            "admin",
            "user123",
            "test-user",
            "endpoint_name",
            "about",
            "projects",
            "resume",
            "valid_endpoint",
        ]

        for safe_input in safe_inputs:
            # Should not raise exception
            InputValidator.validate_input_security(safe_input, "test_field")

    def test_validate_input_security_path_traversal(self):
        """Test detection of path traversal attacks"""
        dangerous_inputs = [
            "../admin",
            "user/../admin",
            "test..%2fadmin",
            "endpoint..%2F",
            "..%2F..%2Fadmin",
        ]

        for dangerous_input in dangerous_inputs:
            with pytest.raises(SecurityError) as exc_info:
                InputValidator.validate_input_security(dangerous_input, "test_field")
            assert "Dangerous pattern detected" in str(exc_info.value)

    def test_validate_input_security_endpoint_injection(self):
        """Test detection of endpoint injection attacks"""
        dangerous_inputs = [
            "/api/v1/user/admin",
            "test/user/secret",
            "endpoint/api/v1/user/",
            "/user/admin",
        ]

        for dangerous_input in dangerous_inputs:
            with pytest.raises(SecurityError) as exc_info:
                InputValidator.validate_input_security(dangerous_input, "test_field")
            assert "Dangerous pattern detected" in str(exc_info.value)

    def test_validate_input_security_privilege_escalation(self):
        """Test detection of privilege escalation attempts"""
        dangerous_inputs = [
            "admin/secret",
            "root/config",
            "system/admin",
            "useradmin/test",
        ]

        for dangerous_input in dangerous_inputs:
            with pytest.raises(SecurityError) as exc_info:
                InputValidator.validate_input_security(dangerous_input, "test_field")
            assert "Dangerous pattern detected" in str(exc_info.value)

    def test_validate_input_security_xss_attempts(self):
        """Test detection of XSS attacks"""
        dangerous_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert(1)",
            "data:text/html,<script>alert(1)</script>",
            "user<script",
        ]

        for dangerous_input in dangerous_inputs:
            with pytest.raises(SecurityError) as exc_info:
                InputValidator.validate_input_security(dangerous_input, "test_field")
            assert "Dangerous pattern detected" in str(exc_info.value)

    def test_validate_input_security_sql_injection(self):
        """Test detection of SQL injection attempts"""
        dangerous_inputs = [
            "user'; select * from users; --",
            "admin union select password from users",
            "test insert into users",
            "user update users set",
            "endpoint delete from",
        ]

        for dangerous_input in dangerous_inputs:
            with pytest.raises(SecurityError) as exc_info:
                InputValidator.validate_input_security(dangerous_input, "test_field")
            assert "Dangerous pattern detected" in str(exc_info.value)

    def test_validate_input_security_code_injection(self):
        """Test detection of code injection attempts"""
        dangerous_inputs = [
            "user; exec('rm -rf /')",
            "eval('malicious_code')",
            "system('cat /etc/passwd')",
            "__import__('os').system('ls')",
        ]

        for dangerous_input in dangerous_inputs:
            with pytest.raises(SecurityError) as exc_info:
                InputValidator.validate_input_security(dangerous_input, "test_field")
            assert "Dangerous pattern detected" in str(exc_info.value)

    def test_validate_input_security_empty_values(self):
        """Test handling of empty values"""
        # Should raise error when empty not allowed
        with pytest.raises(SecurityError) as exc_info:
            InputValidator.validate_input_security("", "test_field", allow_empty=False)
        assert "cannot be empty" in str(exc_info.value)

        # Should pass when empty allowed
        InputValidator.validate_input_security("", "test_field", allow_empty=True)

    def test_validate_input_security_case_insensitive(self):
        """Test that validation is case-insensitive"""
        dangerous_inputs = [
            "ADMIN/secret",
            "User../Admin",
            "<SCRIPT>alert(1)</SCRIPT>",
            "SELECT * FROM users",
        ]

        for dangerous_input in dangerous_inputs:
            with pytest.raises(SecurityError):
                InputValidator.validate_input_security(dangerous_input, "test_field")

    def test_validate_username_valid(self):
        """Test validation of valid usernames"""
        valid_usernames = [
            "admin",
            "user123",
            "test-user",
            "user_name",
            "a",
            "user-123_test",
        ]

        for username in valid_usernames:
            # Should not raise exception
            InputValidator.validate_username(username)

    def test_validate_username_invalid_format(self):
        """Test rejection of invalid username formats"""
        invalid_usernames = [
            "user@domain.com",  # Contains @
            "user space",  # Contains space
            "user.name",  # Contains dot
            "user/name",  # Contains slash
            "user#123",  # Contains hash
            "user$name",  # Contains dollar sign
        ]

        for username in invalid_usernames:
            with pytest.raises(SecurityError) as exc_info:
                InputValidator.validate_username(username)
            assert (
                "must contain only letters, numbers, hyphens, and underscores"
                in str(exc_info.value)
            )

    def test_validate_username_empty(self):
        """Test rejection of empty usernames"""
        with pytest.raises(SecurityError) as exc_info:
            InputValidator.validate_username("")
        assert "Username cannot be empty" in str(exc_info.value)

    def test_validate_username_too_long(self):
        """Test rejection of overly long usernames"""
        long_username = "a" * 51  # 51 characters
        with pytest.raises(SecurityError) as exc_info:
            InputValidator.validate_username(long_username)
        assert "cannot exceed 50 characters" in str(exc_info.value)

    def test_validate_username_dangerous_patterns(self):
        """Test that usernames with dangerous patterns are rejected"""
        dangerous_usernames = [
            "user../admin",
            "admin/root",
            "user<script",
        ]

        for username in dangerous_usernames:
            with pytest.raises(SecurityError) as exc_info:
                InputValidator.validate_username(username)
            assert "Dangerous pattern detected" in str(exc_info.value)

    def test_validate_endpoint_name_valid(self):
        """Test validation of valid endpoint names"""
        valid_endpoints = [
            "about",
            "projects",
            "resume",
            "endpoint-123",
            "end_point",
            "test_endpoint_name",
        ]

        for endpoint in valid_endpoints:
            # Should not raise exception
            InputValidator.validate_endpoint_name(endpoint)

    def test_validate_endpoint_name_invalid_format(self):
        """Test rejection of invalid endpoint name formats"""
        invalid_endpoints = [
            "end.point",  # Contains dot
            "end point",  # Contains space
            "end/point",  # Contains slash
            "end@point",  # Contains @
            "end#point",  # Contains hash
        ]

        for endpoint in invalid_endpoints:
            with pytest.raises(SecurityError) as exc_info:
                InputValidator.validate_endpoint_name(endpoint)
            assert (
                "must contain only letters, numbers, hyphens, and underscores"
                in str(exc_info.value)
            )

    def test_validate_endpoint_name_empty(self):
        """Test rejection of empty endpoint names"""
        with pytest.raises(SecurityError) as exc_info:
            InputValidator.validate_endpoint_name("")
        assert "Endpoint name cannot be empty" in str(exc_info.value)

    def test_validate_endpoint_name_too_long(self):
        """Test rejection of overly long endpoint names"""
        long_endpoint = "a" * 51  # 51 characters
        with pytest.raises(SecurityError) as exc_info:
            InputValidator.validate_endpoint_name(long_endpoint)
        assert "cannot exceed 50 characters" in str(exc_info.value)

    def test_validate_route_parameters_valid(self):
        """Test validation of valid route parameters"""
        # Should not raise exception
        InputValidator.validate_route_parameters("admin", "about")
        InputValidator.validate_route_parameters("user123", "projects")
        InputValidator.validate_route_parameters(username="test-user")
        InputValidator.validate_route_parameters(endpoint_name="resume")
        InputValidator.validate_route_parameters()  # No parameters

    def test_validate_route_parameters_invalid(self):
        """Test rejection of invalid route parameters"""
        # Invalid username
        with pytest.raises(SecurityError):
            InputValidator.validate_route_parameters("user../admin", "about")

        # Invalid endpoint
        with pytest.raises(SecurityError):
            InputValidator.validate_route_parameters("admin", "end../point")

        # Both invalid
        with pytest.raises(SecurityError):
            InputValidator.validate_route_parameters("user../admin", "end../point")

    def test_get_security_violations(self):
        """Test getting list of security violations"""
        # Safe input
        violations = InputValidator.get_security_violations("admin")
        assert violations == []

        # Single violation
        violations = InputValidator.get_security_violations("user../admin")
        assert "../" in violations

        # Multiple violations
        violations = InputValidator.get_security_violations("user../admin/root")
        assert "../" in violations
        assert "admin/" in violations

        # Empty input
        violations = InputValidator.get_security_violations("")
        assert violations == []

    def test_is_safe_input(self):
        """Test safe input checking"""
        # Safe inputs
        assert InputValidator.is_safe_input("admin") is True
        assert InputValidator.is_safe_input("user123") is True
        assert InputValidator.is_safe_input("test-endpoint") is True
        assert InputValidator.is_safe_input("") is True

        # Unsafe inputs
        assert InputValidator.is_safe_input("user../admin") is False
        assert InputValidator.is_safe_input("admin/root") is False
        assert InputValidator.is_safe_input("<script>alert(1)</script>") is False


class TestConvenienceFunctions:
    """Test the convenience validation functions"""

    def test_validate_user_route_security_valid(self):
        """Test valid user route parameters"""
        # Should not raise exception
        validate_user_route_security("admin", "about")
        validate_user_route_security("user123", "projects")

    def test_validate_user_route_security_invalid(self):
        """Test invalid user route parameters"""
        with pytest.raises(SecurityError):
            validate_user_route_security("user../admin", "about")

        with pytest.raises(SecurityError):
            validate_user_route_security("admin", "end../point")

    def test_validate_endpoint_route_security_valid(self):
        """Test valid endpoint route parameters"""
        # Should not raise exception
        validate_endpoint_route_security("about")
        validate_endpoint_route_security("projects")

    def test_validate_endpoint_route_security_invalid(self):
        """Test invalid endpoint route parameters"""
        with pytest.raises(SecurityError):
            validate_endpoint_route_security("end../point")

        with pytest.raises(SecurityError):
            validate_endpoint_route_security("admin/secret")


class TestSecurityPatterns:
    """Test comprehensive security pattern detection"""

    def test_all_dangerous_patterns_detected(self):
        """Test that all defined dangerous patterns are properly detected"""
        patterns_to_test = [
            "../",
            "..%2f",
            "..%2F",
            "/api/v1/user/",
            "/user/",
            "admin/",
            "root/",
            "system/",
            "<script",
            "javascript:",
            "data:",
            "select ",
            "union ",
            "insert ",
            "update ",
            "delete ",
            "exec(",
            "eval(",
            "system(",
            "__import__",
        ]

        for pattern in patterns_to_test:
            # Test pattern detection
            violations = InputValidator.get_security_violations(f"test{pattern}content")
            assert len(violations) > 0, f"Pattern '{pattern}' was not detected"

            # Test that input is marked as unsafe
            assert not InputValidator.is_safe_input(
                f"test{pattern}content"
            ), f"Pattern '{pattern}' was not marked as unsafe"

    def test_pattern_detection_edge_cases(self):
        """Test edge cases in pattern detection"""
        # Pattern at start
        assert not InputValidator.is_safe_input("../test")

        # Pattern at end
        assert not InputValidator.is_safe_input("test../")

        # Pattern in middle
        assert not InputValidator.is_safe_input("test../content")

        # Multiple patterns
        violations = InputValidator.get_security_violations("../admin/select")
        assert len(violations) >= 2

        # Case variations
        assert not InputValidator.is_safe_input("ADMIN/secret")
        assert not InputValidator.is_safe_input("Admin/Secret")

    def test_legitimate_content_with_partial_matches(self):
        """Test that legitimate content with partial pattern matches is allowed"""
        legitimate_inputs = [
            "administration",  # Contains "admin" but not "admin/"
            "administrator",  # Contains "admin" but not "admin/"
            "selection",  # Contains "select" but not "select "
            "insertion",  # Contains "insert" but not "insert "
            "systematic",  # Contains "system" but not "system/"
            "rooted",  # Contains "root" but not "root/"
            "javascript_framework",  # Contains "javascript" but not "javascript:"
        ]

        for legitimate_input in legitimate_inputs:
            assert InputValidator.is_safe_input(
                legitimate_input
            ), f"Legitimate input '{legitimate_input}' was incorrectly flagged as unsafe"

    # TESTS FROM test_security_additional.py (10 tests)
    def test_url_encoded_attack_detection(self):
        """Test detection of URL-encoded attacks"""
        # These patterns are in the DANGEROUS_PATTERNS list and should be detected
        url_encoded_attacks = [
            "..%2f",  # URL-encoded ../
            "..%2F",  # URL-encoded ../ (uppercase)
        ]

        for attack in url_encoded_attacks:
            with pytest.raises(SecurityError):
                InputValidator.validate_input_security(attack, "test_field")

    def test_specific_dangerous_patterns(self):
        """Test that all specific dangerous patterns are detected"""
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

    def test_username_validation_comprehensive(self):
        """Test comprehensive username validation"""
        # Valid usernames
        valid_usernames = [
            "admin",
            "user123",
            "test-user",
            "user_name",
            "a",
            "TEST_USER",
        ]
        for username in valid_usernames:
            InputValidator.validate_username(username)

        # Invalid usernames - dangerous patterns
        invalid_usernames = ["../admin", "admin/secret", "<script>test", "user\x00null"]
        for username in invalid_usernames:
            with pytest.raises(SecurityError):
                InputValidator.validate_username(username)

    def test_endpoint_name_validation_comprehensive(self):
        """Test comprehensive endpoint name validation"""
        # Valid endpoint names
        valid_endpoints = [
            "about",
            "projects",
            "resume",
            "test-endpoint",
            "endpoint_123",
        ]
        for endpoint in valid_endpoints:
            InputValidator.validate_endpoint_name(endpoint)

        # Invalid endpoint names - dangerous patterns
        invalid_endpoints = [
            "/api/v1/user/admin",
            "../admin",
            "<script>test",
            "end.point",
        ]
        for endpoint in invalid_endpoints:
            with pytest.raises(SecurityError):
                InputValidator.validate_endpoint_name(endpoint)

    def test_case_insensitive_validation(self):
        """Test that validation is case-insensitive"""
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

    def test_edge_cases(self):
        """Test edge cases for security validation"""
        # Test empty string handling
        with pytest.raises(SecurityError):
            InputValidator.validate_input_security("", "test_field", allow_empty=False)

        # Test very long inputs (should pass if no dangerous patterns)
        long_input = "a" * 1000
        InputValidator.validate_input_security(long_input, "test_field")

        # Test Unicode characters
        unicode_input = "用户名"  # Chinese characters
        InputValidator.validate_input_security(unicode_input, "test_field")

    def test_route_parameters_validation(self):
        """Test route parameters validation"""
        # Valid parameters
        InputValidator.validate_route_parameters("admin", "about")
        InputValidator.validate_route_parameters(username="testuser")
        InputValidator.validate_route_parameters(endpoint_name="projects")

        # Invalid parameters
        with pytest.raises(SecurityError):
            InputValidator.validate_route_parameters("../admin", "about")

        with pytest.raises(SecurityError):
            InputValidator.validate_route_parameters("user", "/api/v1/user/admin")

    def test_validation_functions_integration(self):
        """Test that validation functions are properly integrated"""
        from app.security import (
            validate_endpoint_route_security,
            validate_user_route_security,
        )

        # Test endpoint route security
        # Safe inputs should pass
        validate_endpoint_route_security("about")

        # Dangerous inputs should raise
        with pytest.raises(SecurityError):
            validate_endpoint_route_security("../admin")

        # Test user route security
        # Safe inputs should pass
        validate_user_route_security("testuser", "about")

        # Dangerous inputs should raise
        with pytest.raises(SecurityError):
            validate_user_route_security("../admin", "about")

        with pytest.raises(SecurityError):
            validate_user_route_security("user", "../admin")

    def test_multiple_dangerous_patterns(self):
        """Test inputs containing multiple dangerous patterns"""
        multi_dangerous_inputs = [
            "../admin/secret",  # Path traversal + privilege escalation
            "<script>admin/alert(1)",  # XSS + privilege escalation
            "select * from admin/users",  # SQL injection + privilege escalation
        ]

        for dangerous_input in multi_dangerous_inputs:
            with pytest.raises(SecurityError):
                InputValidator.validate_input_security(dangerous_input, "test_field")

    def test_boundary_conditions(self):
        """Test boundary conditions for validation"""
        # Test strings that are almost dangerous but not quite
        safe_but_close = [
            "admin_user",  # Contains 'admin' but not 'admin/'
            "rootless",  # Contains 'root' but not 'root/'
            "system32",  # Contains 'system' but not 'system/'
            "scriptwriter",  # Contains 'script' but not '<script'
        ]

        for safe_input in safe_but_close:
            # These should pass validation
            InputValidator.validate_input_security(safe_input, "test_field")
