"""
Unit tests for authentication functionality
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from passlib.context import CryptContext

from app.auth import (
    create_access_token,
    generate_api_key,
    get_current_admin_user,
    get_current_user,
    get_password_hash,
    verify_password,
)


class TestPasswordHandling:
    """Test password hashing and verification"""

    def test_get_password_hash(self):
        """Test password hashing"""
        password = "test_password_123"
        hashed = get_password_hash(password)

        # Hash should be different from original password
        assert hashed != password
        # Hash should be a string
        assert isinstance(hashed, str)
        # Hash should have reasonable length
        assert len(hashed) > 50

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "test_password_123"
        hashed = get_password_hash(password)

        # Verification should succeed
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "test_password_123"
        wrong_password = "wrong_password_456"
        hashed = get_password_hash(password)

        # Verification should fail
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_password(self):
        """Test password verification with empty password"""
        password = "test_password_123"
        hashed = get_password_hash(password)

        # Empty password should fail
        assert verify_password("", hashed) is False

    def test_verify_password_empty_hash(self):
        """Test password verification with empty hash"""
        password = "test_password_123"

        # Empty hash should fail
        assert verify_password(password, "") is False

    def test_password_hash_consistency(self):
        """Test that same password produces different hashes (salt)"""
        password = "test_password_123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashes should be different due to salt
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_password_special_characters(self):
        """Test password handling with special characters"""
        special_passwords = [
            "password!@#$%^&*()",
            "pássword_wïth_ûnicode",
            "pass word with spaces",
            "password\nwith\nnewlines",
            "password\twith\ttabs",
            "中文密码测试",
            "password🔒🚀",
        ]

        for password in special_passwords:
            hashed = get_password_hash(password)
            assert verify_password(password, hashed) is True

    def test_very_long_password(self):
        """Test handling of very long passwords"""
        long_password = "a" * 1000
        hashed = get_password_hash(long_password)
        assert verify_password(long_password, hashed) is True


class TestTokenGeneration:
    """Test JWT token creation and validation"""

    @patch("app.auth.settings")
    def test_create_access_token_basic(self, mock_settings):
        """Test basic access token creation"""
        mock_settings.SECRET_KEY = "test_secret_key"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30

        data = {"sub": "testuser"}
        token = create_access_token(data)

        # Token should be a string
        assert isinstance(token, str)
        # Token should have JWT structure (3 parts separated by dots)
        parts = token.split(".")
        assert len(parts) == 3

    @patch("app.auth.settings")
    def test_create_access_token_with_expiry(self, mock_settings):
        """Test access token creation with custom expiry"""
        mock_settings.SECRET_KEY = "test_secret_key"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30

        data = {"sub": "testuser"}
        expires_delta = timedelta(hours=2)
        token = create_access_token(data, expires_delta)

        assert isinstance(token, str)
        parts = token.split(".")
        assert len(parts) == 3

    @patch("app.auth.settings")
    def test_create_access_token_empty_data(self, mock_settings):
        """Test access token creation with empty data"""
        mock_settings.SECRET_KEY = "test_secret_key"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30

        data = {}
        token = create_access_token(data)

        assert isinstance(token, str)

    @patch("app.auth.settings")
    def test_create_access_token_complex_data(self, mock_settings):
        """Test access token creation with complex data"""
        mock_settings.SECRET_KEY = "test_secret_key"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30

        data = {
            "sub": "testuser",
            "role": "admin",
            "permissions": ["read", "write", "admin"],
            "metadata": {"team": "development"},
        }
        token = create_access_token(data)

        assert isinstance(token, str)
        parts = token.split(".")
        assert len(parts) == 3


class TestUserAuthentication:
    """Test user authentication and authorization"""

    @patch("app.auth.get_db")
    @patch("app.auth.jwt.decode")
    def test_get_current_user_success(self, mock_jwt_decode, mock_get_db):
        """Test successful user authentication"""
        # Mock JWT decode
        mock_jwt_decode.return_value = {"sub": "testuser"}

        # Mock database
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock user
        mock_user = MagicMock()
        mock_user.username = "testuser"
        mock_user.is_active = True
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        # Test authentication
        token = "valid_jwt_token"
        user = get_current_user(token, mock_db)

        assert user.username == "testuser"

    @patch("app.auth.get_db")
    @patch("app.auth.jwt.decode")
    def test_get_current_user_invalid_token(self, mock_jwt_decode, mock_get_db):
        """Test authentication with invalid token"""
        # Mock JWT decode to raise exception
        mock_jwt_decode.side_effect = Exception("Invalid token")

        mock_db = MagicMock()

        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            get_current_user("invalid_token", mock_db)

        assert exc_info.value.status_code == 401

    @patch("app.auth.get_db")
    @patch("app.auth.jwt.decode")
    def test_get_current_user_user_not_found(self, mock_jwt_decode, mock_get_db):
        """Test authentication when user doesn't exist"""
        # Mock JWT decode
        mock_jwt_decode.return_value = {"sub": "nonexistent"}

        # Mock database
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            get_current_user("valid_token", mock_db)

        assert exc_info.value.status_code == 401

    @patch("app.auth.get_db")
    @patch("app.auth.jwt.decode")
    def test_get_current_user_inactive_user(self, mock_jwt_decode, mock_get_db):
        """Test authentication with inactive user"""
        # Mock JWT decode
        mock_jwt_decode.return_value = {"sub": "testuser"}

        # Mock database
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock inactive user
        mock_user = MagicMock()
        mock_user.username = "testuser"
        mock_user.is_active = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            get_current_user("valid_token", mock_db)

        assert exc_info.value.status_code == 401

    @patch("app.auth.get_current_user")
    def test_get_current_admin_user_success(self, mock_get_current_user):
        """Test successful admin user authentication"""
        # Mock admin user
        mock_user = MagicMock()
        mock_user.username = "admin"
        mock_user.is_admin = True
        mock_get_current_user.return_value = mock_user

        admin_user = get_current_admin_user("valid_token", MagicMock())

        assert admin_user.username == "admin"
        assert admin_user.is_admin is True

    @patch("app.auth.get_current_user")
    def test_get_current_admin_user_not_admin(self, mock_get_current_user):
        """Test admin authentication with non-admin user"""
        # Mock non-admin user
        mock_user = MagicMock()
        mock_user.username = "user"
        mock_user.is_admin = False
        mock_get_current_user.return_value = mock_user

        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            get_current_admin_user("valid_token", MagicMock())

        assert exc_info.value.status_code == 403

    @patch("app.auth.get_current_user")
    def test_get_current_admin_user_user_auth_fails(self, mock_get_current_user):
        """Test admin authentication when user auth fails"""
        # Mock user authentication failure
        mock_get_current_user.side_effect = HTTPException(status_code=401)

        # Should propagate HTTPException
        with pytest.raises(HTTPException) as exc_info:
            get_current_admin_user("invalid_token", MagicMock())

        assert exc_info.value.status_code == 401


