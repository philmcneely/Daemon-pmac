"""
Additional unit tests for security validation features
"""

import pytest

from app.security import InputValidator, SecurityError


class TestSecurityValidationAdditional:
    """Additional tests for security validation"""

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
