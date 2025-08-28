"""
Comprehensive utils tests - consolidated from multiple test files
Covers all utility functions with proper mocking and security testing
"""

import json
import os
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, mock_open, patch

import pytest

from app.schemas import BackupResponse
from app.utils import (
    cleanup_old_backups,
    create_backup,
    export_endpoint_data,
    format_bytes,
    get_backup_files_to_delete,
    get_single_user,
    get_system_metrics,
    get_uptime,
    health_check,
    import_endpoint_data,
    is_single_user_mode,
    mask_sensitive_data,
    sanitize_data_dict,
    sanitize_data_entry,
    sanitize_filename,
    sanitize_input,
    validate_endpoint_name,
    validate_json_schema,
    validate_url,
)


class TestSanitizationFunctions:
    """Test input sanitization functions"""

    def test_sanitize_input_string(self):
        """Test string input sanitization"""
        # Normal strings should pass through
        assert sanitize_input("hello world") == "hello world"
        assert sanitize_input("user123") == "user123"
        assert sanitize_input("simple_text") == "simple_text"

        # HTML should be escaped
        result = sanitize_input("<script>alert('xss')</script>")
        assert "&lt;script&gt;" in result
        assert "&lt;/script&gt;" in result

        # Special characters should be escaped
        result = sanitize_input("user&company")
        assert "&amp;" in result

        # Quotes should be escaped
        result = sanitize_input('He said "Hello"')
        assert "&quot;" in result

    def test_sanitize_input_non_string(self):
        """Test non-string input sanitization"""
        # Numbers should pass through
        assert sanitize_input(123) == 123
        assert sanitize_input(45.67) == 45.67
        assert sanitize_input(0) == 0
        assert sanitize_input(-123) == -123

        # Booleans should pass through
        assert sanitize_input(True) is True
        assert sanitize_input(False) is False

        # None should pass through
        assert sanitize_input(None) is None

    def test_sanitize_input_edge_cases(self):
        """Test edge cases for input sanitization"""
        # Empty string
        assert sanitize_input("") == ""

        # Whitespace only
        assert sanitize_input("   ") == "   "

        # Unicode characters
        assert sanitize_input("café") == "café"
        assert sanitize_input("测试") == "测试"

        # Mixed content
        result = sanitize_input("Normal text <script>alert('xss')</script> more text")
        assert "Normal text" in result
        assert "&lt;script&gt;" in result
        assert "more text" in result

    def test_sanitize_data_dict(self):
        """Test dictionary data sanitization"""
        input_dict = {
            "safe_key": "safe_value",
            "html_key": "<script>alert('xss')</script>",
            "number_key": 123,
            "bool_key": True,
            "nested_dict": {
                "nested_html": "<img src=x onerror=alert('xss')>",
                "nested_safe": "safe_nested_value",
            },
            "list_key": ["safe_item", "<script>", 456, True],
        }

        result = sanitize_data_dict(input_dict)

        # Safe values should pass through
        assert result["safe_key"] == "safe_value"
        assert result["number_key"] == 123
        assert result["bool_key"] is True

        # HTML should be escaped
        assert "&lt;script&gt;" in result["html_key"]

        # Nested dictionary should be sanitized
        assert "&lt;img" in result["nested_dict"]["nested_html"]
        assert result["nested_dict"]["nested_safe"] == "safe_nested_value"

        # Lists should be sanitized
        assert result["list_key"][0] == "safe_item"
        assert "&lt;script&gt;" in result["list_key"][1]
        assert result["list_key"][2] == 456
        assert result["list_key"][3] is True

    def test_sanitize_data_entry(self):
        """Test data entry sanitization"""
        # Test with dictionary
        dict_entry = {
            "title": "Test Entry",
            "content": "<script>alert('xss')</script>",
            "metadata": {"author": "user<script>"},
        }

        result = sanitize_data_entry(dict_entry)
        assert result["title"] == "Test Entry"
        assert "&lt;script&gt;" in result["content"]
        assert "&lt;script&gt;" in result["metadata"]["author"]

        # Test with non-dictionary
        string_entry = "<script>alert('xss')</script>"
        result = sanitize_data_entry(string_entry)
        assert "&lt;script&gt;" in result

    def test_sanitize_filename(self):
        """Test filename sanitization"""
        # Safe filenames should pass through
        assert sanitize_filename("normal_file.txt") == "normal_file.txt"
        assert sanitize_filename("file-123.json") == "file-123.json"

        # Dangerous characters should be removed or replaced
        dangerous_chars = ["../", "..\\", "/", "\\", ":", "*", "?", "<", ">", "|"]
        for char in dangerous_chars:
            filename = f"test{char}file.txt"
            result = sanitize_filename(filename)
            assert char not in result

        # Path traversal should be blocked
        assert sanitize_filename("../../../etc/passwd") != "../../../etc/passwd"
        assert (
            sanitize_filename("..\\..\\windows\\system32")
            != "..\\..\\windows\\system32"
        )

        # Empty or None should be handled
        assert sanitize_filename("") != ""
        assert sanitize_filename(None) is not None

    def test_mask_sensitive_data(self):
        """Test sensitive data masking"""
        sensitive_data = {
            "password": "secret123",
            "api_key": "sk-1234567890abcdef",
            "token": "bearer_token_value",
            "secret": "top_secret",
            "key": "encryption_key",
            "username": "normal_user",  # Should not be masked
            "email": "user@example.com",  # Should not be masked
        }

        result = mask_sensitive_data(sensitive_data)

        # Sensitive fields should be masked
        assert result["password"] == "***"
        assert result["api_key"] == "***"
        assert result["token"] == "***"
        assert result["secret"] == "***"
        assert result["key"] == "***"

        # Non-sensitive fields should remain
        assert result["username"] == "normal_user"
        assert result["email"] == "user@example.com"

    def test_mask_sensitive_data_nested(self):
        """Test masking sensitive data in nested structures"""
        nested_data = {
            "user": {
                "username": "testuser",
                "password": "secret123",
                "profile": {"api_key": "sk-abcdef", "name": "Test User"},
            },
            "config": {"database_password": "db_secret", "debug": True},
        }

        result = mask_sensitive_data(nested_data)

        assert result["user"]["username"] == "testuser"
        assert result["user"]["password"] == "***"
        assert result["user"]["profile"]["api_key"] == "***"
        assert result["user"]["profile"]["name"] == "Test User"
        assert result["config"]["database_password"] == "***"
        assert result["config"]["debug"] is True


