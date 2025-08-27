"""
Security validation utilities for input sanitization and threat detection
"""

import re
from typing import List, Optional, Tuple


class SecurityError(Exception):
    """Raised when security validation fails"""

    pass


class InputValidator:
    """Security input validation utilities"""

    # Common dangerous patterns for path traversal and injection attacks
    DANGEROUS_PATTERNS = [
        "../",
        "..%2f",
        "..%2F",  # Path traversal attempts
        "/api/v1/user/",
        "/user/",  # Endpoint injection attempts
        "admin/",
        "root/",
        "system/",  # Privilege escalation attempts
        "<script",
        "javascript:",
        "data:",  # XSS attempts
        "select ",
        "union ",
        "insert ",
        "update ",
        "delete ",  # SQL injection
        "exec(",
        "eval(",
        "system(",
        "__import__",  # Code injection
    ]

    # Valid patterns for usernames and endpoint names
    VALID_USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")
    VALID_ENDPOINT_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

    @classmethod
    def validate_input_security(
        cls, value: str, field_name: str = "input", allow_empty: bool = False
    ) -> None:
        """
        Validate input for security threats

        Args:
            value: The input value to validate
            field_name: Name of the field being validated (for error messages)
            allow_empty: Whether to allow empty strings

        Raises:
            SecurityError: If dangerous patterns are detected
        """
        if not value and not allow_empty:
            raise SecurityError(f"{field_name} cannot be empty")

        if not value:
            return  # Empty string allowed

        # Convert to lowercase for case-insensitive pattern matching
        value_lower = value.lower()

        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if pattern.lower() in value_lower:
                raise SecurityError(
                    f"Dangerous pattern detected in {field_name}: {pattern}"
                )

    @classmethod
    def validate_username(cls, username: str) -> None:
        """
        Validate username format and security

        Args:
            username: The username to validate

        Raises:
            SecurityError: If username is invalid or contains dangerous patterns
        """
        if not username:
            raise SecurityError("Username cannot be empty")

        # Check for dangerous patterns first
        cls.validate_input_security(username, "username")

        # Check format
        if not cls.VALID_USERNAME_PATTERN.match(username):
            raise SecurityError(
                "Username must contain only letters, numbers, hyphens, and underscores"
            )

        # Length check
        if len(username) > 50:
            raise SecurityError("Username cannot exceed 50 characters")

    @classmethod
    def validate_endpoint_name(cls, endpoint_name: str) -> None:
        """
        Validate endpoint name format and security

        Args:
            endpoint_name: The endpoint name to validate

        Raises:
            SecurityError: If endpoint name is invalid or contains dangerous patterns
        """
        if not endpoint_name:
            raise SecurityError("Endpoint name cannot be empty")

        # Check for dangerous patterns first
        cls.validate_input_security(endpoint_name, "endpoint_name")

        # Check format
        if not cls.VALID_ENDPOINT_PATTERN.match(endpoint_name):
            raise SecurityError(
                "Endpoint name must contain only letters, numbers, hyphens, and underscores"
            )

        # Length check
        if len(endpoint_name) > 50:
            raise SecurityError("Endpoint name cannot exceed 50 characters")

    @classmethod
    def validate_route_parameters(
        cls, username: Optional[str] = None, endpoint_name: Optional[str] = None
    ) -> None:
        """
        Validate route parameters for security

        Args:
            username: Optional username to validate
            endpoint_name: Optional endpoint name to validate

        Raises:
            SecurityError: If any parameter is invalid
        """
        if username is not None:
            cls.validate_username(username)

        if endpoint_name is not None:
            cls.validate_endpoint_name(endpoint_name)

    @classmethod
    def get_security_violations(cls, value: str) -> List[str]:
        """
        Get list of security violations in a value without raising exceptions

        Args:
            value: The value to check

        Returns:
            List of detected dangerous patterns
        """
        if not value:
            return []

        value_lower = value.lower()
        violations = []

        for pattern in cls.DANGEROUS_PATTERNS:
            if pattern.lower() in value_lower:
                violations.append(pattern)

        return violations

    @classmethod
    def is_safe_input(cls, value: str) -> bool:
        """
        Check if input is safe without raising exceptions

        Args:
            value: The value to check

        Returns:
            True if input is safe, False otherwise
        """
        return len(cls.get_security_violations(value)) == 0


def validate_user_route_security(username: str, endpoint_name: str) -> None:
    """
    Convenience function to validate user route parameters

    Args:
        username: The username parameter
        endpoint_name: The endpoint name parameter

    Raises:
        SecurityError: If validation fails
    """
    InputValidator.validate_route_parameters(username, endpoint_name)


def validate_endpoint_route_security(endpoint_name: str) -> None:
    """
    Convenience function to validate endpoint route parameters

    Args:
        endpoint_name: The endpoint name parameter

    Raises:
        SecurityError: If validation fails
    """
    InputValidator.validate_endpoint_name(endpoint_name)
