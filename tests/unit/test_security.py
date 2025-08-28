"""
Comprehensive security validation tests - consolidated from multiple test files
Covers all security validation functionality with proper testing of attack vectors
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
            "test_123",
            "my-project",
            "user_data",
            "simple_name",
            "AbCdEf",
            "123456",
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
            "../../etc/passwd",
            "..\\..\\windows\\system32",
            "%2e%2e%2f%2e%2e%2fpasswd",
        ]

        for dangerous_input in dangerous_inputs:
            with pytest.raises(SecurityError) as exc_info:
                InputValidator.validate_input_security(dangerous_input, "test_field")
            assert "Dangerous pattern detected" in str(exc_info.value)

    def test_validate_input_security_endpoint_injection(self):
        """Test detection of endpoint injection attacks"""
        endpoint_injections = [
            "/api/v1/user/admin",
            "/api/v1/endpoint/malicious",
            "/user/admin",
            "/admin/users",
            "api/v1/admin",
            "user/bypass",
        ]

        for injection in endpoint_injections:
            with pytest.raises(SecurityError) as exc_info:
                InputValidator.validate_input_security(injection, "test_field")
            assert "Dangerous pattern detected" in str(exc_info.value)

    def test_validate_input_security_privilege_escalation(self):
        """Test detection of privilege escalation attempts"""
        privilege_attacks = [
            "admin/bypass",
            "root/access",
            "system/command",
            "superuser/data",
            "administrator/panel",
        ]

        for attack in privilege_attacks:
            with pytest.raises(SecurityError) as exc_info:
                InputValidator.validate_input_security(attack, "test_field")
            assert "Dangerous pattern detected" in str(exc_info.value)

    def test_validate_input_security_xss_attacks(self):
        """Test detection of XSS attacks"""
        xss_attacks = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "<iframe src=javascript:alert('xss')>",
            "onload=alert('xss')",
            "onerror=alert('xss')",
        ]

        for attack in xss_attacks:
            with pytest.raises(SecurityError) as exc_info:
                InputValidator.validate_input_security(attack, "test_field")
            assert "Dangerous pattern detected" in str(exc_info.value)

    def test_validate_input_security_sql_injection(self):
        """Test detection of SQL injection attacks"""
        sql_attacks = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "1; SELECT * FROM users",
            "UNION SELECT password FROM users",
            "INSERT INTO users VALUES",
            "UPDATE users SET admin=1",
            "DELETE FROM users WHERE",
            "' UNION ALL SELECT NULL--",
            "admin'--",
            "' OR 1=1--",
        ]

        for attack in sql_attacks:
            with pytest.raises(SecurityError) as exc_info:
                InputValidator.validate_input_security(attack, "test_field")
            assert "Dangerous pattern detected" in str(exc_info.value)

    def test_validate_input_security_code_injection(self):
        """Test detection of code injection attacks"""
        code_attacks = [
            "exec('malicious code')",
            "eval('dangerous')",
            "system('rm -rf /')",
            "__import__('os').system('pwd')",
            "os.system('malicious')",
            "subprocess.call(['rm', '-rf', '/'])",
            "open('/etc/passwd').read()",
        ]

        for attack in code_attacks:
            with pytest.raises(SecurityError) as exc_info:
                InputValidator.validate_input_security(attack, "test_field")
            assert "Dangerous pattern detected" in str(exc_info.value)

    def test_validate_input_security_url_encoded_attacks(self):
        """Test detection of URL-encoded attacks"""
        url_encoded_attacks = [
            "..%2f",  # URL-encoded ../
            "..%2F",  # URL-encoded ../ (uppercase)
            "%2e%2e%2f",  # Double URL-encoded ../
            "%2e%2e%5c",  # URL-encoded ..\
            "%252e%252e%252f",  # Triple URL-encoded ../
        ]

        for attack in url_encoded_attacks:
            with pytest.raises(SecurityError):
                InputValidator.validate_input_security(attack, "test_field")

    def test_validate_input_security_null_byte_injection(self):
        """Test detection of null byte injection"""
        null_byte_attacks = [
            "test\x00.txt",
            "file.txt\x00.exe",
            "endpoint\x00admin",
            "user\x00root",
        ]

        for attack in null_byte_attacks:
            with pytest.raises(SecurityError):
                InputValidator.validate_input_security(attack, "test_field")

    def test_validate_input_security_empty_input(self):
        """Test handling of empty input"""
        # Empty input should be allowed (handled by other validation)
        InputValidator.validate_input_security("", "test_field")

    def test_validate_input_security_none_input(self):
        """Test handling of None input"""
        # None input should be handled gracefully
        with pytest.raises((SecurityError, TypeError)):
            InputValidator.validate_input_security(None, "test_field")

    def test_validate_input_security_whitespace_input(self):
        """Test handling of whitespace-only input"""
        whitespace_inputs = [
            " ",
            "\t",
            "\n",
            "\r",
            "   ",
            "\t\n\r",
        ]

        for whitespace in whitespace_inputs:
            # Whitespace should be allowed
            InputValidator.validate_input_security(whitespace, "test_field")

    def test_validate_input_security_unicode_attacks(self):
        """Test detection of unicode-based attacks"""
        unicode_attacks = [
            "＜script＞alert('xss')＜/script＞",  # Full-width characters
            "ᅟᅟ../admin",  # Unicode spaces with path traversal
            "test\u200b../admin",  # Zero-width space
            "test\ufeff../admin",  # Byte order mark
        ]

        for attack in unicode_attacks:
            # Should detect dangerous patterns even with unicode
            try:
                InputValidator.validate_input_security(attack, "test_field")
                # If it doesn't raise, check if it contains dangerous patterns
                if any(
                    pattern in attack.lower() for pattern in ["../", "script", "admin"]
                ):
                    pytest.fail(f"Should have detected dangerous pattern in: {attack}")
            except SecurityError:
                pass  # This is expected

    def test_validate_input_security_mixed_case_attacks(self):
        """Test detection of mixed case attacks"""
        mixed_case_attacks = [
            "ScRiPt",
            "EvAl",
            "SyStEm",
            "AdMiN",
            "RoOt",
            "UnIoN sElEcT",
        ]

        for attack in mixed_case_attacks:
            with pytest.raises(SecurityError):
                InputValidator.validate_input_security(attack, "test_field")

    def test_validate_input_security_length_boundaries(self):
        """Test validation with various input lengths"""
        # Very short inputs
        short_inputs = ["a", "1", "_", "-"]
        for short_input in short_inputs:
            InputValidator.validate_input_security(short_input, "test_field")

        # Very long safe input
        long_safe = "a" * 1000
        InputValidator.validate_input_security(long_safe, "test_field")

        # Very long dangerous input
        long_dangerous = "../" * 500
        with pytest.raises(SecurityError):
            InputValidator.validate_input_security(long_dangerous, "test_field")

    def test_validate_input_security_special_characters(self):
        """Test validation with special characters"""
        safe_special_chars = [
            "test_file",
            "project-name",
            "version.1.0",
            "user@domain",
            "item#1",
            "value$100",
            "question?",
            "percent%",
            "and&more",
            "star*",
            "plus+",
            "equals=",
        ]

        for char_input in safe_special_chars:
            # Most special characters should be allowed
            InputValidator.validate_input_security(char_input, "test_field")


class TestValidateEndpointRouteSecurity:
    """Test endpoint route security validation"""

    def test_validate_endpoint_route_security_safe_routes(self):
        """Test validation of safe endpoint routes"""
        safe_routes = [
            "about",
            "projects",
            "resume",
            "skills",
            "experience",
            "education",
            "contacts",
            "ideas",
            "notes",
            "tasks",
        ]

        for route in safe_routes:
            # Should not raise exception
            validate_endpoint_route_security(route)

    def test_validate_endpoint_route_security_dangerous_routes(self):
        """Test detection of dangerous endpoint routes"""
        dangerous_routes = [
            "../admin",
            "admin/users",
            "system/config",
            "/etc/passwd",
            "..%2fadmin",
            "endpoint/../admin",
            "api/v1/admin",
        ]

        for route in dangerous_routes:
            with pytest.raises(SecurityError):
                validate_endpoint_route_security(route)

    def test_validate_endpoint_route_security_empty_route(self):
        """Test validation of empty route"""
        with pytest.raises(SecurityError):
            validate_endpoint_route_security("")

    def test_validate_endpoint_route_security_none_route(self):
        """Test validation of None route"""
        with pytest.raises((SecurityError, TypeError)):
            validate_endpoint_route_security(None)

    def test_validate_endpoint_route_security_numeric_routes(self):
        """Test validation of numeric routes"""
        numeric_routes = ["123", "456", "999"]

        for route in numeric_routes:
            # Numeric routes should be allowed
            validate_endpoint_route_security(route)

    def test_validate_endpoint_route_security_mixed_routes(self):
        """Test validation of mixed alphanumeric routes"""
        mixed_routes = [
            "project1",
            "idea_2",
            "task-3",
            "note.4",
        ]

        for route in mixed_routes:
            validate_endpoint_route_security(route)


class TestValidateUserRouteSecurity:
    """Test user route security validation"""

    def test_validate_user_route_security_safe_routes(self):
        """Test validation of safe user routes"""
        safe_routes = [
            "profile",
            "settings",
            "preferences",
            "dashboard",
            "data",
            "export",
            "import",
        ]

        for route in safe_routes:
            validate_user_route_security(route)

    def test_validate_user_route_security_dangerous_routes(self):
        """Test detection of dangerous user routes"""
        dangerous_routes = [
            "../admin",
            "admin/bypass",
            "system/access",
            "/api/v1/admin",
            "..%2fadmin",
            "root/access",
        ]

        for route in dangerous_routes:
            with pytest.raises(SecurityError):
                validate_user_route_security(route)

    def test_validate_user_route_security_empty_route(self):
        """Test validation of empty user route"""
        with pytest.raises(SecurityError):
            validate_user_route_security("")

    def test_validate_user_route_security_privilege_escalation(self):
        """Test detection of privilege escalation in user routes"""
        escalation_attempts = [
            "admin",
            "administrator",
            "root",
            "superuser",
            "system",
            "sudo",
        ]

        for attempt in escalation_attempts:
            with pytest.raises(SecurityError):
                validate_user_route_security(attempt)


class TestSecurityValidationEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_security_validation_with_encoding_attacks(self):
        """Test security validation with various encoding attacks"""
        encoding_attacks = [
            "%252e%252e%252f",  # Triple URL encoding
            "%c0%ae%c0%ae%c0%af",  # UTF-8 overlong encoding
            "%u002e%u002e%u002f",  # Unicode encoding
        ]

        for attack in encoding_attacks:
            with pytest.raises(SecurityError):
                InputValidator.validate_input_security(attack, "test_field")

    def test_security_validation_with_whitespace_evasion(self):
        """Test security validation with whitespace evasion"""
        whitespace_attacks = [
            ".. / admin",
            "admin / users",
            "script \t alert",
            "eval \n ('code')",
        ]

        for attack in whitespace_attacks:
            with pytest.raises(SecurityError):
                InputValidator.validate_input_security(attack, "test_field")

    def test_security_validation_with_comment_evasion(self):
        """Test security validation with comment evasion"""
        comment_attacks = [
            "admin/*comment*/users",
            "script//comment\nalert",
            "eval/**/('code')",
            "union/**/select",
        ]

        for attack in comment_attacks:
            with pytest.raises(SecurityError):
                InputValidator.validate_input_security(attack, "test_field")

    def test_security_validation_performance(self):
        """Test security validation performance with large inputs"""
        # Large safe input
        large_safe = "safe_" * 10000
        InputValidator.validate_input_security(large_safe, "test_field")

        # Large input with dangerous pattern at end
        large_dangerous = "safe_" * 9999 + "../admin"
        with pytest.raises(SecurityError):
            InputValidator.validate_input_security(large_dangerous, "test_field")

    def test_security_validation_with_control_characters(self):
        """Test security validation with control characters"""
        control_char_attacks = [
            "test\x01admin",
            "user\x02root",
            "endpoint\x03system",
            "data\x7f../admin",
        ]

        for attack in control_char_attacks:
            # Should handle control characters appropriately
            try:
                InputValidator.validate_input_security(attack, "test_field")
                # If dangerous patterns are present, should be caught
                if any(
                    pattern in attack for pattern in ["admin", "root", "system", "../"]
                ):
                    pytest.fail(
                        f"Should have detected dangerous pattern in: {repr(attack)}"
                    )
            except SecurityError:
                pass  # Expected for dangerous patterns

    def test_security_validation_case_sensitivity(self):
        """Test that security validation is case-insensitive where appropriate"""
        case_variants = [
            ("ADMIN", "admin"),
            ("ROOT", "root"),
            ("SYSTEM", "system"),
            ("SCRIPT", "script"),
            ("EVAL", "eval"),
        ]

        for upper, lower in case_variants:
            # Both cases should be caught
            with pytest.raises(SecurityError):
                InputValidator.validate_input_security(upper, "test_field")
            with pytest.raises(SecurityError):
                InputValidator.validate_input_security(lower, "test_field")

    def test_security_validation_boundary_patterns(self):
        """Test security validation at pattern boundaries"""
        boundary_tests = [
            "xadmin",  # Contains 'admin' but not at boundary
            "adminx",  # Contains 'admin' but not at boundary
            "rooter",  # Contains 'root' but not at boundary
            "scripted",  # Contains 'script' but not at boundary
        ]

        for test_input in boundary_tests:
            # These should be detected if the patterns are substring matches
            with pytest.raises(SecurityError):
                InputValidator.validate_input_security(test_input, "test_field")

    def test_security_validation_multiple_patterns(self):
        """Test security validation with multiple dangerous patterns"""
        multi_pattern_attacks = [
            "../admin/system",
            "script eval admin",
            "union select admin",
            "exec system admin",
        ]

        for attack in multi_pattern_attacks:
            with pytest.raises(SecurityError):
                InputValidator.validate_input_security(attack, "test_field")

    def test_security_validation_international_characters(self):
        """Test security validation with international characters"""
        international_safe = [
            "résumé",
            "naïve",
            "café",
            "niño",
            "Müller",
            "François",
        ]

        for safe_input in international_safe:
            InputValidator.validate_input_security(safe_input, "test_field")

        # International characters with dangerous patterns
        international_dangerous = [
            "résumé/../admin",
            "café/system",
            "niño<script>",
        ]

        for dangerous_input in international_dangerous:
            with pytest.raises(SecurityError):
                InputValidator.validate_input_security(dangerous_input, "test_field")


class TestSecurityErrorHandling:
    """Test security error handling and reporting"""

    def test_security_error_contains_field_name(self):
        """Test that SecurityError includes the field name"""
        try:
            InputValidator.validate_input_security("../admin", "username")
            pytest.fail("Should have raised SecurityError")
        except SecurityError as e:
            assert "username" in str(e)

    def test_security_error_contains_pattern_info(self):
        """Test that SecurityError includes pattern information"""
        try:
            InputValidator.validate_input_security("../admin", "test_field")
            pytest.fail("Should have raised SecurityError")
        except SecurityError as e:
            assert "Dangerous pattern detected" in str(e)

    def test_security_error_different_patterns(self):
        """Test that different patterns produce appropriate error messages"""
        pattern_tests = [
            ("../admin", "path traversal"),
            ("<script>", "XSS"),
            ("'; DROP TABLE", "SQL injection"),
            ("eval(", "code injection"),
        ]

        for pattern, expected_type in pattern_tests:
            try:
                InputValidator.validate_input_security(pattern, "test_field")
                pytest.fail(f"Should have raised SecurityError for {expected_type}")
            except SecurityError as e:
                # Error should contain information about dangerous pattern
                assert "Dangerous pattern detected" in str(e)

    def test_security_validation_logging(self):
        """Test that security validation attempts are logged appropriately"""
        # This test would require checking logging output
        # For now, just ensure validation works without logging errors

        try:
            InputValidator.validate_input_security("../admin", "test_field")
            pytest.fail("Should have raised SecurityError")
        except SecurityError:
            pass  # Expected

        # Safe input should not cause logging issues
        InputValidator.validate_input_security("safe_input", "test_field")