class TestValidationFunctions:
    """Test validation functions"""

    def test_validate_endpoint_name(self):
        """Test endpoint name validation"""
        # Valid endpoint names
        valid_names = [
            "projects",
            "ideas",
            "resume",
            "about",
            "skills",
            "experience",
            "education",
            "contacts",
        ]

        for name in valid_names:
            assert validate_endpoint_name(name) is True

        # Invalid endpoint names
        invalid_names = [
            "",
            None,
            "../admin",
            "admin/users",
            "<script>",
            "endpoint with spaces",
            "endpoint/with/slashes",
            "endpoint..json",
        ]

        for name in invalid_names:
            assert validate_endpoint_name(name) is False

    def test_validate_url(self):
        """Test URL validation"""
        # Valid URLs
        valid_urls = [
            "http://example.com",
            "https://example.com",
            "https://example.com/path",
            "https://example.com:8080",
            "https://subdomain.example.com",
            "http://localhost:3000",
        ]

        for url in valid_urls:
            assert validate_url(url) is True

        # Invalid URLs
        invalid_urls = [
            "",
            None,
            "not_a_url",
            "ftp://example.com",  # Non-HTTP(S)
            "javascript:alert('xss')",
            "data:text/html,<script>",
            "file:///etc/passwd",
            "http://",
            "https://",
        ]

        for url in invalid_urls:
            assert validate_url(url) is False

    def test_validate_json_schema(self):
        """Test JSON schema validation"""
        # Valid JSON
        valid_json_strings = [
            '{"key": "value"}',
            "[]",
            "{}",
            '{"array": [1, 2, 3]}',
            '{"nested": {"object": true}}',
        ]

        for json_str in valid_json_strings:
            assert validate_json_schema(json_str) is True

        # Invalid JSON
        invalid_json_strings = [
            "",
            None,
            "not json",
            '{"missing": quote}',
            '{"trailing": "comma",}',
            '{key: "no quotes"}',
            '{"unclosed": ',
        ]

        for json_str in invalid_json_strings:
            assert validate_json_schema(json_str) is False