class TestApiKeyGeneration:
    """Test API key generation"""

    def test_generate_api_key_basic(self):
        """Test basic API key generation"""
        api_key = generate_api_key()

        # API key should be a string
        assert isinstance(api_key, str)
        # API key should have reasonable length
        assert len(api_key) >= 32
        # API key should contain only safe characters
        safe_chars = set(
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        )
        assert all(c in safe_chars for c in api_key)

    def test_generate_api_key_uniqueness(self):
        """Test that generated API keys are unique"""
        keys = [generate_api_key() for _ in range(100)]

        # All keys should be unique
        assert len(set(keys)) == 100

    def test_generate_api_key_length(self):
        """Test API key length consistency"""
        keys = [generate_api_key() for _ in range(10)]

        # All keys should have same length
        lengths = [len(key) for key in keys]
        assert len(set(lengths)) == 1  # All lengths should be the same


class TestAuthenticationSecurityValidation:
    """Test security aspects of authentication"""

    def test_password_hash_timing_attack_resistance(self):
        """Test that password hashing is resistant to timing attacks"""
        import time

        short_password = "abc"
        long_password = "a" * 1000

        # Time hashing of short password
        start = time.time()
        get_password_hash(short_password)
        short_time = time.time() - start

        # Time hashing of long password
        start = time.time()
        get_password_hash(long_password)
        long_time = time.time() - start

        # Times should be relatively similar (within order of magnitude)
        # This is a basic check - real timing attack analysis would be more sophisticated
        assert long_time < short_time * 10

    def test_password_verification_timing_attack_resistance(self):
        """Test that password verification is resistant to timing attacks"""
        import time

        password = "test_password"
        hashed = get_password_hash(password)
        wrong_password = "wrong_password"

        # Time correct password verification
        times_correct = []
        for _ in range(10):
            start = time.time()
            verify_password(password, hashed)
            times_correct.append(time.time() - start)

        # Time incorrect password verification
        times_incorrect = []
        for _ in range(10):
            start = time.time()
            verify_password(wrong_password, hashed)
            times_incorrect.append(time.time() - start)

        # Average times should be relatively similar
        avg_correct = sum(times_correct) / len(times_correct)
        avg_incorrect = sum(times_incorrect) / len(times_incorrect)

        # This is a basic check - real timing analysis would be more sophisticated
        assert abs(avg_correct - avg_incorrect) < max(avg_correct, avg_incorrect) * 2

    def test_token_creation_with_malicious_data(self):
        """Test token creation with potentially malicious data"""
        with patch("app.auth.settings") as mock_settings:
            mock_settings.SECRET_KEY = "test_secret_key"
            mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30

            malicious_data = {
                "sub": "<script>alert('xss')</script>",
                "role": "'; DROP TABLE users; --",
                "eval": "eval('malicious_code')",
                "proto": "__proto__",
            }

            # Should create token without errors
            token = create_access_token(malicious_data)
            assert isinstance(token, str)

    def test_empty_or_none_passwords(self):
        """Test handling of empty or None passwords"""
        # Empty password should be handled gracefully
        with pytest.raises((ValueError, TypeError)):
            get_password_hash("")

        # None password should be handled gracefully
        with pytest.raises((ValueError, TypeError)):
            get_password_hash(None)

    def test_very_weak_passwords(self):
        """Test handling of very weak passwords"""
        weak_passwords = ["1", "a", "123", "abc", "password", "123456", "qwerty"]

        for weak_password in weak_passwords:
            # Should still hash and verify correctly (policy enforcement is elsewhere)
            hashed = get_password_hash(weak_password)
            assert verify_password(weak_password, hashed) is True

    def test_sql_injection_in_usernames(self):
        """Test that SQL injection in usernames is handled safely"""
        with (
            patch("app.auth.get_db") as mock_get_db,
            patch("app.auth.jwt.decode") as mock_jwt_decode,
        ):

            # Mock JWT decode with malicious username
            mock_jwt_decode.return_value = {"sub": "'; DROP TABLE users; --"}

            # Mock database
            mock_db = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = None

            # Should handle malicious username safely (SQLAlchemy should parameterize)
            with pytest.raises(HTTPException) as exc_info:
                get_current_user("token", mock_db)

            # Should fail due to user not found, not due to SQL error
            assert exc_info.value.status_code == 401

    def test_unicode_in_authentication(self):
        """Test handling of unicode characters in authentication"""
        unicode_usernames = [
            "用户名",  # Chinese
            "ユーザー",  # Japanese
            "пользователь",  # Russian
            "user🚀",  # Emoji
        ]

        with (
            patch("app.auth.get_db") as mock_get_db,
            patch("app.auth.jwt.decode") as mock_jwt_decode,
        ):

            mock_db = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_db

            for username in unicode_usernames:
                mock_jwt_decode.return_value = {"sub": username}
                mock_db.query.return_value.filter.return_value.first.return_value = None

                # Should handle unicode usernames without errors
                with pytest.raises(HTTPException) as exc_info:
                    get_current_user("token", mock_db)

                assert exc_info.value.status_code == 401

    def test_api_key_entropy(self):
        """Test that generated API keys have sufficient entropy"""
        api_keys = [generate_api_key() for _ in range(100)]

        # Check character distribution
        all_chars = "".join(api_keys)
        char_counts = {}
        for char in all_chars:
            char_counts[char] = char_counts.get(char, 0) + 1

        # Should use a reasonable variety of characters
        assert len(char_counts) > 20  # Should use most available characters

        # No character should be overly dominant
        total_chars = len(all_chars)
        for count in char_counts.values():
            frequency = count / total_chars
            assert frequency < 0.1  # No char should be >10% of total

    def test_token_expiry_boundary_conditions(self):
        """Test token creation with boundary expiry times"""
        with patch("app.auth.settings") as mock_settings:
            mock_settings.SECRET_KEY = "test_secret_key"
            mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30

            data = {"sub": "testuser"}

            # Test very short expiry
            very_short = timedelta(seconds=1)
            token = create_access_token(data, very_short)
            assert isinstance(token, str)

            # Test very long expiry
            very_long = timedelta(days=365)
            token = create_access_token(data, very_long)
            assert isinstance(token, str)

            # Test zero expiry
            zero_expiry = timedelta(seconds=0)
            token = create_access_token(data, zero_expiry)
            assert isinstance(token, str)