class TestBackupOperations:
    """Test backup creation and management"""

    @patch("app.utils.settings")
    @patch("app.utils.os.path.exists")
    @patch("app.utils.shutil.copy2")
    @patch("app.utils.os.path.getsize")
    @patch("app.utils.os.makedirs")
    def test_create_backup_success(
        self, mock_makedirs, mock_getsize, mock_copy, mock_exists, mock_settings
    ):
        """Test successful backup creation"""
        # Mock settings
        mock_settings.DATABASE_URL = "sqlite:///test.db"
        mock_settings.BACKUP_DIR = "/backups"

        # Mock file operations
        mock_exists.return_value = True
        mock_getsize.return_value = 1024 * 1024  # 1MB

        # Call function
        result = create_backup()

        # Verify backup file name format
        assert result.startswith("daemon_backup_")
        assert result.endswith(".db")

        # Verify file operations were called
        mock_makedirs.assert_called_once()
        mock_copy.assert_called_once()

    @patch("app.utils.settings")
    @patch("app.utils.os.path.exists")
    def test_create_backup_source_not_exists(self, mock_exists, mock_settings):
        """Test backup creation when source database doesn't exist"""
        mock_settings.DATABASE_URL = "sqlite:///nonexistent.db"
        mock_settings.BACKUP_DIR = "/backups"
        mock_exists.return_value = False

        result = create_backup()
        assert result is None

    @patch("app.utils.settings")
    @patch("app.utils.os.path.exists")
    @patch("app.utils.shutil.copy2")
    def test_create_backup_copy_failure(self, mock_copy, mock_exists, mock_settings):
        """Test backup creation when copy operation fails"""
        mock_settings.DATABASE_URL = "sqlite:///test.db"
        mock_settings.BACKUP_DIR = "/backups"
        mock_exists.return_value = True
        mock_copy.side_effect = Exception("Copy failed")

        result = create_backup()
        assert result is None

    @patch("app.utils.os.listdir")
    @patch("app.utils.os.path.getmtime")
    @patch("app.utils.os.remove")
    @patch("app.utils.settings")
    def test_cleanup_old_backups(
        self, mock_settings, mock_remove, mock_getmtime, mock_listdir
    ):
        """Test cleanup of old backup files"""
        mock_settings.BACKUP_DIR = "/backups"
        mock_settings.BACKUP_RETENTION_DAYS = 7

        # Mock backup files with different ages
        old_time = datetime.now().timestamp() - (8 * 24 * 60 * 60)  # 8 days old
        new_time = datetime.now().timestamp() - (3 * 24 * 60 * 60)  # 3 days old

        mock_listdir.return_value = [
            "daemon_backup_old.db",
            "daemon_backup_new.db",
            "other_file.txt",  # Should be ignored
        ]

        def mock_getmtime_side_effect(path):
            if "old" in path:
                return old_time
            elif "new" in path:
                return new_time
            return new_time

        mock_getmtime.side_effect = mock_getmtime_side_effect

        result = cleanup_old_backups()

        # Should remove only old backup files
        assert result == 1
        mock_remove.assert_called_once()

    def test_get_backup_files_to_delete(self):
        """Test getting list of backup files to delete"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test backup files with different timestamps
            old_backup = os.path.join(temp_dir, "daemon_backup_old.db")
            new_backup = os.path.join(temp_dir, "daemon_backup_new.db")

            # Create files
            with open(old_backup, "w") as f:
                f.write("old backup")
            with open(new_backup, "w") as f:
                f.write("new backup")

            # Set old timestamp
            old_time = datetime.now().timestamp() - (10 * 24 * 60 * 60)  # 10 days old
            os.utime(old_backup, (old_time, old_time))

            files_to_delete = get_backup_files_to_delete(temp_dir, retention_days=7)

            # Should include only old file
            assert len(files_to_delete) == 1
            assert "old" in files_to_delete[0]


class TestSystemUtilities:
    """Test system utility functions"""

    def test_format_bytes(self):
        """Test byte formatting"""
        assert format_bytes(1024) == "1.00 KB"
        assert format_bytes(1024 * 1024) == "1.00 MB"
        assert format_bytes(1024 * 1024 * 1024) == "1.00 GB"
        assert format_bytes(0) == "0 B"
        assert format_bytes(512) == "512 B"

    @patch("app.utils.psutil")
    def test_get_system_metrics(self, mock_psutil):
        """Test system metrics gathering"""
        # Mock psutil responses
        mock_psutil.cpu_percent.return_value = 45.2

        mock_memory = MagicMock()
        mock_memory.total = 8 * 1024 * 1024 * 1024  # 8GB
        mock_memory.available = 4 * 1024 * 1024 * 1024  # 4GB
        mock_memory.percent = 50.0
        mock_psutil.virtual_memory.return_value = mock_memory

        mock_disk = MagicMock()
        mock_disk.total = 1024 * 1024 * 1024 * 1024  # 1TB
        mock_disk.free = 512 * 1024 * 1024 * 1024  # 512GB
        mock_disk.percent = 50.0
        mock_psutil.disk_usage.return_value = mock_disk

        metrics = get_system_metrics()

        assert metrics["cpu_usage"] == 45.2
        assert metrics["memory"]["total_gb"] == 8.0
        assert metrics["memory"]["available_gb"] == 4.0
        assert metrics["disk"]["total_gb"] == 1024.0
        assert metrics["disk"]["free_gb"] == 512.0

    @patch("app.utils.psutil")
    def test_get_uptime(self, mock_psutil):
        """Test system uptime calculation"""
        # Mock boot time (1 hour ago)
        boot_time = datetime.now().timestamp() - 3600
        mock_psutil.boot_time.return_value = boot_time

        uptime = get_uptime()

        # Should be approximately 1 hour (3600 seconds)
        assert 3500 < uptime < 3700

    @patch("app.utils.get_db")
    def test_health_check_success(self, mock_get_db):
        """Test successful health check"""
        # Mock database connection
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        health = health_check()

        assert health["status"] == "healthy"
        assert health["database"] == "connected"
        assert "timestamp" in health

    @patch("app.utils.get_db")
    def test_health_check_database_failure(self, mock_get_db):
        """Test health check with database failure"""
        mock_get_db.side_effect = Exception("Database connection failed")

        health = health_check()

        assert health["status"] == "unhealthy"
        assert health["database"] == "disconnected"


class TestSingleUserMode:
    """Test single user mode utilities"""

    @patch("app.utils.settings")
    def test_is_single_user_mode_true(self, mock_settings):
        """Test single user mode detection when enabled"""
        mock_settings.SINGLE_USER_MODE = True

        assert is_single_user_mode() is True

    @patch("app.utils.settings")
    def test_is_single_user_mode_false(self, mock_settings):
        """Test single user mode detection when disabled"""
        mock_settings.SINGLE_USER_MODE = False

        assert is_single_user_mode() is False

    @patch("app.utils.get_db")
    @patch("app.utils.settings")
    def test_get_single_user(self, mock_settings, mock_get_db):
        """Test getting single user"""
        mock_settings.SINGLE_USER_MODE = True

        # Mock database and user
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "single_user"
        mock_db.query.return_value.first.return_value = mock_user

        user = get_single_user()

        assert user.id == 1
        assert user.username == "single_user"

    @patch("app.utils.get_db")
    @patch("app.utils.settings")
    def test_get_single_user_not_found(self, mock_settings, mock_get_db):
        """Test getting single user when none exists"""
        mock_settings.SINGLE_USER_MODE = True

        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.query.return_value.first.return_value = None

        user = get_single_user()

        assert user is None


class TestDataImportExport:
    """Test data import/export utilities"""

    @patch("app.utils.get_db")
    def test_export_endpoint_data_success(self, mock_get_db):
        """Test successful data export"""
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock data entries
        mock_entry1 = MagicMock()
        mock_entry1.data = {"title": "Entry 1", "content": "Content 1"}
        mock_entry2 = MagicMock()
        mock_entry2.data = {"title": "Entry 2", "content": "Content 2"}

        mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_entry1,
            mock_entry2,
        ]

        result = export_endpoint_data("test_endpoint", user_id=1)

        assert len(result) == 2
        assert result[0]["title"] == "Entry 1"
        assert result[1]["title"] == "Entry 2"

    @patch("app.utils.get_db")
    def test_export_endpoint_data_no_data(self, mock_get_db):
        """Test data export when no data exists"""
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = export_endpoint_data("empty_endpoint", user_id=1)

        assert result == []

    @patch("app.utils.import_endpoint_data_to_database")
    def test_import_endpoint_data_success(self, mock_import):
        """Test successful data import"""
        mock_import.return_value = True

        data_to_import = [
            {"title": "Entry 1", "content": "Content 1"},
            {"title": "Entry 2", "content": "Content 2"},
        ]

        result = import_endpoint_data("test_endpoint", data_to_import, user_id=1)

        assert result["success"] is True
        assert result["imported_count"] == 2
        assert result["failed_count"] == 0

    @patch("app.utils.import_endpoint_data_to_database")
    def test_import_endpoint_data_partial_failure(self, mock_import):
        """Test data import with partial failures"""
        # First import succeeds, second fails
        mock_import.side_effect = [True, False]

        data_to_import = [
            {"title": "Entry 1", "content": "Content 1"},
            {"title": "Entry 2", "content": "Content 2"},
        ]

        result = import_endpoint_data("test_endpoint", data_to_import, user_id=1)

        assert result["success"] is False
        assert result["imported_count"] == 1
        assert result["failed_count"] == 1

    def test_import_endpoint_data_empty_data(self):
        """Test data import with empty data"""
        result = import_endpoint_data("test_endpoint", [], user_id=1)

        assert result["success"] is True
        assert result["imported_count"] == 0
        assert result["failed_count"] == 0


class TestUtilitySecurityValidation:
    """Test security validation in utility functions"""

    def test_sanitize_malicious_html(self):
        """Test sanitization of various HTML/XSS attacks"""
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "<iframe src=javascript:alert('xss')>",
            "<object data=javascript:alert('xss')>",
            "<embed src=javascript:alert('xss')>",
            "<link rel=stylesheet href=javascript:alert('xss')>",
            "<style>@import 'javascript:alert(\"xss\")';</style>",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "vbscript:msgbox('xss')",
        ]

        for malicious_input in malicious_inputs:
            result = sanitize_input(malicious_input)
            # Should not contain executable JavaScript
            assert "javascript:" not in result.lower()
            assert "<script" not in result.lower()
            assert "alert(" not in result.lower()

    def test_filename_path_traversal_protection(self):
        """Test filename sanitization against path traversal"""
        malicious_filenames = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM",
            "..%2f..%2f..%2fetc%2fpasswd",
            "..%5c..%5c..%5cwindows%5csystem32",
        ]

        for filename in malicious_filenames:
            result = sanitize_filename(filename)
            # Should not contain path traversal sequences
            assert "../" not in result
            assert "..\\" not in result
            assert not result.startswith("/")
            assert (
                ":" not in result or result.count(":") <= 1
            )  # Allow single colon for drive letters

    def test_url_validation_security(self):
        """Test URL validation against malicious URLs"""
        malicious_urls = [
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "file:///etc/passwd",
            "ftp://malicious.com/file",
            "gopher://malicious.com",
            "ldap://malicious.com",
            "jar:http://malicious.com!/",
            "vbscript:msgbox('xss')",
        ]

        for url in malicious_urls:
            assert validate_url(url) is False

    def test_json_schema_security(self):
        """Test JSON schema validation security"""
        malicious_json_strings = [
            '{"__proto__": {"polluted": true}}',  # Prototype pollution
            '{"constructor": {"prototype": {"polluted": true}}}',  # Constructor pollution
            '{"eval": "alert(\'xss\')"}',  # Code in JSON
            '{"script": "<script>alert(\'xss\')</script>"}',  # HTML in JSON
        ]

        for json_str in malicious_json_strings:
            # Should validate as JSON but content should be treated safely
            if validate_json_schema(json_str):
                parsed = json.loads(json_str)
                # Content should be treated as safe strings, not executable code
                assert isinstance(parsed, dict)

    def test_endpoint_name_security(self):
        """Test endpoint name validation security"""
        malicious_endpoints = [
            "../admin",
            "admin/users",
            "/etc/passwd",
            "endpoint<script>",
            "endpoint'; DROP TABLE users; --",
            "endpoint${eval(code)}",
            "endpoint`rm -rf /`",
        ]

        for endpoint in malicious_endpoints:
            assert validate_endpoint_name(endpoint) is False

    def test_sensitive_data_masking_thoroughness(self):
        """Test that all sensitive data patterns are properly masked"""
        sensitive_patterns = {
            "password": "secret123",
            "passwd": "secret123",
            "pwd": "secret123",
            "pass": "secret123",
            "secret": "secret123",
            "key": "secret123",
            "api_key": "sk-1234567890",
            "apikey": "sk-1234567890",
            "token": "bearer_token",
            "access_token": "oauth_token",
            "refresh_token": "refresh_token",
            "private_key": "-----BEGIN PRIVATE KEY-----",
            "auth": "auth_string",
            "authorization": "auth_string",
            "credential": "cred_string",
            "database_url": "postgresql://user:pass@host:5432/db",
        }

        result = mask_sensitive_data(sensitive_patterns)

        for key in sensitive_patterns:
            assert result[key] == "***", f"Failed to mask {key}"

    def test_large_input_handling(self):
        """Test handling of extremely large inputs"""
        # Large safe input
        large_safe = "a" * 100000
        result = sanitize_input(large_safe)
        assert len(result) <= len(large_safe) + 1000  # Allow for some encoding overhead

        # Large malicious input
        large_malicious = "<script>alert('xss')</script>" * 10000
        result = sanitize_input(large_malicious)
        assert "<script>" not in result
        assert "alert(" not in result

    def test_unicode_security_handling(self):
        """Test security handling of unicode characters"""
        unicode_attacks = [
            "＜script＞alert('xss')＜/script＞",  # Full-width characters
            "javåscript:alert('xss')",  # Unicode lookalikes
            "\u202e<script>alert('xss')</script>",  # Right-to-left override
            "\ufeff<script>alert('xss')</script>",  # Byte order mark
        ]

        for attack in unicode_attacks:
            result = sanitize_input(attack)
            # Should handle unicode attacks safely
            assert "alert(" not in result.lower()
            assert "<script" not in result.lower()

    def test_nested_structure_sanitization(self):
        """Test sanitization of deeply nested structures"""
        deeply_nested = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "malicious": "<script>alert('xss')</script>",
                            "safe": "normal_value",
                        }
                    }
                }
            }
        }

        result = sanitize_data_dict(deeply_nested)

        # Should sanitize even deeply nested malicious content
        malicious_value = result["level1"]["level2"]["level3"]["level4"]["malicious"]
        assert "&lt;script&gt;" in malicious_value
        assert "alert(" not in malicious_value

        # Safe content should remain unchanged
        safe_value = result["level1"]["level2"]["level3"]["level4"]["safe"]
        assert safe_value == "normal_value"
